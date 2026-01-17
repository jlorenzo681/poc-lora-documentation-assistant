#!/bin/bash
# Cleanup script for RAG Chatbot
# Removes containers (keeps images and volumes by default)
# Use flags: --images to remove images, --volumes to remove volumes, --all for everything

set -e

echo "======================================"
echo "RAG Chatbot - Cleanup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
    docker-compose -p rag-fresh down 2>/dev/null || true
    echo -e "${GREEN}✓ Containers stopped via docker-compose${NC}"
elif docker compose version &> /dev/null; then
    docker compose -p rag-fresh down 2>/dev/null || true
    echo -e "${GREEN}✓ Containers stopped via docker compose${NC}"
else
    # Manual removal
    if docker ps -a | grep -q rag-chatbot; then
        docker stop rag-chatbot 2>/dev/null || true
        docker rm rag-chatbot 2>/dev/null || true
        echo -e "${GREEN}✓ rag-chatbot container removed${NC}"
    fi

    if docker ps -a | grep -q ollama; then
        docker stop ollama 2>/dev/null || true
        docker rm ollama 2>/dev/null || true
        echo -e "${GREEN}✓ ollama container removed${NC}"
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

    if docker image inspect rag-chatbot:latest >/dev/null 2>&1; then
        docker rmi rag-chatbot:latest 2>/dev/null || true
        echo -e "${GREEN}✓ rag-chatbot image removed${NC}"
    else
        echo -e "${YELLOW}⚠ rag-chatbot image not found${NC}"
    fi

    if docker image inspect docker.io/ollama/ollama:latest >/dev/null 2>&1; then
        docker rmi docker.io/ollama/ollama:latest 2>/dev/null || true
        echo -e "${GREEN}✓ Ollama image removed${NC}"
    else
        echo -e "${YELLOW}⚠ Ollama image not found${NC}"
    fi
else
    echo -e "\n${YELLOW}⚠ Images kept (use --images flag to remove)${NC}"
fi

# Remove volumes if flag set
if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "\n${YELLOW}Removing volumes...${NC}"

    if docker volume inspect ollama-data >/dev/null 2>&1; then
        docker volume rm ollama-data 2>/dev/null || true
        echo -e "${GREEN}✓ Ollama data volume removed${NC}"
    else
        echo -e "${YELLOW}⚠ Ollama data volume not found${NC}"
    fi

    if docker volume inspect poc-rag-chatbot-wiki_hf-cache >/dev/null 2>&1; then
        docker volume rm poc-rag-chatbot-wiki_hf-cache 2>/dev/null || true
        echo -e "${GREEN}✓ HuggingFace cache volume removed${NC}"
    else
        echo -e "${YELLOW}⚠ HuggingFace cache volume not found${NC}"
    fi
else
    echo -e "\n${YELLOW}⚠ Volumes kept (use --volumes flag to remove Ollama models)${NC}"
fi

# Remove networks if they exist and have no containers
echo -e "\n${YELLOW}Cleaning up networks...${NC}"
for network in rag-network poc-rag-chatbot-wiki_rag-network; do
    if docker network inspect $network >/dev/null 2>&1; then
        # Check if network has any containers
        # Docker syntax for network inspect is lengthy, easier to just try removing
        docker network rm $network 2>/dev/null || true
        echo -e "${GREEN}✓ Network $network removed (if empty)${NC}"
    fi
done

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
