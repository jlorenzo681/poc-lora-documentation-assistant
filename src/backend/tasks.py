from .celery_config import celery_app
from src.chatbot.core.processing.document_processor import DocumentProcessor
from src.chatbot.core.storage.vector_store_manager import VectorStoreManager

import os
import logging
import datetime
from pathlib import Path
import config.settings as settings

from src.chatbot.core.factories.logger_factory import LoggerFactory
from src.chatbot.connectors.connector_manager import ConnectorManager
from src.chatbot.sync.file_change_detector import FileChangeDetector
import shutil

@celery_app.task(bind=True)
def process_document_task(self, file_path: str, api_key: str, embedding_type: str, llm_model: str = None, chunking_strategy: str = "recursive"):
    """
    Celery task to process a document.
    """
    logger = None
    file_handler = None
    
    try:
        # 0. Setup Logger
        logger, file_handler = LoggerFactory.setup_task_logger(
            task_id=self.request.id, 
            file_path=file_path, 
            base_name="document_processor"
        )
        logger.info(f"Task Started: {self.request.id}")
        logger.info(f"Processing File: {file_path}")
        logger.info(f"Strategy: {chunking_strategy}")
        
        self.update_state(state='PROGRESS', meta={'status': 'Initializing...'})
        
        # 1. Initialize Managers
        # Note: We pass None for event_bus to avoid overhead
        vector_manager = VectorStoreManager(embedding_type=embedding_type)


        # 2. Check Cache
        self.update_state(state='PROGRESS', meta={'status': 'Checking cache...'})
        logger.info("Checking vector store cache...")
        file_hash = vector_manager.get_file_hash(file_path)
        logger.info(f"File Hash: {file_hash}")
        
        # 3. Process
        status_msg = 'Chunking document...'
        if chunking_strategy == 'agentic':
            status_msg = 'Agentic Chunking (using LLM)...'
            
        self.update_state(state='PROGRESS', meta={'status': status_msg})
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        
        if chunking_strategy == "agentic":
            # We need an LLM for agentic chunking
            from src.chatbot.core.factories.llm_factory import LLMFactory
            
            logger.info("Initializing LLM for Agentic Chunking...")
            llm = LLMFactory.create_llm(
                provider="mlx", 
                temperature=0.0
            )
            processor.set_chunking_strategy("agentic", llm=llm)
        
        logger.info("Starting document processing...")
        chunks = processor.process_document(file_path)
        logger.info(f"Document processed. Generated {len(chunks)} chunks.")
        
        # 4. Create Vector Store
        self.update_state(state='PROGRESS', meta={'status': f'Embedding {len(chunks)} chunks...'})
        logger.info(f"Creating vector store for {len(chunks)} chunks...")
        
        vector_manager.create_vector_store(chunks, cache_key=file_hash)
        logger.info(f"Vector store created/updated successfully.")
        
        
        logger.info("Task Completed Successfully.")
        
        return {
            "status": "completed", 
            "chunks": len(chunks), 
            "file_hash": file_hash,
            "message": "Processing complete",
            "strategy": chunking_strategy,
            "log_file": file_handler.baseFilename if file_handler else "unknown"
        }
        
    except Exception as e:
        if logger: logger.error(f"Task Failed: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        # Clean up handlers to prevent logging leak across tasks
        if logger and file_handler:
            logger.removeHandler(file_handler)
            file_handler.close()

@celery_app.task
def sync_all_connectors_task():
    """
    Periodic task to sync all enabled connectors.
    """
    logger = logging.getLogger("sync_scheduler")
    logger.info("Starting sync for all connectors...")
    
    # 1. Initialize Manager (DB logic needed effectively)
    # For now, we assume Manager can load from DB. 
    # Since Manager._load_config_from_db is TODO, we probably need to implement it 
    # or expose a method to get enabled connectors.
    
    # Let's instantiate manager and get a list of connector IDs to sync.
    # This requires DB access. 
    # We will query the DB directly here or add method to manager.
    # Let's add a helper here for MVP.
    
    manager = ConnectorManager()
    change_detector = FileChangeDetector()
    
    # Mock list of connectors for now or query DB if we can
    # For MVP, we might need to implement `get_enabled_connectors` in Manager.
    # Let's skip the DB query logic for a moment and assume we have a way.
    # But wait, FileChangeDetector has DB logic. Let's use similar logic.
    
    conn = change_detector._get_connection()
    connector_configs = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, provider, oauth_credentials, folders_to_sync, file_filters FROM connectors WHERE enabled = TRUE")
            rows = cur.fetchall()
            for row in rows:
                connector_configs.append({
                    "id": row[0],
                    "name": row[1],
                    "provider": row[2],
                    "oauth_credentials": row[3],
                    "folders_to_sync": row[4], # Need to parse JSON? Postgres text.
                    "file_filters": row[5]
                })
    except Exception as e:
        logger.error(f"Error fetching connectors: {e}")
        return
    finally:
        conn.close()

    for config in connector_configs:
        try:
            connector_id = config["id"]
            logger.info(f"Syncing connector: {connector_id}")
            
            # Instantiate via Manager (it handles factory logic)
            connector = manager._instantiate_connector(config)
            if not connector:
                continue
                
            # Iterate folders
            # Note: config["folders_to_sync"] might need json.loads if stored as text
            import json
            folders = []
            if isinstance(config["folders_to_sync"], str):
                folders = json.loads(config["folders_to_sync"])
            else:
                folders = config["folders_to_sync"]
                
            for folder_id in folders:
                files = connector.list_files(folder_id)
                
                for file_meta in files:
                    # Check if processing needed
                    if change_detector.should_process_file(connector_id, file_meta):
                        logger.info(f"Queueing download for file: {file_meta.get('name')}")
                        
                        # Queue download task
                        download_and_process_task.delay(
                            connector_id, 
                            config, # We pass full config to avoid reloading in worker? Or just ID? Better ID.
                            file_meta
                        )
                        
                        # Optimistically mark as processed? No, wait for success.
                        
        except Exception as e:
            logger.error(f"Error syncing connector {config.get('id')}: {e}")

@celery_app.task(bind=True)
def download_and_process_task(self, connector_id: str, connector_config: dict, file_metadata: dict):
    """
    Task to download a file and trigger processing.
    """
    logger = logging.getLogger("download_worker")
    file_id = file_metadata.get("id")
    file_name = file_metadata.get("name")
    
    try:
        # Re-instantiate connector
        # Note: In a real app we might load config from DB by ID again for freshness
        from src.chatbot.connectors.connector_manager import ConnectorManager
        manager = ConnectorManager()
        connector = manager._instantiate_connector(connector_config)
        
        # Temp path
        temp_dir = os.path.join(settings.DATA_DIR, "temp_downloads")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{connector_id}_{file_name}")
        
        # Download
        logger.info(f"Downloading {file_name}...")
        if connector.download_file(file_id, temp_path):
            
            # Process using existing task logic (invoke locally or subtask)
            # We can reuse the logic from process_document_task directly or call function
            # Let's call the `DocumentProcessor` directly here to simplify or call the task?
            # Calling task adds overhead. Using processor directly.
            
            from src.chatbot.core.processing.document_processor import DocumentProcessor
            from src.chatbot.core.storage.vector_store_manager import VectorStoreManager
            
            logger.info(f"Processing {file_name}...")
            # We might want to pass 'embedding_type' etc. assuming default for now
            processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
            
            # Note: Process document creates a NEW vector store if not default? 
            # We need to ensure we use the centralized store managed by VectorStoreManager
            # But DocumentProcessor internals:
            #   self.vector_store_manager = vector_store_manager
            #   ...
            #   if self.vector_store_manager: ... add_documents
            
            vsm = VectorStoreManager(embedding_type=settings.DEFAULT_EMBEDDING_TYPE)
            # Ensure it links to default store path
            default_path = os.path.join(settings.VECTOR_STORE_PATH, "faiss_index")
            try:
                vsm.load_vector_store(default_path)
            except:
                pass # Will create new
                
            processor.vector_store_manager = vsm
            
            # Process
            processor.process_document(temp_path)
            
            # Save VSM?
            # VectorStoreManager.add_documents usually saves/persists if configured?
            # Looking at VSM code (not shown fully but assumed standard):
            # It should ideally save to disk.
            
            # Update State
            change_detector = FileChangeDetector()
            change_detector.update_file_state(connector_id, file_metadata, processed=True)
            
            logger.info(f"Successfully processed {file_name}")
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        else:
            logger.error(f"Failed to download {file_id}")
            
    except Exception as e:
        logger.error(f"Error in download_and_process_task: {e}")
        # Retry?
        raise e
