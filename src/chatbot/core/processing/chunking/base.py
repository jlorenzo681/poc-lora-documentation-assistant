"""
Base Chunking Strategy
Defines the interface for all chunking strategies.
"""

from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document

class BaseChunker(ABC):
    """
    Abstract base class for document chunking strategies.
    """

    @abstractmethod
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of documents into chunks.
        """
        pass
