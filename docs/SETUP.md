# Setup Guide

This guide will help you set up and run the RAG Chatbot application using **MLX** and **LM Studio**.

## Prerequisites

-   **Operating System**: macOS 13.0+ (Apple Silicon M1/M2/M3 recommended).
-   **Python**: 3.10 or higher.
-   **LM Studio** (optional): For `LLM_PROVIDER=lmstudio` ([Download here](https://lmstudio.ai/)). Default uses MLX.

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd poc-lora-documentation-assistant
```

### 2. Create a Virtual Environment

It is recommended to use `uv` for faster dependency management, but `pip` works too.

```bash
# Using venv standard
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file to configure your local setup.

```bash
cp .env.example .env
```

Edit `.env` to ensure it points to your local LM Studio instance:

```bash
# .env content
LLM_PROVIDER=mlx  # Default. Use 'lmstudio' for LM Studio
LLM_BASE_URL=http://localhost:1234/v1  # Point to your local LM Studio server
# For Docker on Mac, use: http://host.docker.internal:1234/v1

# Embeddings are now calculated locally using HuggingFace by default.
# If you wish to use LM Studio for embeddings, set DEFAULT_EMBEDDING_TYPE="lmstudio" in config/settings.py

MLX_MODEL_PATH=mlx-community/Mistral-7B-Instruct-v0.3-4bit
MLX_ADAPTER_PATH=data/adapters

# Langfuse Observability
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

### 5. Start Langfuse (Optional but recommended)

This project includes a self-hosted Langfuse v2 instance for observability. To set it up:

1.  **Start the services**: 
    ```bash
    make deploy
    ```
2.  **Access the Dashboard**: Open your browser to `http://localhost:3000`.
3.  **Create Account & Project**: Sign up (local) and create a new project.
4.  **Get API Keys**: Go to Project Settings -> API Keys and copy the Public and Secret keys.
5.  **Update `.env`**: Paste the keys into your `.env` file and restart the chatbot:
    ```bash
    docker restart lora-frontend
    ```

### 6. Start LM Studio Server

1.  Open **LM Studio**.
2.  Go to the **Local Server** tab (double-headed arrow icon).
3.  Select a model to load (e.g., `Mistral-7B-Instruct-v0.3` or `Llama-3`).
4.  Click **Start Server**.
5.  Ensure the server is running on port `1234` (default) or update your `.env` accordingly.

## Running the Application

### Web Interface (Streamlit)

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Project Structure Overview

```
poc-lora-documentation-assistant/
├── src/
│   ├── backend/         # FastAPI backend application
│   │   ├── middleware/  # API middleware (CORS, Metrics)
│   │   ├── main.py      # API entry point
│   │   └── tasks.py     # Celery tasks for background processing
│   ├── chatbot/         # Core RAG domain logic
│   │   ├── core/        # Core business logic (events, factories)
│   │   ├── repositories/# Data access layer (Vector, Graph)
│   │   ├── services/    # Application services (Chat, Document)
│   │   └── utils/       # Shared utilities
│   └── schemas/         # Shared Pydantic configurations
├── config/              # Configuration and settings
├── data/                # Runtime data (documents, vector stores)
│   ├── documents/       # Uploaded source files
│   └── vector_stores/   # Generated FAISS indices
├── logs/                # Application logs
├── app.py               # Streamlit web interface
└── pyproject.toml       # Project metadata and dependencies
```

## Troubleshooting

### Connection Refused
-   Ensure LM Studio server is running.
-   Check if the port matches `LLM_BASE_URL` in `.env`.

### MLX Errors
-   Ensure you are running on a Mac with Apple Silicon.
-   Check that `mlx` and `mlx-lm` are installed correctly via `pip`.
