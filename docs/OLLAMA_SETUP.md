# Ollama Setup Guide

This guide explains how to use Ollama as an LLM provider alongside Groq.

## Overview

The RAG chatbot now supports two LLM providers:
- **Groq**: Cloud API (fast, requires API key)
- **Ollama**: Local containerized LLM (no API key needed)

## Quick Start with Ollama

### 1. Deploy with Ollama

```bash
make deploy
```

This will start both the chatbot and Ollama containers:
- Chatbot: http://localhost:8501
- Ollama API: http://localhost:11434

### 2. Pull an Ollama Model

Before using Ollama, you need to pull at least one model:

```bash
# Pull llama3.2:3b (recommended)
podman exec ollama ollama pull llama3.2:3b

# Or pull other models
podman exec ollama ollama pull llama3.1:70b  # Large model, ~40GB
```

### 3. Select Ollama in the UI

1. Open http://localhost:8501
2. In the sidebar, select **"Ollama"** under "LLM Provider"
3. Choose your model from the dropdown
4. Upload a document and start chatting!

## Architecture

```
┌─────────────────┐      ┌──────────────┐
│  rag-chatbot    │─────▶│   ollama     │
│  (Streamlit)    │      │  (LLM Server)│
│  Port: 8501     │      │  Port: 11434 │
└─────────────────┘      └──────────────┘
         │
         │ (shared network: rag-network)
         │
         ▼
    Data Volumes
    - documents
    - vector_stores
    - ollama-data (models)
```

## Available Models

### Small Models
- `llama3.2:3b` - Fast, good quality
- `mistral:latest` - Fast, lightweight

### Medium Models (~20GB)
- `mixtral:latest` - High quality

### Large Models (~40GB+)
- `llama3.1:70b` - Highest quality, slower

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
OLLAMA_BASE_URL=http://ollama:11434
```

### podman-compose.yml

The Ollama service is configured with:
- Persistent volume for models (`ollama-data`)
- Health check on API endpoint
- Shared network with chatbot

## Switching Between Providers

You can switch between Groq and Ollama at any time in the UI:

1. **Use Groq** when you want:
   - Fastest inference speed
   - Cloud-based processing
   - Latest Groq-optimized models

2. **Use Ollama** when you want:
   - Complete local processing
   - No API costs
   - More model variety
   - Privacy (data stays local)

## Troubleshooting

### Ollama container not starting

```bash
# Check container status
podman ps -a | grep ollama

# View logs
podman logs ollama
```

### Model not found

```bash
# List downloaded models
podman exec ollama ollama list

# Pull the missing model
podman exec ollama ollama pull llama3.2:3b
```

### Connection error

Ensure both containers are on the same network:

```bash
podman network inspect rag-network
```

### Out of disk space

Ollama models are large. Check available space:

```bash
df -h
podman system df
```

Remove unused models:

```bash
podman exec ollama ollama rm <model-name>
```

## Performance Tips

1. **GPU Support**: For better performance, use Ollama with GPU support (requires NVIDIA GPU)
2. **Model Size**: Start with smaller models (8B parameters) before trying larger ones
3. **Memory**: Ensure you have enough RAM (16GB+ recommended for 8B models)

## Development Mode

When using `make dev`, Ollama will also be started:

```bash
make dev
```

The chatbot can communicate with Ollama via the container network.

## Commands Reference

```bash
# Start everything
make deploy

# Stop everything
make stop

# View logs
make logs

# Pull a new model
podman exec ollama ollama pull <model-name>

# List models
podman exec ollama ollama list

# Remove a model
podman exec ollama ollama rm <model-name>

# Check Ollama status
curl http://localhost:11434/api/version
```

## Comparison: Groq vs Ollama

| Feature | Groq | Ollama |
|---------|------|--------|
| Speed | Very Fast | Moderate (CPU) to Fast (GPU) |
| Cost | API usage | Free (local compute) |
| Privacy | Cloud | Complete local |
| Setup | API key only | Pull models (~GB) |
| Models | Groq-optimized | Wide variety |
| Latency | Low | Very low (local) |
| Scalability | Unlimited | Limited by hardware |
