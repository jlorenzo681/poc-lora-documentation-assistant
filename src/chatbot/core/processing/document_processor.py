"""
Document Processor Module
Handles loading and chunking of various document types for RAG system.
"""

from typing import List, Optional, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
import time
import logging
from ..events.event_bus import EventBus, ProcessingStartEvent, ProcessingCompleteEvent
from ..factories.logger_factory import LoggerFactory
from ..factories.loader_factory import LoaderFactory

logger = LoggerFactory.get_logger("document_processor")


class DocumentProcessor:
    """
    Processes documents by loading and splitting them into manageable chunks.
    """

    def __init__(
        self,
        vector_store_manager = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        add_start_index: bool = True,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize the document processor.

        Args:
            vector_store_manager: Manager to handle vector embedding storage
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
            add_start_index: Whether to track original position in document
        """
        self.vector_store_manager = vector_store_manager
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.event_bus = event_bus
        
        # Initialize Chunking Strategy
        # Note: Default to Recursive if not specified or for legacy support
        # To enable Agentic, one must pass chunking_strategy='agentic'
        # But we need access to LLM for Agentic.
        
        self.strategy_type = "recursive" 
        # For now, we default to internal recursive initialization, 
        # but we should refactor to use the classes we just made.
        
        from .chunking.recursive import RecursiveChunker
        self.chunker = RecursiveChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=add_start_index)
    
    def set_chunking_strategy(self, strategy: str, llm: Optional[Any] = None, **kwargs):
        """
        Switch the chunking strategy.
        Args:
            strategy: 'recursive' or 'agentic'
            llm: Required for agentic
            **kwargs: Extra args for the chunker (e.g. prompt_template)
        """
        self.strategy_type = strategy
        if strategy == "agentic":
            if not llm:
                raise ValueError("LLM instance required for Agentic Chunking")
            from .chunking.agentic import AgenticChunker
            
            # Pass kwargs like prompt_template to constructor
            self.chunker = AgenticChunker(
                llm=llm, 
                initial_chunk_size=200, 
                max_chunk_size=self.chunk_size * 2,
                **kwargs
            )
            print("✨ Switched to Agentic Chunking Strategy")
        else:
            from .chunking.recursive import RecursiveChunker
            self.chunker = RecursiveChunker(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
            print("reverted to Recursive Chunking Strategy")

    # ... (load_pdf, load_text, load_web, load_document, split_documents methods remain same) ...

    def load_document(self, file_path: str, doc_type: Optional[str] = None) -> List[Document]:
        """Load a document based on its type using LoaderFactory."""
        try:
            loader = LoaderFactory.get_loader(file_path, doc_type)
            documents = loader.load()
            logger.info(f"✓ Loaded {len(documents)} documents/pages from {file_path}")
            return documents
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            raise

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks."""
        chunks = self.chunker.split_documents(documents)
        logger.info(f"✓ Created {len(chunks)} chunks from {len(documents)} documents (Strategy: {self.strategy_type})")
        return chunks

    def process_document(
        self,
        file_path: str,
        doc_type: Optional[str] = None
    ) -> List[Document]:
        """
        Complete pipeline: load, split, and INDEX a document.
        """
        logger.info(f"\n📄 Processing document: {file_path}")
        
        start_time = time.time()
        
        if doc_type is None:
            if file_path.startswith('http://') or file_path.startswith('https://'):
                dt = 'url'
            elif file_path.endswith('.pdf'):
                dt = 'pdf'
            elif file_path.endswith('.txt') or file_path.endswith('.md'):
                dt = 'txt'
            else:
                dt = 'unknown'
        else:
            dt = doc_type

        # Emit start event
        if self.event_bus:
            self.event_bus.publish(ProcessingStartEvent(
                file_path=str(file_path),
                doc_type=dt
            ))

        documents = self.load_document(file_path, doc_type)
        chunks = self.split_documents(documents)
        
        # --- NEW: Add to Vector Store ---
        if self.vector_store_manager:
            try:
                self.vector_store_manager.add_documents(chunks)
                logger.info(f"✓ Added {len(chunks)} chunks to Vector Store")
            except Exception as e:
                logger.error(f"Error adding to vector store: {e}")
                # Don't fail the whole process if vector store fails? Or should we?
                # Probably should warn but return chunks.
        else:
            logger.warning("⚠ No VectorStoreManager provided. Chunks NOT saved to DB.")
        
        # Emit complete event
        if self.event_bus:
            self.event_bus.publish(ProcessingCompleteEvent(
                file_path=str(file_path),
                chunk_count=len(chunks),
                duration_seconds=time.time() - start_time
            ))
            
        return chunks


if __name__ == "__main__":
    # Example usage
    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)

    # Test with a sample document
    print("Document Processor initialized successfully!")
    print(f"Chunk size: {processor.chunk_size}")
    print(f"Chunk overlap: {processor.chunk_overlap}")
