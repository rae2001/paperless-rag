#!/usr/bin/env python3
"""
Create .env file with the correct settings.
"""

import os
import sys


def create_env_file():
    """Create .env file with proper settings."""
    
    env_content = """# Paperless-ngx Configuration
PAPERLESS_BASE_URL=http://192.168.1.77:8000
PAPERLESS_API_TOKEN=your_paperless_token_here

# OpenRouter Configuration  
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# Vector Database Configuration
QDRANT_URL=http://qdrant:6333

# Embedding Configuration
EMBEDDING_MODEL=BAAI/bge-m3

# RAG Configuration
RAG_TOP_K=6
CHUNK_TOKENS=800
CHUNK_OVERLAP=120
MAX_SNIPPETS_TOKENS=2500

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8088
ALLOWED_ORIGINS=http://localhost,http://192.168.1.77,http://localhost:3000

# Logging
LOG_LEVEL=INFO
"""
    
    if os.path.exists('.env'):
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return False
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Created .env file successfully!")
        print("\n⚠️  IMPORTANT: Edit .env file with your actual credentials:")
        print("   - PAPERLESS_API_TOKEN: Get from http://192.168.1.77:8000/admin/authtoken/tokenproxy/")
        print("   - OPENROUTER_API_KEY: Get from https://openrouter.ai/")
        print("\nAfter editing .env, run: python fix_container.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


if __name__ == "__main__":
    success = create_env_file()
    sys.exit(0 if success else 1)
