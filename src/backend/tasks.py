from .celery_config import celery_app
from src.chatbot.core.document_processor import DocumentProcessor
from src.chatbot.core.vector_store_manager import VectorStoreManager
from src.chatbot.core.graph_store_manager import GraphStoreManager
import os
import config.settings as settings

@celery_app.task(bind=True)
def process_document_task(self, file_path: str, api_key: str, embedding_type: str, llm_model: str = None):
    """
    Celery task to process a document.
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Initializing...'})
        
        # 1. Initialize Managers
        # Note: We pass None for event_bus to avoid overhead
        vector_manager = VectorStoreManager(embedding_type=embedding_type)
        graph_manager = GraphStoreManager(model_name=llm_model)

        # 2. Check Cache
        self.update_state(state='PROGRESS', meta={'status': 'Checking cache...'})
        file_hash = vector_manager.get_file_hash(file_path)
        cache_path = f"data/vector_stores/{file_hash}" # Note: VSM now appends language suffix, but check depends on VSM implementation
        
        # NOTE: With dynamic embeddings, the cache path logic in VSM is internal. 
        # We should probably trust VSM or just proceed to process.
        # For graph, we don't have a simple file-based cache check yet (Neo4j deduplication).
        # To simplify, we proceed if we want to ensure graph is updated, or check vector store existence as proxy.
        
        # 3. Process
        self.update_state(state='PROGRESS', meta={'status': 'Chunking document...'})
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        chunks = processor.process_document(file_path)
        
        # 4. Create Vector Store
        self.update_state(state='PROGRESS', meta={'status': f'Embedding {len(chunks)} chunks...'})
        # This will create/cache the vector store (VSM handles language detection internally)
        vector_manager.create_vector_store(chunks, cache_key=file_hash)
        
        # 5. Graph Extraction (if enabled)
        # 5. Graph Extraction (if enabled)
        if getattr(settings, "ENABLE_GRAPHRAG", False):
            # Check cache using Manager (Clean Architecture)
            if graph_manager.check_cache(file_hash):
                self.update_state(state='PROGRESS', meta={'status': 'Graph data already cached. Skipping extraction.'})
                print("✓ Graph data already cached. Skipping extraction.")
            else:
                self.update_state(state='PROGRESS', meta={'status': f'Extracting Graph data (this may take a while)...'})
                graph_manager.add_documents_to_graph(chunks)
                # Mark completion
                graph_manager.mark_as_completed(file_hash)
        
        return {
            "status": "completed", 
            "chunks": len(chunks), 
            "file_hash": file_hash,
            "message": "Processing complete"
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
