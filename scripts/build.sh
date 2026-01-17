#!/bin/bash
# Build RAG Chatbot container image

set -e

echo "Building RAG Chatbot container image..."

docker build --no-cache -t rag-chatbot:latest -f Containerfile .

echo "✓ Build complete!"
echo ""
echo "Image details:"
docker images | grep rag-chatbot || true
