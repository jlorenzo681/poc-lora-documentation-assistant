# API Documentation

The LoRA RAG Chatbot exposes a RESTful API via FastAPI for document management and chatbot interaction (extensible).

## Base URL
`http://localhost:8000` (Local)

## Endpoints

### Health Check

- **GET** `/health`
- **Description**: Check if the backend is running.
- **Response**: `200 OK`
  ```json
  {"status": "ok"}
  ```

### Document Upload

- **POST** `/upload`
- **Description**: Upload a document for processing (chunking, embedding, indexing).
- **Parameters** (Form Data):
    - `file`: The document file (PDF, TXT, MD). Max 10MB.
    - `api_key`: Optional API Key for tracking.
    - `embedding_type`: Embedding model to use (`huggingface`, `lmstudio`, `mlx`). Default: `huggingface`.
    - `llm_model`: Optional LLM model specification.
- **Response**: `200 OK`
  ```json
  {
      "task_id": "uuid-string",
      "filename": "document.pdf",
      "status": "processing",
      "message": "File uploaded and processing started"
  }
  ```
- **Errors**:
    - `400 Bad Request`: Invalid file type or size.
    - `500 Internal Server Error`: Processing failure.

### Task Status

- **GET** `/tasks/{task_id}`
- **Description**: Check the status of a background processing task (Celery).
- **Parameters**:
    - `task_id`: ID returned from `/upload`.
- **Response**: `200 OK`
  ```json
  {
      "task_id": "uuid-string",
      "status": "SUCCESS", # OR PENDING, STARTED, FAILURE
      "result": { ... } # If success
  }
  ```

## Authentication
Currently, the API has basic CORS restrictions but does not enforce authentication tokens for all endpoints. This is improved in `main.py` via `ALLOWED_ORIGINS` but `api_key` param is currently just a placeholder for future implementation.
