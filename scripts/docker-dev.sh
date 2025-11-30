#!/bin/bash
# Start development environment

set -e

echo "Starting development environment..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

