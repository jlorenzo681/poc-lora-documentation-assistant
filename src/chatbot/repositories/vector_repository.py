
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from langchain_core.documents import Document

class VectorRepository(ABC):
    """
    Abstract base class for vector storage operations.
    """
    
    @abstractmethod
    def save_vector_store(self, path: str) -> None:
        """Save the vector store to disk."""
        pass
        
    @abstractmethod
    def load_vector_store(self, path: str) -> None:
        """Load the vector store from disk."""
        pass
        
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        pass
        
    @abstractmethod
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search for similar documents."""
        pass
        
    @abstractmethod
    def get_retriever(self, k: int = 4) -> Any:
        """Get a retriever interface for the store."""
        pass
