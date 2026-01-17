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
from .event_bus import EventBus, VectorStoreUpdateEvent
import config.settings as settings


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
        self.ft_model = self._load_fasttext_model()
        self.current_embedding_model = None # Track which model is currently loaded

    def _load_fasttext_model(self):
        """Load the FastText language identification model."""
        model_path = settings.FASTTEXT_MODEL_PATH
        if not os.path.exists(model_path):
            print(f"⚠ FastText model not found at {model_path}. Language detection disabled.")
            return None
        
        # Suppress fasttext warning about load_model
        fasttext.FastText.eprint = lambda x: None
        try:
            return fasttext.load_model(str(model_path))
        except Exception as e:
            print(f"❌ Error loading FastText model: {e}")
            return None

    def detect_language(self, text: str) -> str:
        """
        Detect language of the text using FastText.
        
        Args:
            text: Text sample to analyze
            
        Returns:
            Language code (e.g., 'en', 'es') or 'en' if detection fails
        """
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

    def _get_embeddings_for_language(self, language_code: str) -> Embeddings:
        """
        Get the appropriate embedding model for the detected language.
        
        Args:
            language_code: Detected language code
            
        Returns:
            Embeddings instance
        """
        if self.embedding_type:
            embedding_type = self.embedding_type
        else:
            embedding_type = getattr(settings, "DEFAULT_EMBEDDING_TYPE", "lmstudio")

        if embedding_type == "huggingface":
            # Use local HuggingFace embeddings (sentence-transformers)
            # Default to a good multilingual model if language is not English, or standard one for English
            # But specific models in settings might be Ollama-specific names. 
            # We'll use a standard variable or hardcoded defaults for HF to be safe/simple for now.
            if language_code == 'en':
                model_name = "sentence-transformers/all-MiniLM-L6-v2"
            else:
                model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            
            print(f"🔧 Selecting HuggingFace embedding model: {model_name}")
            return HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'}, # Use 'mps' if sure about Mac, but 'cpu' is safest fallback
                encode_kwargs={'normalize_embeddings': True}
            )

        elif embedding_type in ["lmstudio", "mlx"]:
             # Use LM Studio's embedding endpoint (OpenAI compatible)
             # MLX usually provides an OpenAI compatible endpoint as well
             from langchain_openai import OpenAIEmbeddings
             base_url = getattr(settings, "LLM_BASE_URL", "http://host.docker.internal:1234/v1")
             if language_code == 'en':
                 model_name = settings.EMBEDDING_MODEL_EN
             else:
                 model_name = settings.EMBEDDING_MODEL_MULTILINGUAL

             print(f"🔧 Selecting {embedding_type.upper()} embedding endpoint: {base_url} with model {model_name}")
             
             return OpenAIEmbeddings(
                 base_url=base_url,
                 api_key="lm-studio",
                 model=model_name, # Identifier often ignored by LM Studio, but good practice
                 check_embedding_ctx_length=False 
             )
        
        else:
            # Default to Ollama
            if language_code == 'en':
                model_name = settings.EMBEDDING_MODEL_EN
                print(f"🔧 Selecting English embedding model: {model_name}")
            else:
                model_name = settings.EMBEDDING_MODEL_MULTILINGUAL
                print(f"🔧 Selecting Multilingual embedding model ({language_code}): {model_name}")

            return OllamaEmbeddings(
                model=model_name,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
            )

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
        self.embeddings = self._get_embeddings_for_language(language)

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
                        self.embeddings = self._get_embeddings_for_language(suffix)
                else:
                    raise FileNotFoundError(f"Vector store not found at: {path}")
            else:
                raise FileNotFoundError(f"Vector store not found at: {path}")

        # If embeddings not set (e.g. manual load), default to English or Multilingual?
        # Ideally, we should detect or store metadata. For now, if not set, default to Multilingual as safest.
        if not hasattr(self, 'embeddings') or self.embeddings is None:
             print("⚠ Embeddings not initialized, defaulting to Multilingual for load.")
             self.embeddings = self._get_embeddings_for_language("es") # Fallback

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

        Args:
            documents: List of Document objects to add
        """
        if self.vector_store is None:
            raise ValueError("No vector store exists. Create one first.")

        print(f"\n➕ Adding {len(documents)} documents to vector store...")
        self.vector_store.add_documents(documents)
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

        Args:
            k: Number of documents to retrieve

        Returns:
            Retriever instance
        """
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
