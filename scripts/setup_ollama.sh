#!/bin/bash

# Configuration
MODEL_NAME="llama3.2:3b"
MODEL_TO_REMOVE="mistral"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 Checking Ollama status...${NC}"

# Check if Ollama is running (in container)
if ! docker ps | grep -q ollama; then
    echo -e "${RED}❌ Ollama container is not running.${NC}"
    echo "Please start it with: ./scripts/deploy.sh"
    exit 1
fi

echo -e "${GREEN}✓ Ollama container is running.${NC}"

# Pull the model
echo -e "${YELLOW}⬇️  Pulling model '${MODEL_NAME}'...${NC}"
docker exec ollama ollama pull ${MODEL_NAME}

# Pull embedding models
echo -e "${YELLOW}⬇️  Pulling embedding model 'nomic-embed-text'...${NC}"
docker exec ollama ollama pull nomic-embed-text

echo -e "${YELLOW}⬇️  Pulling embedding model 'bge-m3'...${NC}"
docker exec ollama ollama pull bge-m3

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Model '${MODEL_NAME}' is ready!${NC}"
else
    echo -e "${RED}❌ Failed to pull model '${MODEL_NAME}'.${NC}"
    exit 1
fi

# Remove the old model if it exists
echo -e "${YELLOW}🗑️  Checking for model '${MODEL_TO_REMOVE}' to remove...${NC}"
if docker exec ollama ollama list | grep -q "${MODEL_TO_REMOVE}"; then
    docker exec ollama ollama rm ${MODEL_TO_REMOVE}
    echo -e "${GREEN}✓ Model '${MODEL_TO_REMOVE}' removed.${NC}"
else
    echo -e "${YELLOW}ℹ️  Model '${MODEL_TO_REMOVE}' not found, skipping removal.${NC}"
fi

# List models to confirm
echo -e "\n${YELLOW}📋 Available models:${NC}"
docker exec ollama ollama list
