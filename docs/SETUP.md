# Setup Guide

This guide will help you set up and run the RAG Chatbot application using **MLX** and **LM Studio**.

## Prerequisites

-   **Operating System**: macOS 13.0+ (Apple Silicon M1/M2/M3 recommended).
-   **Python**: 3.10 or higher.
-   **LM Studio**: Installed and running ([Download here](https://lmstudio.ai/)).

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
LLM_PROVIDER=lmstudio  # or 'mlx'
LLM_BASE_URL=http://localhost:1234/v1  # Point to your local LM Studio server
# Embeddings are now calculated locally using HuggingFace by default.
# If you wish to use LM Studio for embeddings, set DEFAULT_EMBEDDING_TYPE="lmstudio" in config/settings.py

MLX_MODEL_PATH=mlx-community/Mistral-7B-Instruct-v0.3-4bit

```

### 5. Start LM Studio Server

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
├── src/chatbot/          # Main application package
│   ├── core/            # Core modules
│   │   ├── events/      # Event handling (EventBus)
│   │   ├── factories/   # Object factories (LLM, Embedding, Loader, Logger)
│   │   ├── processing/  # Document processing and chunking
│   │   └── storage/     # Vector and Graph store managers
│   └── utils/           # Utility functions
├── config/              # Configuration and settings
├── data/               # Runtime data (documents, vector stores)
│   ├── documents/       # Uploaded source files
│   └── vector_stores/   # Generated FAISS indices
├── logs/               # Application logs (Session and Task logs)
├── app.py             # Streamlit web interface
└── pyproject.toml     # Project metadata and dependencies
```

## Troubleshooting

### Connection Refused
-   Ensure LM Studio server is running.
-   Check if the port matches `LLM_BASE_URL` in `.env`.

### MLX Errors
-   Ensure you are running on a Mac with Apple Silicon.
-   Check that `mlx` and `mlx-lm` are installed correctly via `pip`.
