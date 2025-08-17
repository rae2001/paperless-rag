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
check_command python3
# Check for modern docker compose or legacy docker-compose
if command -v "docker" &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v "docker-compose" &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ Error: Neither 'docker compose' nor 'docker-compose' found"
    exit 1
fi
echo "✅ Docker and Docker Compose found ($DOCKER_COMPOSE)"
echo "✅ Python3 found"

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

# Create OpenWebUI config directory
echo "📁 Creating OpenWebUI config directory..."
mkdir -p openwebui-config
if [ ! -f openwebui-config/config.yaml ]; then
    echo "📝 OpenWebUI config directory created"
else
    echo "✅ OpenWebUI config already exists"
fi

# Pull images
echo "🐳 Pulling Docker images..."
$DOCKER_COMPOSE pull

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env with your API tokens:"
echo "   nano .env"
echo ""
echo "2. Start the core services:"
echo "   $DOCKER_COMPOSE up -d"
echo ""
echo "3. Check system health:"
echo "   curl http://localhost:8088/health"
echo ""
echo "4. Ingest your documents:"
echo "   curl -X POST http://localhost:8088/ingest -H 'Content-Type: application/json' -d '{}'"
echo ""
echo "🌟 Recommended: Setup Enhanced Document Assistant UI"
echo "   python3 setup_openwebui.py"
echo ""
echo "   This provides:"
echo "   ✅ Professional ChatGPT-like interface at http://localhost:3001"
echo "   ✅ Branded as 'Paperless Document Assistant'"
echo "   ✅ Document-focused features and suggestions"
echo "   ✅ Multi-user support with conversation history"
echo "   ✅ Enhanced RAG integration optimized for your documents"
echo ""
echo "🔧 Alternative: Use API directly"
echo "   curl -X POST http://localhost:8088/ask -H 'Content-Type: application/json' -d '{\"query\": \"What documents do I have?\"}'"
echo ""
echo "🧪 Test everything:"
echo "   python test_api.py"
echo ""
echo "📖 For detailed documentation, see README.md"

