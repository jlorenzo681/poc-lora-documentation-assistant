# LoRA-Enhanced RAG Chatbot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![MLX](https://img.shields.io/badge/MLX-Apple%20Silicon-green)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)

A Retrieval Augmented Generation (RAG) chatbot optimized for Apple Silicon using **MLX** and **LM Studio**. This project supports local document ingestion (PDF, TXT, MD), vector similarity search, and optional LoRA fine-tuning integration.

## Features

-   **Apple Silicon Optimization**: Built with Apple's MLX framework for efficient local inference on Macs.
-   **Local & Secure**: Run completely offline using local models via LM Studio. No data leaves your machine.
-   **RAG Architecture**: Upload documents to create a knowledge base and ask questions about them.
-   **LoRA Support**: Architecture ready for integrating Low-Rank Adaptation (LoRA) fine-tuned adapters.
-   **Flexible Embeddings**: Default local embeddings via HuggingFace (MiniLM), with support for LM Studio.

## Documentation

-   [**Quick Start**](docs/QUICKSTART.md): Get up and running in minutes.
-   [**Setup Guide**](docs/SETUP.md): Detailed installation and environment configuration.
-   [**Deployment**](docs/DEPLOYMENT.md): How to deploy using Docker/Podman.

## Prerequisites

-   **Apple Silicon Mac** (M1/M2/M3) recommended for MLX.
-   **LM Studio** ([Download](https://lmstudio.ai/)) running locally as the LLM server.
-   Python 3.10+.

## Architecture

The system uses a decoupled architecture:
-   **Frontend**: Streamlit for the chat interface.
-   **Backend**: Python core handling document processing and RAG logic.
-   **LLM Provider**: LM Studio (server mode) or MLX direct inference.
-   **Vector Store**: FAISS for fast similarity search.

## License

[MIT](LICENSE)
