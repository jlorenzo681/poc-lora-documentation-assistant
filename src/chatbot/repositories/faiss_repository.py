
import os
from typing import List, Optional, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from .vector_repository import VectorRepository

class FAISSRepository(VectorRepository):
    """
    FAISS implementation of the VectorRepository.
    """
    
    def __init__(self, embeddings: Embeddings):
        self.embeddings = embeddings
        self.vector_store: Optional[FAISS] = None
        
    def create_from_documents(self, documents: List[Document]) -> None:
        """Create a new vector store from documents."""
        self.vector_store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        
    def save_vector_store(self, path: str) -> None:
        """Save the vector store to disk."""
        if self.vector_store is None:
            raise ValueError("No vector store to save.")
        self.vector_store.save_local(path)
        
    def load_vector_store(self, path: str) -> None:
        """Load the vector store from disk."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Vector store not found at {path}")
            
        self.vector_store = FAISS.load_local(
            path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        if self.vector_store is None:
            # Create new if doesn't exist
            self.create_from_documents(documents)
        else:
            self.vector_store.add_documents(documents)
            
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search for similar documents."""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized.")
        return self.vector_store.similarity_search(query, k=k)
        
    def get_retriever(self, k: int = 4) -> Any:
        """Get a retriever interface for the store."""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized.")
        return self.vector_store.as_retriever(search_kwargs={"k": k})
