#!/bin/bash
# Development mode script with hot reload
# Starts container with source code mounted as volumes

set -e

echo "======================================"
echo "LoRA RAG Documentation assistant - Development Mode"
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

# Start MLX Server if requested or default
MLX_SERVER_PID_FILE=".mlx_server.pid"
MLX_SERVER_LOG=".mlx_server.log"

if [ "$LLM_PROVIDER" = "mlx" ] || [ -z "$LLM_PROVIDER" ]; then
    echo -e "\n${YELLOW}Starting MLX Server (Dev Mode)...${NC}"
    if [ -f "$MLX_SERVER_PID_FILE" ]; then
        if ps -p $(cat "$MLX_SERVER_PID_FILE") > /dev/null; then
            echo -e "${GREEN}✓ MLX Server already running (PID: $(cat "$MLX_SERVER_PID_FILE"))${NC}"
        else
            rm "$MLX_SERVER_PID_FILE"
        fi
    fi

    if [ ! -f "$MLX_SERVER_PID_FILE" ]; then
        nohup python3 scripts/serve_mlx_model.py --port 8080 > "$MLX_SERVER_LOG" 2>&1 &
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

# Start all services using compose
echo -e "\n${GREEN}Starting development stack (Redis, Backend, Worker, Frontend)...${NC}"
DOCKER_BUILDKIT=1 $COMPOSE_CMD up --build -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check if containers are running
if docker ps | grep -q lora-chatbot; then
    echo -e "\n${GREEN}======================================"
    echo "✓ Development mode started!"
    echo "======================================${NC}"
    echo ""
    echo "Services running:"
    echo "  - Frontend:      http://localhost:8502"
    echo "  - Backend API:   http://localhost:8001"
    if [ "$LLM_PROVIDER" = "mlx" ]; then
        echo "  - MLX Server:  http://localhost:8080"
    fi
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
    echo "  View logs:           docker logs -f lora-chatbot"
    echo "  Stop dev container:  docker stop lora-chatbot"
    echo "  Stop all:            $COMPOSE_CMD down"
    echo "  Pull ollama models:  ./scripts/pull-ollama-models.sh [--all|model_name]"
    echo ""

else
    echo -e "\n${RED}======================================"
    echo "✗ Failed to start development mode!"
    echo "======================================${NC}"
    echo "Check logs with: docker logs lora-chatbot"
    exit 1
fi
