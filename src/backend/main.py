from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from .celery_config import celery_app
from .tasks import process_document_task
from src.schemas.document import DocumentUploadParams, MAX_FILE_SIZE, ALLOWED_FILE_TYPES
import shutil
import os
import re

app = FastAPI(title="RAG Chatbot API")

# Security: CORS Check
# In production, this should be restricted to specific domains.
# For local dev, we allow Streamlit and localhost.
ALLOWED_ORIGINS = [
    "http://localhost:8501", # Streamlit default
    "http://localhost:8502", # Streamlit custom
    "http://127.0.0.1:8501",
    "http://127.0.0.1:8502",
]

# Allow overriding via env (comma separated)
EXTRA_ORIGINS = os.getenv("ALLOWED_ORIGINS")
if EXTRA_ORIGINS:
    ALLOWED_ORIGINS.extend(EXTRA_ORIGINS.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"], # Explicitly allow only needed methods
    allow_headers=["*"],
)

# Observability: Prometheus Metrics
from src.backend.middleware.metrics import PrometheusMiddleware, metrics_endpoint
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics_endpoint)

from src.backend.routers import connectors
app.include_router(connectors.router)

DOCUMENTS_DIR = "data/documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    # Logic matched from app.py to ensure consistency
    name_parts = filename.rsplit(".", 1)
    base_name = name_parts[0]
    extension = name_parts[1] if len(name_parts) > 1 else ""
    sanitized_base = re.sub(r"[^\w\s\-\.]", "_", base_name)
    sanitized_base = re.sub(r"[\s_]+", "_", sanitized_base)
    sanitized_base = sanitized_base.strip("_")
    if sanitized_base:
        return f"{sanitized_base}.{extension}" if extension else sanitized_base
    else:
        return f"document.{extension}" if extension else "document"

def validate_file(file: UploadFile) -> None:
    """Validate file size and type."""
    # Check file type
    if file.content_type not in ALLOWED_FILE_TYPES:
         raise HTTPException(
             status_code=400, 
             detail=f"Invalid file type. Allowed: {list(ALLOWED_FILE_TYPES.keys())}"
         )
    
    # Check file size (approximate using seek)
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE/1024/1024}MB"
        )

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    params: DocumentUploadParams = Depends()
):
    try:
        # 1. Validation 
        if not file.filename:
             raise HTTPException(status_code=400, detail="No filename provided")
        
        validate_file(file)
        
        # 2. Sanitize
        filename = sanitize_filename(file.filename)
        # Ensure extension matches content type to prevent spoofing
        expected_ext = ALLOWED_FILE_TYPES.get(file.content_type)
        if expected_ext and not filename.endswith(expected_ext):
             # Force correct extension
             filename = os.path.splitext(filename)[0] + expected_ext

        file_path = os.path.join(DOCUMENTS_DIR, filename)
        
        # 3. Save
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except IOError as e:
             raise HTTPException(status_code=500, detail=f"Failed to write file to disk: {str(e)}")
            
        # 4. Trigger Celery Task
        # 4. Trigger Celery Task
        task = process_document_task.delay(
            file_path, 
            params.api_key, 
            params.embedding_type, 
            params.llm_model
        )
        
        return {
            "task_id": task.id, 
            "filename": filename, 
            "status": "processing",
            "message": "File uploaded and processing started"
        }
    except HTTPException:
        raise
    except Exception as e:
        # Global fallback
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error during upload")

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task_result = celery_app.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.status == 'SUCCESS':
         response["result"] = task_result.result
    elif task_result.status == 'FAILURE':
         response["error"] = str(task_result.result)
    elif task_result.status == 'PROGRESS':
        response["result"] = task_result.info
         
    return response

@app.get("/health")
def health_check():
    return {"status": "ok"}
