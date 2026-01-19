#!/bin/bash
# Stop RAG Chatbot and Ollama containers

set -e

echo "Stopping RAG Chatbot, Ollama and MLX Server services..."

# MLX Server PID file
MLX_SERVER_PID_FILE=".mlx_server.pid"

if [ -f "$MLX_SERVER_PID_FILE" ]; then
    PID=$(cat "$MLX_SERVER_PID_FILE")
    echo "Stopping MLX Server (PID: $PID)..."
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "✓ MLX Server stopped"
    else
        echo "⚠ MLX Server process not found (stale PID)"
    fi
    rm "$MLX_SERVER_PID_FILE"
fi

# Compose file
COMPOSE_FILE="docker-compose.yml"

# Check if docker-compose is available and use correct command
if command -v docker-compose &> /dev/null; then
    echo "Using docker-compose..."
    docker-compose -f $COMPOSE_FILE -p rag-fresh down
elif docker compose version &> /dev/null; then
    echo "Using docker compose plugin..."
    docker compose -f $COMPOSE_FILE -p rag-fresh down
else
    # Manual stop - stop both containers
    echo "Stopping containers manually..."
    docker stop lora-chatbot 2>/dev/null || true
    docker stop lora-backend 2>/dev/null || true
    docker stop lora-worker 2>/dev/null || true
    docker stop lora-redis 2>/dev/null || true
    docker rm lora-chatbot 2>/dev/null || true
    docker rm lora-backend 2>/dev/null || true
    docker rm lora-worker 2>/dev/null || true
    docker rm lora-redis 2>/dev/null || true
fi

echo "✓ All services stopped"
