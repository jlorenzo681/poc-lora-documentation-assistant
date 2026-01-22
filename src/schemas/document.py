
from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
import os

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 MB
ALLOWED_FILE_TYPES = {
    'application/pdf': '.pdf',
    'text/plain': '.txt',
    'text/markdown': '.md'
}

class TaskResponse(BaseModel):
    task_id: str
    filename: str
    status: str
    message: str

class DocumentUploadParams(BaseModel):
    api_key: Optional[str] = None
    embedding_type: Literal["huggingface", "lmstudio", "mlx"] = "huggingface"
    llm_model: Optional[str] = None

    model_config = ConfigDict(extra='ignore')
