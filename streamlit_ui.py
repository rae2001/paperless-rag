#!/usr/bin/env python3
"""
Streamlit Chat UI for Paperless RAG Q&A System
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configure Streamlit page
st.set_page_config(
    page_title="📚 Paperless RAG Q&A",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE = "http://192.168.1.77:8088"

def check_api_health():
    """Check if API is healthy"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"API returned status {response.status_code}"
    except Exception as e:
        return False, str(e)

def get_stats():
    """Get system statistics"""
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def ask_question(query):
    """Ask a question to the RAG system"""
    try:
        response = requests.post(
            f"{API_BASE}/ask",
            json={"query": query},
            timeout=30
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, str(e)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_healthy" not in st.session_state:
    st.session_state.api_healthy = False

# Sidebar with system info
with st.sidebar:
    st.header("🔧 System Status")
    
    # API Health Check
    healthy, health_data = check_api_health()
    st.session_state.api_healthy = healthy
    
    if healthy:
        st.success("✅ API Connected")
        
        # Show component status
        if isinstance(health_data, dict) and "components" in health_data:
            components = health_data["components"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Qdrant", "✅" if components.get("qdrant") == "healthy" else "❌")
                st.metric("LLM", "✅" if components.get("llm") == "healthy" else "❌")
            
            with col2:
                st.metric("Paperless", "✅" if components.get("paperless") == "healthy" else "❌")
                st.metric("Embeddings", "✅" if components.get("embedding_model") == "healthy" else "❌")
    else:
        st.error(f"❌ API Error: {health_data}")
    
    st.divider()
    
    # System Stats
    st.header("📊 Statistics")
    stats = get_stats()
    
    if stats:
        col1, col2 = st.columns(2)
        with col1:
            docs_count = stats.get("paperless_documents", "Unknown")
            st.metric("Documents", docs_count)
        
        with col2:
            vector_stats = stats.get("vector_database", {})
            chunks_count = vector_stats.get("points_count", "Unknown")
            st.metric("Text Chunks", chunks_count)
        
        # Model info
        st.info(f"🤖 **Model**: {stats.get('llm_model', 'Unknown')}")
        st.info(f"🔗 **Embeddings**: {stats.get('embedding_model', 'Unknown')}")
    else:
        st.warning("Unable to load stats")
    
    st.divider()
    
    # Quick Actions
    st.header("💡 Quick Questions")
    quick_questions = [
        "What documents do I have?",
        "What topics are covered in my documents?",
        "Show me documents about contracts",
        "What welding procedures do I have?",
        "What quality requirements are mentioned?"
    ]
    
    for question in quick_questions:
        if st.button(question, key=f"quick_{hash(question)}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": question})
            st.rerun()

# Main chat interface
st.title("📚 Paperless RAG Q&A")
st.caption("Ask questions about your documents using AI-powered search")

# Check API status before allowing chat
if not st.session_state.api_healthy:
    st.error("🚫 **API is not available**. Please check your connection and try again.")
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show citations if available
        if message["role"] == "assistant" and "citations" in message:
            citations = message["citations"]
            if citations:
                st.markdown("---")
                st.markdown("**📎 Sources:**")
                
                for i, citation in enumerate(citations, 1):
                    with st.expander(f"📄 {citation.get('title', 'Unknown Document')}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            if citation.get("page"):
                                st.markdown(f"**Page:** {citation['page']}")
                            
                            if citation.get("snippet"):
                                st.markdown(f"**Excerpt:** {citation['snippet'][:200]}...")
                        
                        with col2:
                            if citation.get("score"):
                                score_percent = citation['score'] * 100
                                st.metric("Relevance", f"{score_percent:.1f}%")
                            
                            if citation.get("url"):
                                st.link_button("View in Paperless", citation["url"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching documents and generating answer..."):
            success, result = ask_question(prompt)
            
            if success:
                # Display answer
                answer = result.get("answer", "No answer received")
                st.markdown(answer)
                
                # Store message with citations
                message_data = {
                    "role": "assistant", 
                    "content": answer,
                    "citations": result.get("citations", [])
                }
                st.session_state.messages.append(message_data)
                
                # Show citations
                citations = result.get("citations", [])
                if citations:
                    st.markdown("---")
                    st.markdown("**📎 Sources:**")
                    
                    for i, citation in enumerate(citations, 1):
                        with st.expander(f"📄 {citation.get('title', 'Unknown Document')}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                if citation.get("page"):
                                    st.markdown(f"**Page:** {citation['page']}")
                                
                                if citation.get("snippet"):
                                    st.markdown(f"**Excerpt:** {citation['snippet'][:200]}...")
                            
                            with col2:
                                if citation.get("score"):
                                    score_percent = citation['score'] * 100
                                    st.metric("Relevance", f"{score_percent:.1f}%")
                                
                                if citation.get("url"):
                                    st.link_button("View in Paperless", citation["url"])
                
                # Show model used
                model_used = result.get("model_used", "Unknown")
                st.caption(f"Generated using: {model_used}")
                
            else:
                error_msg = f"❌ **Error**: {result}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("*Powered by Paperless-ngx, Qdrant, and OpenRouter*")

# Auto-refresh stats every 30 seconds (if enabled)
if st.sidebar.checkbox("Auto-refresh stats", value=False):
    time.sleep(30)
    st.rerun()
