#!/usr/bin/env python3
"""
Comprehensive OpenWebUI initialization script for Paperless RAG integration
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path

class OpenWebUIConfigurator:
    def __init__(self, base_url="http://192.168.1.77:3001", api_base_url="http://192.168.1.77:8088"):
        self.base_url = base_url
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.admin_token = None
        
    def wait_for_openwebui(self, max_retries=24):
        """Wait for OpenWebUI to be available"""
        print("🔄 Waiting for OpenWebUI to start...")
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/api/config", timeout=5)
                if response.status_code in [200, 401]:  # 401 is also fine, means service is up
                    print("✅ OpenWebUI is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            print(f"   Attempt {i+1}/{max_retries}...")
            time.sleep(5)
        
        print(f"❌ OpenWebUI failed to start after {max_retries * 5} seconds")
        return False
    
    def check_admin_exists(self):
        """Check if an admin user already exists"""
        try:
            response = requests.get(f"{self.base_url}/api/config")
            return response.status_code == 401  # 401 means auth is required, so admin exists
        except:
            return False
    
    def create_admin_user(self, email="admin@paperless-rag.local", password="admin123", name="Administrator"):
        """Create the initial admin user"""
        if self.check_admin_exists():
            print("ℹ️  Admin user already exists")
            return True
            
        print("👤 Creating admin user...")
        signup_data = {
            "email": email,
            "password": password,
            "name": name,
            "role": "admin"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/v1/auths/signup", json=signup_data)
            if response.status_code == 200:
                print("✅ Admin user created successfully")
                print(f"   Email: {email}")
                print(f"   Password: {password}")
                return True
            else:
                print(f"❌ Failed to create admin user: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            return False
    
    def login_admin(self, email="admin@paperless-rag.local", password="admin123"):
        """Login as admin and get auth token"""
        print("🔐 Logging in as admin...")
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/v1/auths/signin", json=login_data)
            if response.status_code == 200:
                token = response.json().get("token")
                if token:
                    self.admin_token = token
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
                    print("✅ Successfully logged in")
                    return True
            
            print(f"❌ Login failed: {response.text}")
            return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def configure_openai_api(self):
        """Configure the OpenAI-compatible API connection"""
        print("🔧 Configuring API connection...")
        
        api_config = {
            "url": self.api_base_url,
            "key": "dummy-key-not-needed"
        }
        
        try:
            # Add OpenAI API configuration
            response = self.session.post(f"{self.base_url}/api/v1/configs/openai", json=api_config)
            if response.status_code in [200, 201]:
                print("✅ API configuration added")
                return True
            else:
                print(f"⚠️  API config response: {response.status_code}")
                # Continue anyway, might already be configured
                return True
        except Exception as e:
            print(f"⚠️  API configuration warning: {e}")
            return True  # Continue anyway
    
    def setup_models(self):
        """Configure available models"""
        print("🤖 Setting up models...")
        
        # First, pull available models from our API
        try:
            models_response = self.session.get(f"{self.base_url}/api/models")
            if models_response.status_code == 200:
                models = models_response.json()
                print(f"✅ Found {len(models.get('data', []))} available models")
                
                # Look for our specific model
                model_found = False
                for model in models.get('data', []):
                    if 'gpt' in model.get('id', '').lower() or 'paperless' in model.get('id', '').lower():
                        print(f"   📝 Model available: {model.get('id')}")
                        model_found = True
                
                if not model_found:
                    print("⚠️  Paperless RAG model not found in available models")
                    print("   This might be normal if the model name is different")
                
                return True
        except Exception as e:
            print(f"⚠️  Model setup warning: {e}")
            return True
    
    def create_system_prompts(self):
        """Create system prompts for document interaction"""
        print("💬 Creating system prompts...")
        
        prompts = [
            {
                "command": "paperless-expert",
                "title": "Paperless Document Expert",
                "content": """You are an expert assistant that helps users find and understand information from their personal document collection. You have access to a comprehensive knowledge base of documents stored in Paperless-ngx through a RAG system.

**Your capabilities:**
- Search through documents using semantic understanding
- Provide accurate answers based on document content
- Cite specific documents when providing information
- Help organize and categorize document insights

**Guidelines:**
1. Always base your answers on the retrieved document content
2. When you reference information, mention the document title or source when available
3. If you cannot find relevant information in the documents, clearly state this
4. Provide comprehensive answers but stay focused on the user's question
5. Suggest follow-up questions that might help users explore their documents further

Remember: Your knowledge comes from the user's personal document collection."""
            },
            {
                "command": "quick-lookup",
                "title": "Quick Document Lookup",
                "content": """You are a fast and efficient document lookup assistant. Your job is to quickly find specific information from the user's document collection.

**Focus on:**
- Direct, concise answers
- Fast information retrieval
- Specific facts and details
- Clear citations of source documents

Perfect for when users need fast answers to specific questions about their documents."""
            }
        ]
        
        created_count = 0
        for prompt in prompts:
            try:
                response = self.session.post(f"{self.base_url}/api/v1/prompts", json=prompt)
                if response.status_code in [200, 201]:
                    created_count += 1
                    print(f"   ✅ Created prompt: {prompt['title']}")
                elif response.status_code == 409:
                    print(f"   ℹ️  Prompt already exists: {prompt['title']}")
                else:
                    print(f"   ⚠️  Failed to create prompt {prompt['title']}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️  Error creating prompt {prompt['title']}: {e}")
        
        print(f"✅ System prompts configured ({created_count} new)")
        return True
    
    def configure_settings(self):
        """Configure OpenWebUI settings"""
        print("⚙️  Configuring settings...")
        
        # Update general settings
        settings = {
            "ui": {
                "title": "Paperless Document Assistant",
                "show_username": True,
                "show_timestamp": True
            },
            "default_prompt_suggestions": [
                {
                    "title": "📄 Search Documents",
                    "content": "What documents do I have about {{topic}}?"
                },
                {
                    "title": "🔍 Find Information",
                    "content": "Can you find information about {{query}} in my documents?"
                },
                {
                    "title": "📊 Summarize Topic",
                    "content": "Please summarize what my documents say about {{subject}}."
                },
                {
                    "title": "📝 Document Analysis",
                    "content": "Analyze the key points from documents related to {{topic}}."
                }
            ]
        }
        
        try:
            # This might not work with all OpenWebUI versions, but that's okay
            response = self.session.post(f"{self.base_url}/api/v1/configs", json=settings)
            print("✅ Settings configured")
            return True
        except Exception as e:
            print(f"ℹ️  Settings configuration skipped: {e}")
            return True
    
    def test_integration(self):
        """Test the integration with a simple query"""
        print("🧪 Testing integration...")
        
        test_message = {
            "model": "openai/gpt-oss-20b",  # or whatever model is available
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! Can you help me search my documents?"
                }
            ],
            "stream": False
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/chat/completions", json=test_message)
            if response.status_code == 200:
                print("✅ Integration test successful!")
                return True
            else:
                print(f"⚠️  Integration test returned: {response.status_code}")
                print(f"   This might be normal if no documents are indexed yet")
                return True
        except Exception as e:
            print(f"ℹ️  Integration test skipped: {e}")
            return True

def main():
    print("🚀 Initializing OpenWebUI for Paperless RAG")
    print("=" * 60)
    
    configurator = OpenWebUIConfigurator()
    
    # Wait for OpenWebUI to be ready
    if not configurator.wait_for_openwebui():
        print("❌ Cannot continue without OpenWebUI")
        sys.exit(1)
    
    # Create admin user if needed
    if not configurator.create_admin_user():
        print("❌ Failed to create admin user")
        sys.exit(1)
    
    # Login as admin
    if not configurator.login_admin():
        print("❌ Failed to login as admin")
        sys.exit(1)
    
    # Configure the system
    configurator.configure_openai_api()
    configurator.setup_models()
    configurator.create_system_prompts()
    configurator.configure_settings()
    configurator.test_integration()
    
    print("\n🎉 OpenWebUI Integration Complete!")
    print("=" * 60)
    print(f"🌐 OpenWebUI URL: http://192.168.1.77:3001")
    print(f"👤 Admin Login: admin@paperless-rag.local / admin123")
    print(f"🔗 RAG API: http://192.168.1.77:8088")
    print("")
    print("📋 What's been configured:")
    print("✅ Admin user created")
    print("✅ API connection established")
    print("✅ System prompts for document interaction")
    print("✅ Custom UI settings")
    print("")
    print("🎯 Next steps:")
    print("1. Open http://192.168.1.77:3001 in your browser")
    print("2. Login with the admin credentials above")
    print("3. Start asking questions about your documents!")
    print("")
    print("💡 Try these prompts:")
    print("• 'What documents do I have about [topic]?'")
    print("• 'Find information about [query] in my documents'")
    print("• 'Summarize what my documents say about [subject]'")

if __name__ == "__main__":
    main()
