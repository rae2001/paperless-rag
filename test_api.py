#!/usr/bin/env python3
"""
Simple test script for the Paperless RAG API.
Run this after starting the services to verify everything works.
"""

import requests
import json
import time
import sys


def test_health():
    """Test the health endpoint."""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8088/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"   Status: {data['status']}")
        print(f"   Version: {data['version']}")
        
        for component, status in data['components'].items():
            status_emoji = "✅" if status == "healthy" else "❌"
            print(f"   {status_emoji} {component}: {status}")
        
        return data['status'] == 'healthy'
        
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False


def test_stats():
    """Test the stats endpoint."""
    print("\n📊 Testing stats endpoint...")
    try:
        response = requests.get("http://localhost:8088/stats", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"   Vector DB points: {data['vector_database'].get('points_count', 0)}")
        print(f"   Paperless documents: {data.get('paperless_documents', 'unknown')}")
        print(f"   Embedding model: {data.get('embedding_model', 'unknown')}")
        print(f"   LLM model: {data.get('llm_model', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Stats check failed: {e}")
        return False


def test_documents():
    """Test the documents endpoint."""
    print("\n📄 Testing documents endpoint...")
    try:
        response = requests.get("http://localhost:8088/documents?limit=5", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"   Found {len(data)} documents (showing first 5)")
        for doc in data[:3]:  # Show first 3
            print(f"   📄 {doc['id']}: {doc['title'][:50]}...")
        
        return len(data) > 0
        
    except Exception as e:
        print(f"   ❌ Documents check failed: {e}")
        return False


def test_ask_question():
    """Test asking a question."""
    print("\n🤔 Testing ask endpoint...")
    try:
        question = "What types of documents are available?"
        
        payload = {
            "query": question,
            "top_k": 3
        }
        
        print(f"   Question: {question}")
        print("   Searching for answer...")
        
        response = requests.post(
            "http://localhost:8088/ask",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"   Answer: {data['answer'][:200]}...")
        print(f"   Citations: {len(data['citations'])}")
        
        for i, citation in enumerate(data['citations'][:2], 1):
            print(f"   📖 [{i}] {citation['title']} (score: {citation['score']:.2f})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ask question failed: {e}")
        return False


def test_ingest_sample():
    """Test ingesting a specific document."""
    print("\n📥 Testing ingest endpoint...")
    try:
        # First get a document ID
        docs_response = requests.get("http://localhost:8088/documents?limit=1", timeout=10)
        docs_response.raise_for_status()
        docs = docs_response.json()
        
        if not docs:
            print("   ⚠️  No documents found to test ingestion")
            return True
        
        doc_id = docs[0]['id']
        print(f"   Testing ingestion of document {doc_id}")
        
        payload = {
            "doc_id": doc_id,
            "force_reindex": True
        }
        
        response = requests.post(
            "http://localhost:8088/ingest",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"   Result: {data['message']}")
        print(f"   Chunks created: {data['chunks_created']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ingest test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Paperless RAG API Test Suite")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health),
        ("Statistics", test_stats),
        ("Documents List", test_documents),
        ("Question Answering", test_ask_question),
        ("Document Ingestion", test_ingest_sample),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            time.sleep(1)  # Brief pause between tests
            
        except KeyboardInterrupt:
            print("\n⏸️  Tests interrupted by user")
            break
        except Exception as e:
            print(f"\n💥 Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your Paperless RAG system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs and configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
