from typing import Optional, List
from langchain_core.document_loaders import BaseLoader
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
import os
from .logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("loader_factory")

class LoaderFactory:
    """
    Factory for creating document loaders based on file type or source.
    Encapsulates logic for selecting the right loader (PDF, Text, Web, etc.).
    """

    @staticmethod
    def get_loader(resource_path: str, doc_type: Optional[str] = None) -> BaseLoader:
        """
        Get the appropriate loader for the given resource path (file path or URL).
        
        Args:
            resource_path: File path or URL.
            doc_type: Explicit type ('pdf', 'txt', 'url'). If None, type is inferred.
            
        Returns:
            Instantiated Loader object (compatible with LangChain BaseLoader).
        """
        
        # 1. Infer type if not provided
        if doc_type is None:
            doc_type = LoaderFactory._infer_type(resource_path)
            
        logger.info(f"Selecting loader for type: {doc_type} (Source: {resource_path})")

        # 2. Return appropriate loader
        if doc_type == 'pdf':
            if not os.path.exists(resource_path):
                raise FileNotFoundError(f"File not found: {resource_path}")
            return PyPDFLoader(resource_path)
            
        elif doc_type == 'txt':
            if not os.path.exists(resource_path):
                raise FileNotFoundError(f"File not found: {resource_path}")
            return TextLoader(resource_path)
            
        elif doc_type == 'url':
            return WebBaseLoader(resource_path)
            
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

    @staticmethod
    def _infer_type(path: str) -> str:
        """Infer document type from path/URL."""
        if path.startswith('http://') or path.startswith('https://'):
            return 'url'
        elif path.lower().endswith('.pdf'):
            return 'pdf'
        elif path.lower().endswith('.txt') or path.lower().endswith('.md'):
            return 'txt'
        else:
            raise ValueError(f"Cannot auto-detect document type for: {path}")
