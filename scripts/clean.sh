#!/bin/bash
# Cleanup script for RAG Chatbot
# Removes containers (keeps images and volumes by default)
# Use flags: --images to remove images, --volumes to remove volumes, --all for everything

set -e

echo "======================================"
echo "LoRA RAG Documentation Assistant - Cleanup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop MLX Server if running
if [ -f "scripts/stop.sh" ]; then
    ./scripts/stop.sh >/dev/null 2>&1 || true
fi

# Parse flags
REMOVE_IMAGES=false
REMOVE_VOLUMES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --images)
            REMOVE_IMAGES=true
            shift
            ;;
        --volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        --all)
            REMOVE_IMAGES=true
            REMOVE_VOLUMES=true
            shift
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            echo "Usage: $0 [--images] [--volumes] [--all]"
            echo "  --images   Remove images too"
            echo "  --volumes  Remove volumes too (Ollama models)"
            echo "  --all      Remove everything (images + volumes)"
            exit 1
            ;;
    esac
done

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Stop and remove containers using compose if available
echo -e "\n${YELLOW}Stopping and removing containers...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose down 2>/dev/null || true
    echo -e "${GREEN}✓ Containers stopped via docker-compose${NC}"
elif docker compose version &> /dev/null; then
    docker compose down 2>/dev/null || true
    echo -e "${GREEN}✓ Containers stopped via docker compose${NC}"
else
    # Manual removal
    if docker ps -a | grep -q lora-chatbot; then
        docker stop lora-chatbot 2>/dev/null || true
        docker rm lora-chatbot 2>/dev/null || true
        echo -e "${GREEN}✓ lora-chatbot container removed${NC}"
    fi

    if docker ps -a | grep -q lora-backend; then
        docker stop lora-backend 2>/dev/null || true
        docker rm lora-backend 2>/dev/null || true
        echo -e "${GREEN}✓ lora-backend container removed${NC}"
    fi
    
    if docker ps -a | grep -q lora-worker; then
        docker stop lora-worker 2>/dev/null || true
        docker rm lora-worker 2>/dev/null || true
        echo -e "${GREEN}✓ lora-worker container removed${NC}"
    fi

    if docker ps -a | grep -q lora-redis; then
        docker stop lora-redis 2>/dev/null || true
        docker rm lora-redis 2>/dev/null || true
        echo -e "${GREEN}✓ lora-redis container removed${NC}"
    fi

    if docker ps -a --format "{{.Names}}" | grep -q "^buildx_buildkit_default$"; then
        docker stop buildx_buildkit_default >/dev/null 2>&1 || true
        docker rm buildx_buildkit_default >/dev/null 2>&1 || true
        echo -e "${GREEN}✓ buildx_buildkit_default container removed${NC}"
    fi
fi

# Remove images if flag set
if [ "$REMOVE_IMAGES" = true ]; then
    echo -e "\n${YELLOW}Removing images...${NC}"

    if docker image inspect lora-chatbot:latest >/dev/null 2>&1; then
        docker rmi lora-chatbot:latest 2>/dev/null || true
        echo -e "${GREEN}✓ lora-chatbot image removed${NC}"
    else
        echo -e "${YELLOW}⚠ lora-chatbot image not found${NC}"
    fi
else
    echo -e "\n${YELLOW}⚠ Images kept (use --images flag to remove)${NC}"
fi

# Remove volumes if flag set
if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "\n${YELLOW}Removing volumes...${NC}"

    for volume in poc-lora-documentation-assistant_lora-redis-data poc-lora-documentation-assistant_langfuse-db-data poc-lora-documentation-assistant_clickhouse-data poc-lora-documentation-assistant_clickhouse-logs; do
        if docker volume inspect $volume >/dev/null 2>&1; then
            docker volume rm $volume 2>/dev/null || true
            echo -e "${GREEN}✓ Volume $volume removed${NC}"
        else
            echo -e "${YELLOW}⚠ Volume $volume not found${NC}"
        fi
    done
else
    echo -e "\n${YELLOW}⚠ Volumes kept (use --volumes flag to remove)${NC}"
fi

# Remove networks if they exist and have no containers
echo -e "\n${YELLOW}Cleaning up networks...${NC}"
for network in lora-network poc-lora-documentation-assistant_lora-network; do
    if docker network inspect $network >/dev/null 2>&1; then
        # Check if network has any containers
        # Docker syntax for network inspect is lengthy, easier to just try removing
        docker network rm $network 2>/dev/null || true
        echo -e "${GREEN}✓ Network $network removed (if empty)${NC}"
    fi
done

# Cleanup MLX Server files
if [ -f ".mlx_server.pid" ]; then
    rm .mlx_server.pid
    echo -e "${GREEN}✓ MLX PID file removed${NC}"
fi
if [ -f ".mlx_server.log" ]; then
    rm .mlx_server.log
    echo -e "${GREEN}✓ MLX log file removed${NC}"
fi

# Summary
echo -e "\n${GREEN}======================================"
echo "✓ Cleanup complete!"
echo "======================================${NC}"
echo ""
echo "Remaining resources:"
echo ""
echo "Containers:"
docker ps -a | grep -E 'CONTAINER|rag-chatbot|ollama' || echo "  None"
echo ""
echo "Images:"
docker images | grep -E 'REPOSITORY|rag-chatbot|ollama' || echo "  None"
echo ""
echo "Volumes:"
docker volume ls | grep -E 'DRIVER|ollama-data' || echo "  None"
echo ""
