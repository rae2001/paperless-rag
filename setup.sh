#!/bin/bash

# Paperless RAG Setup Script
set -e

echo "🚀 Paperless RAG Setup"
echo "====================="

# Check for required commands
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ Error: $1 is not installed or not in PATH"
        exit 1
    fi
}

echo "🔍 Checking prerequisites..."
check_command docker
check_command docker-compose
echo "✅ Docker and Docker Compose found"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: You need to edit .env with your actual credentials:"
    echo "   - PAPERLESS_API_TOKEN: Get from your paperless-ngx settings"
    echo "   - OPENROUTER_API_KEY: Get from https://openrouter.ai/"
    echo ""
    echo "Example paperless token location:"
    echo "   http://192.168.1.77:8000/admin/authtoken/tokenproxy/"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs
echo "✅ Logs directory created"

# Pull images
echo "🐳 Pulling Docker images..."
docker-compose pull

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API tokens:"
echo "   nano .env"
echo ""
echo "2. Start the services:"
echo "   docker-compose up -d"
echo ""
echo "3. Check system health:"
echo "   curl http://localhost:8088/health"
echo ""
echo "4. Run the test suite:"
echo "   python test_api.py"
echo ""
echo "5. Ingest your documents:"
echo "   curl -X POST http://localhost:8088/ingest -H 'Content-Type: application/json' -d '{}'"
echo ""
echo "6. Ask your first question:"
echo "   curl -X POST http://localhost:8088/ask -H 'Content-Type: application/json' -d '{\"query\": \"What documents do I have?\"}'"
echo ""
echo "📖 For more information, see README.md"
