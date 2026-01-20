from .celery_config import celery_app
from src.chatbot.core.processing.document_processor import DocumentProcessor
from src.chatbot.core.storage.vector_store_manager import VectorStoreManager

import os
import logging
import datetime
from pathlib import Path
import config.settings as settings

from src.chatbot.core.factories.logger_factory import LoggerFactory

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
