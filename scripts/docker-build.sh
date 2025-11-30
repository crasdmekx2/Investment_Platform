#!/bin/bash
# Build all Docker images

set -e

echo "Building API image..."
docker build -f Dockerfile.api -t investment-platform-api:latest .

echo "Building Frontend image..."
docker build -f frontend/Dockerfile -t investment-platform-frontend:latest ./frontend

echo "Build complete!"

