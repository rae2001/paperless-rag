#!/usr/bin/env python3
"""
Test script to diagnose the RAG system issues
"""

import requests
import json

API_BASE = "http://192.168.1.77:8088"

def test_system():
    """Test the entire RAG system step by step"""
    print("🔍 Testing RAG System Components")
    print("=" * 50)
    
    # 1. Test API health
    print("1. Testing API Health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API Health: {health.get('status', 'unknown')}")
            components = health.get('components', {})
            for comp, status in components.items():
                icon = "✅" if status == "healthy" else "❌"
                print(f"   {icon} {comp}: {status}")
        else:
            print(f"❌ API Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API Health check error: {e}")
        return
    
    # 2. Test statistics
    print("\n2. Testing System Statistics...")
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            docs = stats.get('paperless_documents', 'Unknown')
            vector_db = stats.get('vector_database', {})
            chunks = vector_db.get('points_count', 'Unknown')
            
            print(f"📄 Paperless Documents: {docs}")
            print(f"🔍 Vector Database Chunks: {chunks}")
            print(f"🤖 LLM Model: {stats.get('llm_model', 'Unknown')}")
            print(f"🔗 Embedding Model: {stats.get('embedding_model', 'Unknown')}")
            
            if chunks == 0 or chunks == 'Unknown':
                print("⚠️  WARNING: No chunks in vector database!")
                print("   You need to ingest documents first:")
                print(f"   curl -X POST {API_BASE}/ingest -H 'Content-Type: application/json' -d '{{}}'")
        else:
            print(f"❌ Stats check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats check error: {e}")
    
    # 3. Test document search
    print("\n3. Testing Document Search...")
    test_queries = [
        "what documents do i have",
        "test query",
        "contract information"
    ]
    
    for query in test_queries:
        print(f"\n   Testing query: '{query}'")
        try:
            response = requests.post(
                f"{API_BASE}/ask",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')[:100] + "..."
                citations = data.get('citations', [])
                
                print(f"   📝 Answer preview: {answer}")
                print(f"   📎 Citations found: {len(citations)}")
                
                if citations:
                    for i, cite in enumerate(citations[:2]):
                        score = cite.get('score', 0) * 100
                        title = cite.get('title', 'Unknown')
                        print(f"      {i+1}. {title} (Relevance: {score:.1f}%)")
                else:
                    print("   ⚠️  No citations found!")
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Query error: {e}")
    
    # 4. Test ingestion status
    print("\n4. Testing Document Ingestion...")
    try:
        response = requests.get(f"{API_BASE}/documents?limit=5", timeout=10)
        if response.status_code == 200:
            docs = response.json()
            print(f"📚 Sample documents available: {len(docs)}")
            for doc in docs[:3]:
                print(f"   - ID: {doc.get('id')}, Title: {doc.get('title', 'Unknown')}")
        else:
            print(f"❌ Document list failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Document list error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Diagnosis Complete!")
    print("\nIf you see 'No citations found' above, try:")
    print(f"1. Ingest documents: curl -X POST {API_BASE}/ingest -d '{{}}' -H 'Content-Type: application/json'")
    print("2. Check Paperless has documents available")
    print("3. Verify Qdrant vector database is working")

if __name__ == "__main__":
    test_system()
