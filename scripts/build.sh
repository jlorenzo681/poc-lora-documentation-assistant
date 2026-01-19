#!/bin/bash

set -e

echo "Building GraphRAG Assistant container images..."

# Check for compose tool
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: No compose tool found"
    exit 1
fi

echo "Building containers for all services..."

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build all services defined in docker-compose.yml
$COMPOSE_CMD build --parallel

echo "✓ Build complete!"
echo ""
echo "Images built:"
docker images | grep lora- || true
