#!/bin/bash
# Rebuild Docker containers after code changes
# This script rebuilds and restarts containers to pick up code changes

set -e

echo "=========================================="
echo "Rebuilding Docker Containers"
echo "=========================================="

# Check if we're in development or production mode
if [ -f "docker-compose.dev.yml" ] && docker-compose ps | grep -q "investment_platform"; then
    echo "Detected development mode. Using docker-compose.dev.yml"
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
else
    echo "Using production mode"
    COMPOSE_FILES="-f docker-compose.yml"
fi

# Ask which services to rebuild
echo ""
echo "Which services would you like to rebuild?"
echo "1) All services"
echo "2) API only"
echo "3) Frontend only"
echo "4) Scheduler only"
echo "5) API + Scheduler"
read -p "Enter choice [1-5] (default: 1): " choice
choice=${choice:-1}

case $choice in
    1)
        echo "Rebuilding all services..."
        docker-compose $COMPOSE_FILES build --no-cache
        docker-compose $COMPOSE_FILES up -d
        ;;
    2)
        echo "Rebuilding API service..."
        docker-compose $COMPOSE_FILES build --no-cache api
        docker-compose $COMPOSE_FILES up -d api
        ;;
    3)
        echo "Rebuilding Frontend service..."
        docker-compose $COMPOSE_FILES build --no-cache frontend
        docker-compose $COMPOSE_FILES up -d frontend
        ;;
    4)
        echo "Rebuilding Scheduler service..."
        docker-compose $COMPOSE_FILES build --no-cache scheduler
        docker-compose $COMPOSE_FILES up -d scheduler
        ;;
    5)
        echo "Rebuilding API and Scheduler services..."
        docker-compose $COMPOSE_FILES build --no-cache api scheduler
        docker-compose $COMPOSE_FILES up -d api scheduler
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Rebuild complete!"
echo "=========================================="
echo ""
echo "Container status:"
docker-compose $COMPOSE_FILES ps

