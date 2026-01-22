# Deployment Guide

This guide covers deploying the RAG Chatbot using Docker, connecting to a locally running LM Studio instance.

## Containerized Deployment

Since the chatbot relies on a local LLM server (LM Studio), the container needs access to the host machine's network.

### Prerequisites
-   Docker installed.
-   LM Studio Server running on host machine (port 1234).

### Method 1: Connecting to Host LM Studio

1.  **Configure `.env`**:
    *   **External LLM (LM Studio)**:
        ```bash
        LLM_PROVIDER=lmstudio
        LLM_BASE_URL=http://host.docker.internal:1234/v1
        ```
    *   **Internal MLX Server (Default)**:
        If using `LLM_PROVIDER=mlx` (default), the deployment script (`make deploy`) automatically starts an MLX server on the host (port 8080) and configures the container to connect to it via `http://host.docker.internal:8080/v1`.

2.  **Build & Run**:
    ```bash
    # Using Make
    make build
    make deploy   # Starts chatbot + backend + worker + redis + langfuse
    ```

### Langfuse Observability Services

The deployment includes a full observability stack (self-hosted Langfuse v2):
- **`langfuse-server`**: Access the UI at `http://localhost:3000`.
- **`langfuse-db`**: PostgreSQL database for storing traces.

#### Volume Management
Vector stores, uploaded documents, and Langfuse data are persisted using Docker volumes:
- `langfuse-db-data`: Stores the Postgres database for Langfuse.
- Local `./data` and `./logs` are mounted for application state.

To perform a clean installation (removing all data and volumes):
```bash
make clean-all && make deploy
```

## Production Notes

-   **Data Persistence**: The `./data` directory is mounted to persist vector stores and processed documents.
-   **Security**: The container runs as a non-root user.
-   **Performance**: For best performance on Mac, running natively (`streamlit run app.py`) is often faster than Docker due to virtualization overhead, especially if using MLX direct inference.
