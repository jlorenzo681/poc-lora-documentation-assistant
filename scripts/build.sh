#!/bin/bash

set -e

echo "Building Lora Documentation Assistant container images..."

# Build the frontend image
echo "Building lora-frontend (target: frontend)..."
docker build -t lora-frontend:latest -f Containerfile --target frontend .

# Build the backend image
echo "Building lora-backend (target: backend)..."
docker build -t lora-backend:latest -f Containerfile --target backend .

# Build the worker image
echo "Building lora-worker (target: worker)..."
docker build -t lora-worker:latest -f Containerfile --target worker .

echo "✓ Build complete!"
echo ""
echo "Images built:"
docker images | grep lora- || true
