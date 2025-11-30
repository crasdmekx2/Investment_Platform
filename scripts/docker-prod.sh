#!/bin/bash
# Start production environment

set -e

echo "Starting production environment..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

echo "Services started. Frontend: http://localhost:3000, API: http://localhost:8000"

