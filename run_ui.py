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
    print("🏢 **Professional Gradio UI** (Recommended)")
    print("   ✅ Business-ready interface")
    print("   ✅ Clean, corporate design")
    print("   ✅ Excellent integration")
    print("   ✅ Easy deployment")
    print("")
    print("🔗 **System Information**")
    print("   📍 API: http://192.168.1.77:8088")
    print("   📍 Paperless: http://192.168.1.77:8000")
    print("")
    print("=" * 35)
    
    while True:
        print("\nChoose an option:")
        print("1️⃣  Start Professional Gradio UI (Recommended)")
        print("2️⃣  [Legacy - Removed]")
        print("3️⃣  Test API Connection")
        print("4️⃣  View API Documentation")
        print("5️⃣  Exit")
        print("")
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            print("\n🚀 Starting Professional Gradio UI...")
            try:
                subprocess.run([sys.executable, "start_gradio.py"], check=True)
            except KeyboardInterrupt:
                print("\n👋 Gradio UI stopped")
            except Exception as e:
                print(f"❌ Error starting Gradio: {e}")
            continue
            
        elif choice == "2":
            print("\n❌ Streamlit UI has been removed")
            print("💡 Use the Professional Gradio UI instead (Option 1)")
            continue
            
        elif choice == "3":
            print("\n🔍 Testing API connection...")
            try:
                subprocess.run([sys.executable, "test_connections.py"], check=True)
            except Exception as e:
                print(f"❌ Error running connection test: {e}")
            continue
            
        elif choice == "4":
            print("\n📖 API Documentation:")
            print("   🌐 Health Check: http://192.168.1.77:8088/health")
            print("   📊 Statistics: http://192.168.1.77:8088/stats")
            print("   📚 API Docs: http://192.168.1.77:8088/docs")
            print("   ❓ Ask Question: POST http://192.168.1.77:8088/ask")
            print("   📥 Ingest Docs: POST http://192.168.1.77:8088/ingest")
            continue
            
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()
