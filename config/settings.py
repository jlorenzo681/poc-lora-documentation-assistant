"""
Configuration settings for the RAG Chatbot application.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT: Path = Path(__file__).parent.parent

# Data directories
DATA_DIR: Path = PROJECT_ROOT / "data"
DOCUMENTS_DIR: Path = DATA_DIR / "documents"
VECTOR_STORES_DIR: Path = DATA_DIR / "vector_stores"
LOGS_DIR: Path = PROJECT_ROOT / "logs"

# Document Processing Settings
DEFAULT_CHUNK_SIZE: int = 1000
DEFAULT_CHUNK_OVERLAP: int = 200

# Embedding Settings
DEFAULT_EMBEDDING_TYPE: str = "huggingface"  # Options: "huggingface", "lmstudio", "mlx"

# Dynamic Embedding Models
EMBEDDING_MODEL_EN: str = "nomic-ai/nomic-embed-text-v1.5-GGUF" # High quality English model (LM Studio)
EMBEDDING_MODEL_MULTILINGUAL: str = "text-embedding-bge-m3"   # High quality Multilingual model (LM Studio)
FASTTEXT_MODEL_PATH: str = "data/models/lid.176.ftz"

# LoRA Settings (Training)
ENABLE_LORA: bool = True
TRAINING_LLM_PROVIDER: str = "mlx"
TRAINING_MODEL: str = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
MLX_MODEL_PATH: str = TRAINING_MODEL # Alias for backward compatibility if needed
MLX_ADAPTER_PATH: str = "data/adapters"


# LLM Settings (Runtime / Docker)
# Provider options: "lmstudio" (default), "mlx_server"
DEFAULT_LLM_PROVIDER: str = "lmstudio" 

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mlx") # Options: "mlx", "lmstudio"
DEFAULT_LLM_PROVIDER = "mlx" 
LM_STUDIO_URL = os.getenv("LLM_BASE_URL", "http://host.docker.internal:8080/v1") # Default to MLX Server for Docker
LLM_BASE_URL = LM_STUDIO_URL # Alias for compatibility

# MLX Specifics (for local training/inference)
MLX_MODEL_PATH = os.getenv("MLX_MODEL_PATH", "mlx-community/Mistral-7B-Instruct-v0.3-4bit")
MLX_ADAPTER_PATH = os.getenv("MLX_ADAPTER_PATH", "data/adapters")

# RAG Settings (Restored)
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
VECTOR_STORE_PATH = os.path.join(DATA_DIR, "vector_stores")

DEFAULT_TEMPERATURE: float = 0.3
DEFAULT_MAX_TOKENS: int = 500
DEFAULT_RETRIEVAL_K: int = 4

# Memory Settings
DEFAULT_MEMORY_TYPE: str = "buffer"  # or "window"
DEFAULT_WINDOW_SIZE: int = 5

# Streamlit Settings
STREAMLIT_PAGE_TITLE: str = "Document Q&A Chatbot"
STREAMLIT_PAGE_ICON: str = "📚"
STREAMLIT_LAYOUT: str = "wide"

# Supported file types
SUPPORTED_FILE_TYPES: List[str] = ["pdf", "txt", "md"]



# Create directories if they don't exist
for directory in [DATA_DIR, DOCUMENTS_DIR, VECTOR_STORES_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
