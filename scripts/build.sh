#!/bin/bash

set -e

echo "Building GraphRAG Assistant container images..."

# Build the main image directly
docker build -t lora-chatbot:latest -f Containerfile .

echo "✓ Build complete!"
echo ""
echo "Images built:"
docker images | grep lora- || true
