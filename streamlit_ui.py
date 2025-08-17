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
    page_title="Paperless Document Assistant",
    page_icon="📄",
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
    st.header("System Status")
    
    # API Health Check
    healthy, health_data = check_api_health()
    st.session_state.api_healthy = healthy
    
    if healthy:
        st.success("API Connected")
        
        # Show component status
        if isinstance(health_data, dict) and "components" in health_data:
            components = health_data["components"]
            
            status_items = []
            for component, status in components.items():
                icon = "✓" if status == "healthy" else "✗"
                status_items.append(f"{icon} {component.title()}")
            
            st.text("\n".join(status_items))
    else:
        st.error(f"API Error: {health_data}")
    
    st.divider()
    
    # System Stats
    st.header("Statistics")
    stats = get_stats()
    
    if stats:
        docs_count = stats.get("paperless_documents", "Unknown")
        vector_stats = stats.get("vector_database", {})
        chunks_count = vector_stats.get("points_count", "Unknown")
        
        st.metric("Documents", docs_count)
        st.metric("Text Chunks", chunks_count)
        
        st.caption(f"Model: {stats.get('llm_model', 'Unknown')}")
    else:
        st.warning("Unable to load stats")
    
    st.divider()
    
    # Quick Actions
    st.header("Quick Actions")
    
    # Common queries
    quick_questions = [
        "What documents do I have?",
        "Summarize my contracts",
        "Show recent reports",
        "List project requirements",
        "Find safety protocols"
    ]
    
    for question in quick_questions:
        if st.button(question, key=f"quick_{hash(question)}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": question})
            st.rerun()
    
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.title("Document Assistant")
st.caption("AI-powered assistant with access to your document knowledge base")

# Check API status before allowing chat
if not st.session_state.api_healthy:
    st.error("API is not available. Please check your connection and try again.")
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
if prompt := st.chat_input("Ask questions about your documents or general topics..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        # Show different spinner messages based on query type
        spinner_text = "Processing..." if len(prompt.split()) <= 3 else "Searching documents and generating response..."
        
        with st.spinner(spinner_text):
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
                
                # Show citations if available
                citations = result.get("citations", [])
                if citations:
                    st.markdown("---")
                    st.markdown("**Sources:**")
                    
                    for citation in citations:
                        relevance = citation.get('score', 0) * 100
                        title = citation.get('title', 'Unknown Document')
                        
                        with st.expander(f"{title} (Relevance: {relevance:.0f}%)"):
                            if citation.get("page"):
                                st.write(f"Page: {citation['page']}")
                            
                            if citation.get("snippet"):
                                st.write(f"Excerpt: {citation['snippet'][:200]}...")
                            
                            if citation.get("url"):
                                st.link_button("View Document", citation["url"])
                else:
                    # Show when no documents were referenced for longer queries
                    if len(prompt.split()) > 3:
                        st.caption("Response based on general knowledge")
                
                # Show model used
                model_used = result.get("model_used", "Unknown")
                st.caption(f"Model: {model_used}")
                
            else:
                error_msg = f"Error: {result}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
st.caption("Powered by Paperless-ngx, Qdrant, and OpenRouter")
