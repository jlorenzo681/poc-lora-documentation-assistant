"""
Document Processor Module
Handles loading and chunking of various document types for RAG system.
"""

from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
import time
from .event_bus import EventBus, ProcessingStartEvent, ProcessingCompleteEvent


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
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=add_start_index,
            separators=["\n\n", "\n", " ", ""]
        )
        self.event_bus = event_bus

    # ... (load_pdf, load_text, load_web, load_document, split_documents methods remain same) ...

    def load_pdf(self, file_path: str) -> List[Document]:
        """Load a PDF document."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            print(f"✓ Loaded {len(documents)} pages from PDF")
            return documents
        except Exception as e:
            print(f"Error loading PDF {file_path}: {e}")
            raise

    def load_text(self, file_path: str) -> List[Document]:
        """Load a text document."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            loader = TextLoader(file_path)
            documents = loader.load()
            print(f"✓ Loaded text file: {file_path}")
            return documents
        except Exception as e:
            print(f"Error loading text {file_path}: {e}")
            raise

    def load_web(self, url: str) -> List[Document]:
        """Load content from a web URL."""
        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            print(f"✓ Loaded content from URL: {url}")
            return documents
        except Exception as e:
            print(f"Error loading URL {url}: {e}")
            raise

    def load_document(self, file_path: str, doc_type: Optional[str] = None) -> List[Document]:
        """Load a document based on its type."""
        if doc_type is None:
            if file_path.startswith('http://') or file_path.startswith('https://'):
                doc_type = 'url'
            elif file_path.endswith('.pdf'):
                doc_type = 'pdf'
            elif file_path.endswith('.txt') or file_path.endswith('.md'):
                doc_type = 'txt'
            else:
                raise ValueError(f"Cannot auto-detect document type for: {file_path}")

        if doc_type == 'pdf':
            return self.load_pdf(file_path)
        elif doc_type == 'txt':
            return self.load_text(file_path)
        elif doc_type == 'url':
            return self.load_web(file_path)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks."""
        chunks = self.text_splitter.split_documents(documents)
        print(f"✓ Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks

    def process_document(
        self,
        file_path: str,
        doc_type: Optional[str] = None
    ) -> List[Document]:
        """
        Complete pipeline: load, split, and INDEX a document.
        """
        print(f"\n📄 Processing document: {file_path}")
        
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
                print(f"✓ Added {len(chunks)} chunks to Vector Store")
            except Exception as e:
                print(f"Error adding to vector store: {e}")
                # Don't fail the whole process if vector store fails? Or should we?
                # Probably should warn but return chunks.
        else:
            print("⚠ No VectorStoreManager provided. Chunks NOT saved to DB.")
        
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
