#!/usr/bin/env python3
"""
Main launcher for Paperless RAG UI
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("🚀 Paperless RAG Q&A System")
    print("=" * 35)
    print("")
    print("📱 **New Streamlit UI** (Recommended)")
    print("   ✅ No CORS issues")
    print("   ✅ Better chat interface")
    print("   ✅ Real-time monitoring")
    print("   ✅ Professional design")
    print("")
    print("🔗 **Direct API Access**")
    print("   📍 API: http://192.168.1.77:8088")
    print("   📍 Paperless: http://192.168.1.77:8000")
    print("")
    print("=" * 35)
    
    while True:
        print("\nChoose an option:")
        print("1️⃣  Start Streamlit UI (Recommended)")
        print("2️⃣  Test API Connection")
        print("3️⃣  View API Documentation")
        print("4️⃣  Exit")
        print("")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 Starting Streamlit UI...")
            try:
                subprocess.run([sys.executable, "start_streamlit.py"], check=True)
            except KeyboardInterrupt:
                print("\n👋 Streamlit UI stopped")
            except Exception as e:
                print(f"❌ Error starting Streamlit: {e}")
            continue
            
        elif choice == "2":
            print("\n🔍 Testing API connection...")
            try:
                subprocess.run([sys.executable, "test_connections.py"], check=True)
            except Exception as e:
                print(f"❌ Error running connection test: {e}")
            continue
            
        elif choice == "3":
            print("\n📖 API Documentation:")
            print("   🌐 Health Check: http://192.168.1.77:8088/health")
            print("   📊 Statistics: http://192.168.1.77:8088/stats")
            print("   📚 API Docs: http://192.168.1.77:8088/docs")
            print("   ❓ Ask Question: POST http://192.168.1.77:8088/ask")
            print("   📥 Ingest Docs: POST http://192.168.1.77:8088/ingest")
            continue
            
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
