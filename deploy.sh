#!/bin/bash

# Exit on any error
set -e

echo "Starting deployment setup..."

# Create Docker network if it doesn't exist
if ! docker network inspect tp >/dev/null 2>&1; then
    echo "Creating Docker network 'tp'..."
    docker network create tp
else
    echo "Network 'tp' already exists"
fi

# Build database image
echo "Building database image..."
docker build -t gova/tp-db -f Dockerfile.db .

# Build API image
echo "Building API image..."
docker build -t gova/tp-api -f Dockerfile.api .

# Stop existing containers if running
echo "Checking for existing containers..."
docker stop postgres api 2>/dev/null || true

# Start database container
echo "Starting database container..."
docker run --name postgres \
    --net tp \
    -p 5432:5432 \
    --rm \
    -d gova/tp-db

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Start API container
echo "Starting API container..."
docker run --name api \
    --net tp \
    -p 8000:8000 \
    --rm \
    -d gova/tp-api

echo "Deployment setup complete!"
echo "API is accessible at http://localhost:8000"
echo "Database is accessible at localhost:5432"
echo ""
echo "To check container status:"
echo "docker ps"
echo ""
echo "To view logs:"
echo "docker logs api"
echo "docker logs postgres"
