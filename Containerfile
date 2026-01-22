# syntax=docker/dockerfile:1.4
# Containerfile for RAG Chatbot - Optimized for fast builds
# Compatible with Podman and Docker

# ============================================
# Base stage - System and Python setup
# ============================================
FROM docker.io/library/python:3.10-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# ============================================
# Dependencies stage - cached separately
# ============================================
FROM base AS dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with pip cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Common stage - Application code
# ============================================
FROM dependencies AS common

# Create necessary directories
RUN mkdir -p data/documents data/vector_stores logs /app/.cache/huggingface && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser .streamlit/ ./.streamlit/

# Switch to non-root user
USER appuser

# ============================================
# Frontend stage (Streamlit)
# ============================================
FROM common AS frontend

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# ============================================
# Backend stage (FastAPI)
# ============================================
FROM common AS backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# ============================================
# Worker stage (Celery)
# ============================================
FROM common AS worker

# No specific port exposed for worker usually, unless for monitoring
# Healthcheck for worker involves checking celery status (often via specialized command or file touch)
# For simplicity, we skip HEALTHCHECK here or use a dummy one if needed.
# A basic check could be checking if the process is running.

CMD ["celery", "-A", "src.backend.celery_config", "worker", "--loglevel=info"]
