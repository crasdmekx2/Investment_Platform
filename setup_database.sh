#!/bin/bash
# Bash script to setup the PostgreSQL database with TimescaleDB

echo "Setting up PostgreSQL database with TimescaleDB..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ Docker is not running. Please start Docker."
    exit 1
fi
echo "✓ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "✗ docker-compose is not available. Please install docker-compose."
    exit 1
fi
echo "✓ docker-compose is available"

# Stop any existing containers
echo ""
echo "Stopping any existing containers..."
docker-compose down

# Start the database container
echo ""
echo "Starting database container..."
docker-compose up -d

# Wait for database to be ready
echo ""
echo "Waiting for database to be ready..."
max_attempts=30
attempt=0
ready=false

while [ $attempt -lt $max_attempts ]; do
    health=$(docker inspect --format='{{.State.Health.Status}}' investment_platform_db 2>/dev/null)
    if [ "$health" = "healthy" ]; then
        ready=true
        break
    fi
    sleep 2
    echo -n "."
    attempt=$((attempt + 1))
done

echo ""

if [ "$ready" = true ]; then
    echo "✓ Database is ready!"
else
    echo "⚠ Database container started but health check timed out. It may still be initializing."
    echo "  You can check status with: docker-compose ps"
fi

# Display connection information
echo ""
echo "Database connection information:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: investment_platform"
echo "  User: postgres"
echo "  Password: postgres"

echo ""
echo "To test connectivity, run:"
echo "  python tests/test_connection.py"

echo ""
echo "To view logs:"
echo "  docker-compose logs -f"

echo ""
echo "To stop the database:"
echo "  docker-compose down"

