#!/bin/bash
# Force complete rebuild of Docker containers

echo "========================================"
echo "FORCING COMPLETE DOCKER REBUILD"
echo "========================================"
echo ""

cd ~/DotStarkRag365/backend

echo "1. Stopping all containers..."
sudo docker-compose down

echo ""
echo "2. Removing old images..."
sudo docker-compose rm -f

echo ""
echo "3. Building with no cache..."
sudo docker-compose build --no-cache

echo ""
echo "4. Starting containers..."
sudo docker-compose up -d

echo ""
echo "5. Waiting for containers to be ready..."
sleep 10

echo ""
echo "6. Checking if backend is running..."
sudo docker ps | grep fastapi-backend

echo ""
echo "========================================"
echo "✅ REBUILD COMPLETE"
echo "========================================"
echo ""
echo "Now test with:"
echo "  sudo docker exec -it fastapi-backend python test_ant24_crawl.py"
echo ""
