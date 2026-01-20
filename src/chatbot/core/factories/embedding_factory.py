import os
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
import config.settings as settings
from .logger_factory import LoggerFactory

logger = LoggerFactory.get_logger("embedding_factory")

class EmbeddingFactory:
    """
    Factory for creating embedding models based on configuration and language.
    Encapsulates provider-specific logic (HuggingFace, Ollama, LM Studio/MLX).
    """

    @staticmethod
    def get_embedding_model(embedding_type: Optional[str], language_code: str = 'en') -> Embeddings:
        """
        Get the appropriate embedding model for the specified type and language.
        
        Args:
            embedding_type: Type of embedding ('huggingface', 'lmstudio', 'mlx', or 'ollama')
                           If None, uses DEFAULT_EMBEDDING_TYPE from settings.
            language_code: Detected language code (e.g., 'en', 'es').
            
        Returns:
            Configured Embeddings instance.
        """
        if embedding_type:
            etype = embedding_type
        else:
            etype = getattr(settings, "DEFAULT_EMBEDDING_TYPE", "lmstudio")

        logger.info(f"Requested embedding type: {etype} for language: {language_code}")

        if etype == "huggingface":
            return EmbeddingFactory._create_huggingface_embeddings(language_code)

        elif etype in ["lmstudio", "mlx"]:
            return EmbeddingFactory._create_openai_compatible_embeddings(etype, language_code)
        
        else:
            # Default to Ollama
            return EmbeddingFactory._create_ollama_embeddings(language_code)

    @staticmethod
    def _create_huggingface_embeddings(language_code: str) -> HuggingFaceEmbeddings:
        """Create HuggingFace embeddings (local)."""
        # Default to a good multilingual model if language is not English
        if language_code == 'en':
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
        else:
            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        
        logger.info(f"🔧 Selecting HuggingFace embedding model: {model_name}")
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'}, # Use 'mps' if sure about Mac, but 'cpu' is safest fallback
            encode_kwargs={'normalize_embeddings': True}
        )

    @staticmethod
    def _create_openai_compatible_embeddings(provider_name: str, language_code: str) -> OpenAIEmbeddings:
        """Create embeddings via OpenAI-compatible API (LM Studio, MLX)."""
        base_url = getattr(settings, "LLM_BASE_URL", "http://host.docker.internal:1234/v1")
        if language_code == 'en':
            model_name = settings.EMBEDDING_MODEL_EN
        else:
            model_name = settings.EMBEDDING_MODEL_MULTILINGUAL

        logger.info(f"🔧 Selecting {provider_name.upper()} embedding endpoint: {base_url} with model {model_name}")
        
        return OpenAIEmbeddings(
            base_url=base_url,
            api_key="lm-studio",
            model=model_name, # Identifier often ignored by LM Studio, but good practice
            check_embedding_ctx_length=False 
        )

    @staticmethod
    def _create_ollama_embeddings(language_code: str) -> OllamaEmbeddings:
        """Create Ollama embeddings."""
        if language_code == 'en':
            model_name = settings.EMBEDDING_MODEL_EN
            logger.info(f"🔧 Selecting English embedding model: {model_name}")
        else:
            model_name = settings.EMBEDDING_MODEL_MULTILINGUAL
            logger.info(f"🔧 Selecting Multilingual embedding model ({language_code}): {model_name}")

        return OllamaEmbeddings(
            model=model_name,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        )
