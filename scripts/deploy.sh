#!/bin/bash
# Deployment script for RAG Chatbot using Docker

set -e

echo "======================================"
echo "RAG Chatbot - Docker Deployment"
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
            echo "  --pull-models           Pull all Ollama models after deployment"
            echo "  --pull-model MODEL      Pull specific Ollama model (e.g., llama3.2:3b)"
            exit 1
            ;;
    esac
done

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file with your API keys:"
    echo "  cp .env.example .env"
    exit 1
fi

# Source environment variables
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
    echo -e "${RED}Error: No compose tool found${NC}"
    echo "Please install Docker Desktop properly."
    exit 1
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data/documents data/vector_stores logs

# Generate requirements.txt
echo "Generating requirements.txt..."
uv export --format requirements-txt > requirements.txt

# Build the image only if it doesn't exist
if ! docker image inspect rag-chatbot:latest >/dev/null 2>&1; then
    echo -e "\n${YELLOW}Image not found. Building container image...${NC}"
    docker build -t rag-chatbot:latest -f Containerfile .
else
    echo -e "\n${GREEN}✓ Image rag-chatbot:latest already exists${NC}"
fi

# Stop existing containers via compose
echo -e "\n${YELLOW}Stopping existing containers...${NC}"
$COMPOSE_CMD down 2>/dev/null || true

# Cleanup buildx container which can block startup
if docker ps -a --format "{{.Names}}" | grep -q "^buildx_buildkit_default$"; then
    echo -e "${YELLOW}Stopping and removing buildx_buildkit_default container...${NC}"
    docker stop buildx_buildkit_default >/dev/null 2>&1 || true
    docker rm buildx_buildkit_default >/dev/null 2>&1 || true
    echo -e "${GREEN}✓ buildx_buildkit_default removed${NC}"
fi

# Start all services using compose
echo -e "\n${GREEN}Starting RAG Chatbot and Ollama services...${NC}"
$COMPOSE_CMD up -d

# Wait for application to start
echo -e "\n${YELLOW}Waiting for application to start...${NC}"
sleep 5

# Check if containers are running
if docker ps | grep -q rag-chatbot && docker ps | grep -q ollama; then
    echo -e "\n${GREEN}======================================"
    echo "✓ Deployment successful!"
    echo "======================================${NC}"
    echo ""
    echo "Services running:"
    echo "  - RAG Chatbot: http://localhost:8501"
    echo "  - Ollama:      http://localhost:11434"
    echo ""
    echo "Useful commands:"
    echo "  View logs:           docker logs -f rag-chatbot"
    echo "  View ollama logs:    docker logs -f ollama"
    echo "  Stop all:            $COMPOSE_CMD down"
    echo "  Restart all:         $COMPOSE_CMD restart"
    echo "  Container status:    $COMPOSE_CMD ps"
    echo "  Pull ollama models:  ./scripts/pull-ollama-models.sh [--all|model_name]"
    echo ""

    # Pull Ollama models if requested
    if [ "$PULL_MODELS" = true ]; then
        echo -e "${YELLOW}Waiting for Ollama to be fully ready...${NC}"
        sleep 5

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
    echo "✗ Deployment failed!"
    echo "======================================${NC}"
    echo "Check logs with:"
    echo "  docker logs rag-chatbot"
    echo "  docker logs ollama"
    exit 1
fi
