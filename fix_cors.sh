#!/bin/bash

echo "Fixing CORS issues for Paperless RAG"
echo "===================================="

# Step 1: Stop the current containers
echo "1. Stopping current containers..."
docker compose down

# Step 2: Rebuild with new CORS settings
echo ""
echo "2. Rebuilding API with updated CORS configuration..."
docker compose build rag-api

# Step 3: Start containers
echo ""
echo "3. Starting containers..."
docker compose up -d

# Step 4: Wait for API to be ready
echo ""
echo "4. Waiting for API to be ready..."
sleep 5

# Step 5: Test the API
echo ""
echo "5. Testing API connection..."
curl -I http://localhost:8088/health

echo ""
echo "===================================="
echo "CORS fix complete!"
echo ""
echo "Now you can:"
echo "1. Access the UI at: http://192.168.1.77:8080"
echo "2. The API should be available at: http://192.168.1.77:8088"
echo ""
echo "If you still see issues, run: python3 debug_cors.py"
