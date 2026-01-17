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
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        add_start_index: bool = True,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize the document processor.

        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
            add_start_index: Whether to track original position in document
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=add_start_index,
            separators=["\n\n", "\n", " ", ""]
        )
        self.event_bus = event_bus

    def load_pdf(self, file_path: str) -> List[Document]:
        """
        Load a PDF document.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of Document objects
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print(f"✓ Loaded {len(documents)} pages from PDF")
        return documents

    def load_text(self, file_path: str) -> List[Document]:
        """
        Load a text document.

        Args:
            file_path: Path to the text file

        Returns:
            List of Document objects
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        loader = TextLoader(file_path)
        documents = loader.load()
        print(f"✓ Loaded text file: {file_path}")
        return documents

    def load_web(self, url: str) -> List[Document]:
        """
        Load content from a web URL.

        Args:
            url: Web URL to load

        Returns:
            List of Document objects
        """
        loader = WebBaseLoader(url)
        documents = loader.load()
        print(f"✓ Loaded content from URL: {url}")
        return documents

    def load_document(self, file_path: str, doc_type: Optional[str] = None) -> List[Document]:
        """
        Load a document based on its type.

        Args:
            file_path: Path to the document or URL
            doc_type: Type of document ('pdf', 'txt', 'url'). Auto-detected if None.

        Returns:
            List of Document objects
        """
        if doc_type is None:
            # Auto-detect document type
            if file_path.startswith('http://') or file_path.startswith('https://'):
                doc_type = 'url'
            elif file_path.endswith('.pdf'):
                doc_type = 'pdf'
            elif file_path.endswith('.txt') or file_path.endswith('.md'):
                doc_type = 'txt'
            else:
                raise ValueError(f"Cannot auto-detect document type for: {file_path}")

        # Load based on type
        if doc_type == 'pdf':
            return self.load_pdf(file_path)
        elif doc_type == 'txt':
            return self.load_text(file_path)
        elif doc_type == 'url':
            return self.load_web(file_path)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks.

        Args:
            documents: List of Document objects to split

        Returns:
            List of chunked Document objects
        """
        chunks = self.text_splitter.split_documents(documents)
        print(f"✓ Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks

    def process_document(
        self,
        file_path: str,
        doc_type: Optional[str] = None
    ) -> List[Document]:
        """
        Complete pipeline: load and split a document.

        Args:
            file_path: Path to the document or URL
            doc_type: Type of document ('pdf', 'txt', 'url')

        Returns:
            List of chunked Document objects
        """
        print(f"\n📄 Processing document: {file_path}")
        
        start_time = time.time()
        
        if doc_type is None:
            # Simple auto-detection for event info (full detection logic is inside load_document)
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
