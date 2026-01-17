from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .celery_config import celery_app
from .tasks import process_document_task
import shutil
import os
import re

app = FastAPI(title="RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    api_key: str = Form(""),
    embedding_type: str = Form("huggingface"),
    llm_model: str = Form(None) 
):
    try:
        filename = sanitize_filename(file.filename)
        file_path = os.path.join(DOCUMENTS_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Trigger Celery Task
        task = process_document_task.delay(file_path, api_key, embedding_type, llm_model)
        
        return {
            "task_id": task.id, 
            "filename": filename, 
            "status": "processing",
            "message": "File uploaded and processing started"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
