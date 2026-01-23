"""
Vector Store Manager Module
Handles embeddings generation and vector store operations.
"""

from typing import List, Optional, Literal, Any
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
import os
import hashlib
import fasttext
import sys
from ..events.event_bus import EventBus, VectorStoreUpdateEvent
import config.settings as settings
from ..factories.embedding_factory import EmbeddingFactory


class VectorStoreManager:
    """
    Manages vector store creation, loading, and retrieval operations with dynamic embedding selection.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        embedding_type: Optional[str] = None
    ):
        """
        Initialize the vector store manager.
        """
        self.vector_store = None
        self.event_bus = event_bus
        self.embedding_type = embedding_type
        self.ft_model = None  # OPTIMIZATION: Lazy load FastText model
        self._ft_model_loaded = False
        self.current_embedding_model = None # Track which model is currently loaded

    def _load_fasttext_model(self):
        """Load the FastText language identification model (lazy loading)."""
        if self._ft_model_loaded:
            return self.ft_model
            
        self._ft_model_loaded = True
        model_path = settings.FASTTEXT_MODEL_PATH
        if not os.path.exists(model_path):
            print(f"⚠ FastText model not found at {model_path}. Language detection disabled.")
            self.ft_model = None
            return None
        
        # Suppress fasttext warning about load_model
        fasttext.FastText.eprint = lambda x: None
        try:
            self.ft_model = fasttext.load_model(str(model_path))
            return self.ft_model
        except Exception as e:
            print(f"❌ Error loading FastText model: {e}")
            self.ft_model = None
            return None

    def detect_language(self, text: str) -> str:
        """
        Detect language of the text using FastText.
        
        Args:
            text: Text sample to analyze
            
        Returns:
            Language code (e.g., 'en', 'es') or 'en' if detection fails
        """
        # Lazy load FastText model only when needed
        if not self._ft_model_loaded:
            self._load_fasttext_model()
        
        if not self.ft_model:
            return 'en'
            
        try:
            # Clean text specifically for fasttext
            clean_text = text.replace('\n', ' ')[:1000] # Analyze first 1000 chars
            pred = self.ft_model.predict(clean_text, k=1)
            language_code = pred[0][0].replace('__label__', '')
            confidence = pred[1][0]
            print(f"🔍 Language detected: {language_code} ({confidence:.1%})")
            return language_code
        except Exception as e:
            print(f"⚠ Language detection failed: {e}")
            return 'en'

    # _get_embeddings_for_language removed: Logic moved to EmbeddingFactory

    def get_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of a file.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_vector_store(self, documents: List[Document], cache_key: Optional[str] = None) -> FAISS:
        """
        Create a new vector store from documents with dynamic embedding selection.
        """
        # Detect language from a sample of documents
        sample_text = " ".join([d.page_content for d in documents[:5]])
        language = self.detect_language(sample_text)
        
        # Initialize appropriate embeddings
        # Initialize appropriate embeddings
        self.embeddings = EmbeddingFactory.get_embedding_model(
            embedding_type=self.embedding_type, 
            language_code=language
        )

        # Helper to get the model name being used
        current_model_name = "default"
        if hasattr(self.embeddings, 'model'):
             current_model_name = self.embeddings.model
        elif hasattr(self.embeddings, 'model_name'):
             current_model_name = self.embeddings.model_name
        
        # Sanitize model name for filesystem
        safe_model_name = current_model_name.replace("/", "_").replace(":", "_")

        # If cache_key provided, check if cached version exists
        if cache_key:
            # Append language AND model specific suffix to avoid mixing incompatible embeddings
            # New format: {hash}_{safe_model_name}_{language}
            cache_path = f"data/vector_stores/{cache_key}_{safe_model_name}_{language}"
            
            if os.path.exists(cache_path):
                print(f"\n📦 Loading cached vector store: {cache_path}...")
                self.current_embedding_model = current_model_name # Track it
                return self.load_vector_store(cache_path)
            
            # Legacy fallback (language only)
            legacy_path = f"data/vector_stores/{cache_key}_{language}"
            if os.path.exists(legacy_path):
                 print(f"\n⚠ Found legacy cache at {legacy_path}, but ignoring to ensure correct embedding model ({current_model_name}).")

        print(f"\n🔄 Creating vector store from {len(documents)} documents using {current_model_name}...")
        self.vector_store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        print("✓ Vector store created successfully")

        # Save to cache if cache_key provided
        if cache_key:
            cache_path = f"data/vector_stores/{cache_key}_{safe_model_name}_{language}"
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            self.save_vector_store(cache_path)
            print(f"✓ Vector store cached at: {cache_path}")

        if self.event_bus:
            self.event_bus.publish(VectorStoreUpdateEvent(
                operation="create",
                document_count=len(documents)
            ))

        return self.vector_store

    def save_vector_store(self, path: str = "faiss_index"):
        """Save the vector store to disk."""
        if self.vector_store is None:
            raise ValueError("No vector store to save. Create one first.")

        self.vector_store.save_local(path)
        print(f"✓ Vector store saved to: {path}")

    def load_vector_store(self, path: str = "faiss_index") -> FAISS:
        """
        Load a vector store from disk.
        WARNING: This assumes the currently initialized embeddings match the stored index.
        For dynamic loading, create_vector_store handles the flow better.
        """
        if not os.path.exists(path):
            # Try to find a directory with language suffix
            parent_dir = os.path.dirname(path)
            base_name = os.path.basename(path)
            
            if os.path.exists(parent_dir):
                candidates = [
                    d for d in os.listdir(parent_dir) 
                    if d.startswith(base_name + "_") 
                    and not d.endswith("_graph.done")
                    and os.path.isdir(os.path.join(parent_dir, d))
                ]
                if candidates:
                    # Use the first match (usually just one language per file)
                    new_path = os.path.join(parent_dir, candidates[0])
                    print(f"ℹ️ Found suffixed vector store at: {new_path}")
                    path = new_path
                    
                    # Infer language from suffix to select correct embedding model
                    suffix = candidates[0].split('_')[-1]
                    if suffix in ['en', 'es', 'fr', 'de']: # List of likely codes
                        print(f"ℹ️ Inferred language '{suffix}' from directory name.")
                        self.embeddings = EmbeddingFactory.get_embedding_model(self.embedding_type, suffix)
                else:
                    raise FileNotFoundError(f"Vector store not found at: {path}")
            else:
                raise FileNotFoundError(f"Vector store not found at: {path}")

        # If embeddings not set (e.g. manual load), default to English or Multilingual?
        # Ideally, we should detect or store metadata. For now, if not set, default to Multilingual as safest.
        if not hasattr(self, 'embeddings') or self.embeddings is None:
             print("⚠ Embeddings not initialized, defaulting to Multilingual for load.")
             self.embeddings = EmbeddingFactory.get_embedding_model(self.embedding_type, "es") # Fallback

        print(f"📂 Loading vector store from: {path}")
        self.vector_store = FAISS.load_local(
            path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        print("✓ Vector store loaded successfully")

        if self.event_bus and self.vector_store:
            count = 0
            if hasattr(self.vector_store, 'index'):
                count = self.vector_store.index.ntotal
                
            self.event_bus.publish(VectorStoreUpdateEvent(
                operation="load",
                document_count=count
            ))

        return self.vector_store

    def add_documents(self, documents: List[Document]):
        """
        Add new documents to an existing vector store.
        If store doesn't exist, create it.
        """
        if self.vector_store is None:
            print("ℹ️ No vector store exists, creating new one...")
            self.create_vector_store(documents, cache_key="faiss_index")
            return

        print(f"\n➕ Adding {len(documents)} documents to vector store...")
        self.vector_store.add_documents(documents)
        
        # Auto-save after addition
        self.save_vector_store("data/vector_stores/faiss_index") # Or track current path
        print("✓ Documents added successfully")
        
        if self.event_bus:
            self.event_bus.publish(VectorStoreUpdateEvent(
                operation="add",
                document_count=len(documents)
            ))

    def similarity_search(
        self,
        query: str,
        k: int = 4
    ) -> List[Document]:
        """
        Search for similar documents.

        Args:
            query: Query text
            k: Number of documents to return

        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            raise ValueError("No vector store exists. Create or load one first.")

        results = self.vector_store.similarity_search(query, k=k)
        return results

    def get_retriever(self, k: int = 4) -> VectorStoreRetriever:
        """
        Get a retriever for the vector store.
        """
        # Lazy load if missing
        if self.vector_store is None:
            print("Using lazy load in get_retriever...")
            try:
                # Try default path
                default_path = "data/vector_stores/faiss_index"
                self.load_vector_store(default_path)
            except Exception as e:
                print(f"Lazy load failed: {e}")

        if self.vector_store is None:
            raise ValueError("No vector store exists. Create or load one first.")

        return self.vector_store.as_retriever(
            search_kwargs={"k": k}
        )


if __name__ == "__main__":
    # Example usage
    print("Vector Store Manager initialized successfully!")
    print("\nSupported embedding types:")
    print("  - huggingface: all-MiniLM-L6-v2 (default, free)")
