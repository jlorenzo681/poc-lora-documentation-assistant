#!/bin/bash
# View logs from RAG Chatbot or Ollama container

set -e

# Parse arguments
CONTAINER="rag-chatbot"
if [ "$1" = "ollama" ]; then
    CONTAINER="ollama"
elif [ "$1" = "all" ]; then
    # Show both logs side by side (requires docker-compose or docker compose)
    if docker compose version &> /dev/null; then
        echo "Viewing all service logs (Ctrl+C to exit)..."
        echo "=============================================="
        docker compose logs -f
        exit 0
    elif command -v docker-compose &> /dev/null; then
        echo "Viewing all service logs (Ctrl+C to exit)..."
        echo "=============================================="
        docker-compose logs -f
        exit 0
    else
        echo "Error: docker-compose not available. Showing rag-chatbot logs only."
        echo "Usage: $0 [rag-chatbot|ollama|all]"
    fi
fi

echo "Viewing $CONTAINER logs (Ctrl+C to exit)..."
echo "=============================================="

docker logs -f $CONTAINER
