#!/bin/bash
# Development mode script with hot reload
# Starts container with source code mounted as volumes

set -e

echo "======================================"
echo "RAG Chatbot - Development Mode"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse flags
PULL_MODELS=false
MODEL_TO_PULL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --pull-models)
            PULL_MODELS=true
            shift
            ;;
        --pull-model)
            PULL_MODELS=true
            MODEL_TO_PULL="$2"
            shift 2
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            echo "Usage: $0 [--pull-models] [--pull-model MODEL_NAME]"
            echo "  --pull-models           Pull all Ollama models after starting"
            echo "  --pull-model MODEL      Pull specific Ollama model (e.g., llama3.2:3b)"
            exit 1
            ;;
    esac
done

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file with your configuration:"
    echo "  cp .env.example .env"
    echo "  # Edit .env and add your API keys"
    exit 1
fi

# Source environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"

# Compose file location
COMPOSE_FILE="docker-compose.yml"

# Check for compose tool
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose -f $COMPOSE_FILE"
    echo -e "${GREEN}✓ Using docker-compose${NC}"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose -f $COMPOSE_FILE"
    echo -e "${GREEN}✓ Using docker compose plugin${NC}"
else
    echo -e "${RED}Error: docker-compose not found${NC}"
    exit 1
fi

# Cleanup buildx container which can block startup
if docker ps -a --format "{{.Names}}" | grep -q "^buildx_buildkit_default$"; then
    echo -e "${YELLOW}Stopping and removing buildx_buildkit_default container...${NC}"
    docker stop buildx_buildkit_default >/dev/null 2>&1 || true
    docker rm buildx_buildkit_default >/dev/null 2>&1 || true
    echo -e "${GREEN}✓ buildx_buildkit_default removed${NC}"
fi

# Start all services using compose with project name to avoid state issues
echo -e "\n${GREEN}Starting development stack (Ollama, Redis, Backend, Worker, Frontend)...${NC}"
DOCKER_BUILDKIT=1 $COMPOSE_CMD -p rag-fresh up --build -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check if containers are running
if docker ps | grep -q rag-chatbot; then
    echo -e "\n${GREEN}======================================"
    echo "✓ Development mode started!"
    echo "======================================${NC}"
    echo ""
    echo "Services running:"
    echo "  - Frontend:      http://localhost:8501"
    echo "  - Backend API:   http://localhost:8000/docs"
    echo "  - Ollama:        http://localhost:11434"
    echo ""
    echo "Hot reload enabled for:"
    echo "  - app.py"
    echo "  - src/"
    echo "  - config/"
    echo "  - .streamlit/"
    echo ""
    echo "Changes to these files will be reflected immediately!"
    echo ""
    echo "Useful commands:"
    echo "  View logs:           docker logs -f rag-chatbot"
    echo "  View ollama logs:    docker logs -f ollama"
    echo "  Stop dev container:  docker stop rag-chatbot"
    echo "  Stop all:            $COMPOSE_CMD down"
    echo "  Pull ollama models:  ./scripts/pull-ollama-models.sh [--all|model_name]"
    echo ""

    # Pull Ollama models if requested
    if [ "$PULL_MODELS" = true ]; then
        echo -e "${YELLOW}Waiting for Ollama to be fully ready...${NC}"
        sleep 3

        if [ -n "$MODEL_TO_PULL" ]; then
            echo -e "${GREEN}Pulling Ollama model: $MODEL_TO_PULL${NC}"
            ./scripts/pull-ollama-models.sh "$MODEL_TO_PULL"
        else
            echo -e "${GREEN}Pulling all Ollama models...${NC}"
            ./scripts/pull-ollama-models.sh --all
        fi
    else
        echo -e "${YELLOW}Note: No Ollama models pulled. To pull models, run:${NC}"
        echo "  ./scripts/pull-ollama-models.sh --all"
        echo "  or: ./scripts/pull-ollama-models.sh llama3.2:3b"
    fi
else
    echo -e "\n${RED}======================================"
    echo "✗ Failed to start development mode!"
    echo "======================================${NC}"
    echo "Check logs with: docker logs rag-chatbot"
    exit 1
fi
