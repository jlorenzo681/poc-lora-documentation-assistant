# Deployment Guide

This guide covers deploying the RAG Chatbot using Docker/Podman, connecting to a locally running LM Studio instance.

## Containerized Deployment

Since the chatbot relies on a local LLM server (LM Studio), the container needs access to the host machine's network.

### Prerequisites
-   Docker or Podman installed.
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
    make deploy
    
    # Or manual
    docker build -t rag-chatbot -f Containerfile .
    docker run -d -p 8502:8501 --add-host=host.docker.internal:host-gateway --env-file .env -v ./data:/app/data -v ./logs:/app/logs rag-chatbot
    ```

    *Note: `--add-host=host.docker.internal:host-gateway` is crucial for Linux/Podman. Docker Desktop for Mac handles this automatically.*

### Method 2: Development Mode

To develop locally with hot-reloading:

```bash
make dev
```
(See `scripts/dev.sh` for details on how this mounts your local directory).

## Production Notes

-   **Data Persistence**: The `./data` directory is mounted to persist vector stores and processed documents.
-   **Security**: The container runs as a non-root user.
-   **Performance**: For best performance on Mac, running natively (`streamlit run app.py`) is often faster than Docker due to virtualization overhead, especially if using MLX direct inference.
