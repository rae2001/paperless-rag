#!/bin/bash

echo "Fixing CORS issues on Ubuntu Server"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found. Please run this from the project root."
    exit 1
fi

# Step 1: Stop the current containers
echo "1. Stopping current containers..."
sudo docker compose down

# Step 2: Rebuild with new CORS settings
echo ""
echo "2. Rebuilding API with updated CORS configuration..."
sudo docker compose build rag-api --no-cache

# Step 3: Start containers
echo ""
echo "3. Starting containers..."
sudo docker compose up -d

# Step 4: Wait for API to be ready
echo ""
echo "4. Waiting for API to be ready..."
sleep 10

# Step 5: Test the API and CORS headers
echo ""
echo "5. Testing API connection and CORS headers..."
echo "Health check:"
curl -s http://localhost:8088/health | head -5

echo ""
echo "CORS headers test:"
curl -I http://localhost:8088/health 2>/dev/null | grep -i "access-control"

echo ""
echo "OPTIONS test:"
curl -X OPTIONS -I http://localhost:8088/ask 2>/dev/null | head -10

echo ""
echo "===================================="
echo "CORS fix complete!"
echo ""
echo "The API should now be accessible from your Windows PC at:"
echo "http://192.168.1.77:8088"
echo ""
echo "Access the UI from your Windows PC at:"
echo "http://192.168.1.77:8080"
