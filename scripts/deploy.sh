#!/bin/bash
# Deployment script for RAG Chatbot using Docker

set -e

echo "======================================"
echo "LoRA RAG Documentation assistant - Docker Deployment"
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
# Build images if they don't exist
if ! docker image inspect lora-frontend:latest >/dev/null 2>&1 || \
   ! docker image inspect lora-backend:latest >/dev/null 2>&1 || \
   ! docker image inspect lora-worker:latest >/dev/null 2>&1; then
    echo -e "\n${YELLOW}One or more images not found. Running build script...${NC}"
    ./scripts/build.sh
else
    echo -e "\n${GREEN}✓ All container images already exist${NC}"
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

# Start MLX Server if requested or default
MLX_SERVER_PID_FILE=".mlx_server.pid"
MLX_SERVER_LOG=".mlx_server.log"

if [ "$LLM_PROVIDER" = "mlx" ] || [ -z "$LLM_PROVIDER" ]; then
    echo -e "\n${YELLOW}Starting MLX Server...${NC}"
    MLX_ALREADY_RUNNING=false

    # 1. Check by port (most reliable)
    if curl -s http://localhost:8080/v1/models >/dev/null; then
        echo -e "${GREEN}✓ MLX Server detected running on port 8080${NC}"
        MLX_ALREADY_RUNNING=true
    # 2. Check by PID file
    elif [ -f "$MLX_SERVER_PID_FILE" ]; then
        if ps -p $(cat "$MLX_SERVER_PID_FILE") > /dev/null; then
            echo -e "${GREEN}✓ MLX Server already running (PID: $(cat "$MLX_SERVER_PID_FILE"))${NC}"
            MLX_ALREADY_RUNNING=true
        else
            rm "$MLX_SERVER_PID_FILE"
        fi
    fi

    if [ "$MLX_ALREADY_RUNNING" = false ]; then
        # Determine Python interpreter
        if [ -f ".venv/bin/python" ]; then
            PYTHON_CMD=".venv/bin/python"
        elif [ -f ".venv/bin/python3" ]; then
            PYTHON_CMD=".venv/bin/python3"
        else
            PYTHON_CMD="python3"
        fi
        
        nohup $PYTHON_CMD scripts/serve_mlx_model.py --port 8080 > "$MLX_SERVER_LOG" 2>&1 &
        echo $! > "$MLX_SERVER_PID_FILE"
        echo -e "${GREEN}✓ MLX Server started (PID: $(cat "$MLX_SERVER_PID_FILE"))${NC}"
        echo "Waiting for MLX Server to be ready..."
        # Simple wait loop
        for i in {1..30}; do
            if curl -s http://localhost:8080/v1/models >/dev/null; then
                echo -e "${GREEN}✓ MLX Server is ready${NC}"
                break
            fi
            sleep 1
        done
    fi
fi

# Wait for application to start
echo -e "\n${YELLOW}Waiting for application to start...${NC}"
sleep 5

# Check if containers are running
if docker ps | grep -q lora-frontend; then
    echo -e "\n${GREEN}======================================"
    echo "✓ Deployment successful!"
    echo "======================================${NC}"
    echo ""
    echo "Services running:"
    echo "  - Frontend:      http://localhost:8502"
    echo "  - Backend:     http://localhost:8001"
    if [ "$LLM_PROVIDER" = "mlx" ]; then
        echo "  - MLX Server:  http://localhost:8080"
    fi
    echo ""
    echo "Useful commands:"
    echo "  View logs:           ./scripts/logs.sh"
    echo "  Stop all:            make stop"
    echo "  Restart all:         make restart"
    echo "  Container status:    docker-compose ps"
    echo ""

else
    echo -e "\n${RED}======================================"
    echo "✗ Deployment failed!"
    echo "======================================${NC}"
    echo "Check logs with:"
    echo "  ./scripts/logs.sh"
    exit 1
fi
