# Deployment Guide

This guide covers deploying the RAG Chatbot using Docker, connecting to a locally running LM Studio instance.

## Containerized Deployment

Since the chatbot relies on a local LLM server (LM Studio), the container needs access to the host machine's network.

### Prerequisites
-   Docker installed.
-   LM Studio Server (optional, for `LLM_PROVIDER=lmstudio`). Default uses MLX.
-   Google Cloud Project with Drive API enabled (optional, for Google Drive connectors).

### Method 1: Connecting to Host LM Studio

1.  **Configure `.env`**:
    *   **Internal MLX Server (Default)**:
        ```bash
        LLM_PROVIDER=mlx
        ```
        The deployment script (`make deploy`) automatically starts an MLX server on the host (port 8080) and configures the container to connect to it via `http://host.docker.internal:8080/v1`.
    *   **External LLM (LM Studio Alternative)**:
        ```bash
        LLM_PROVIDER=lmstudio
        LLM_BASE_URL=http://host.docker.internal:1234/v1
        ```
    *   **Cloud Storage Connectors (Optional)**:
        ```bash
        GOOGLE_CLIENT_ID=your_google_client_id
        GOOGLE_CLIENT_SECRET=your_google_client_secret
        API_BASE_URL=http://localhost:8001
        ```

2.  **Build & Run**:
    ```bash
    # Using Make
    make build
    make deploy   # Starts chatbot + backend + worker + beat + redis + langfuse
    ```

3.  **Run Database Migrations** (First-time setup):
    ```bash
    docker exec -i shared-db psql -U postgres -d postgres < migrations/001_add_connectors_postgres.sql
    ```

### Services Overview

The deployment includes the following services:

- **`lora-frontend`**: Streamlit frontend at `http://localhost:8502`.
- **`lora-backend`**: FastAPI REST API at `http://localhost:8001/docs`.
- **`lora-celery_worker`**: Background task processor for document ingestion.
- **`lora-celery_beat`**: Scheduler for periodic connector syncs (every 15 minutes).
- **`lora-redis`**: Message broker for Celery tasks.
- **`langfuse-server`**: Observability UI at `http://localhost:3000`.
- **`shared-db`**: PostgreSQL database for Langfuse and connector metadata.

### Cloud Storage Connectors

The Admin UI (`pages/admin.py`) allows you to configure cloud storage connectors:

1. Navigate to the **Data Connectors** page in Streamlit (sidebar).
2. Add a new connector (Google Drive or OneDrive).
3. Complete the OAuth authorization flow.
4. Files will be automatically synced every 15 minutes via Celery Beat.

**Manual Sync**: You can trigger a manual sync from the Admin UI or via API:
```bash
curl -X POST http://localhost:8001/api/connectors/{connector_id}/sync
```

#### Volume Management
Vector stores, uploaded documents, and Langfuse data are persisted using Docker volumes:
- `langfuse-db-data`: Stores the PostgreSQL database for Langfuse and connectors.
- Local `./data` and `./logs` are mounted for application state.

To perform a clean installation (removing all data and volumes):
```bash
make clean-all && make deploy
```

## Production Notes

-   **Data Persistence**: The `./data` directory is mounted to persist vector stores and processed documents.
-   **Security**: The container runs as a non-root user. OAuth credentials are stored encrypted in the database.
-   **Performance**: For best performance on Mac, running natively (`streamlit run app.py`) is often faster than Docker due to virtualization overhead, especially if using MLX direct inference.
-   **Database Backups**: Regularly backup the `langfuse-db-data` volume to preserve connector configurations and sync state.
