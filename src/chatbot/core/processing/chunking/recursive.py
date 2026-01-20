"""
Recursive Character Chunking Strategy
Wraps the standard LangChain RecursiveCharacterTextSplitter.
"""

from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .base import BaseChunker

class RecursiveChunker(BaseChunker):
    """
    Standard recursive character splitting.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, add_start_index: bool = True):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=add_start_index,
            separators=["\n\n", "\n", " ", ""]
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.splitter.split_documents(documents)
