#!/bin/bash
# View logs from RAG Chatbot or Ollama container

set -e

# Parse arguments
# Parse arguments
CONTAINER="lora-chatbot"
if [ "$1" = "backend" ]; then
    CONTAINER="lora-backend"
elif [ "$1" = "worker" ]; then
    CONTAINER="lora-worker"
elif [ "$1" = "redis" ]; then
    CONTAINER="lora-redis"
elif [ "$1" = "langfuse" ]; then
    CONTAINER="poc-lora-documentation-assistant-langfuse-server-1"
elif [ "$1" = "mlx" ]; then
    if [ -f ".mlx_server.log" ]; then
        echo "Viewing MLX Server logs (Ctrl+C to exit)..."
        echo "=============================================="
        tail -f .mlx_server.log
        exit 0
    else
        echo "Error: .mlx_server.log not found. Is the server running?"
        exit 1
    fi
elif [ "$1" = "all" ]; then
    # Show both logs side by side (requires docker-compose or docker compose)
    if docker compose version &> /dev/null; then
        echo "Viewing all service logs (Ctrl+C to exit)..."
        echo "=============================================="
        # This only shows docker logs, not local file logs unfortunately
        docker compose logs -f
        exit 0
    elif command -v docker-compose &> /dev/null; then
        echo "Viewing all service logs (Ctrl+C to exit)..."
        echo "=============================================="
        docker-compose logs -f
        exit 0
    else
        echo "Error: docker-compose not available. Showing lora-chatbot logs only."
        echo "Usage: $0 [backend|worker|redis|mlx|all]"
        echo "Default: lora-chatbot"
    fi
fi

echo "Viewing $CONTAINER logs (Ctrl+C to exit)..."
echo "=============================================="

docker logs -f $CONTAINER
