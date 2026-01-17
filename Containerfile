# syntax=docker/dockerfile:1.4
# Containerfile for RAG Chatbot - Optimized for fast builds
# Compatible with Podman and Docker

FROM docker.io/library/python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface

# Install system dependencies in a single layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Dependencies stage - cached separately
# ============================================
FROM base AS dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with pip cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Pre-download HuggingFace model step removed to use local cache

# ============================================
# Final stage - application code
# ============================================
FROM dependencies AS final

# Create necessary directories
RUN mkdir -p data/documents data/vector_stores logs /app/.cache/huggingface

# Copy only essential application code (not everything)
COPY app.py .
COPY config/ ./config/
COPY src/ ./src/
COPY .streamlit/ ./.streamlit/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
