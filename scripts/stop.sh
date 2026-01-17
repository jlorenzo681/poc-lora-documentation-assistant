#!/bin/bash
# Stop RAG Chatbot and Ollama containers

set -e

echo "Stopping RAG Chatbot and Ollama services..."

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
    docker stop rag-chatbot 2>/dev/null || true
    docker stop ollama 2>/dev/null || true
    docker rm rag-chatbot 2>/dev/null || true
    docker rm ollama 2>/dev/null || true
fi

echo "✓ All services stopped"
