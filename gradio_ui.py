#!/usr/bin/env python3
"""
Professional Gradio interface for Paperless RAG Q&A System
Designed for company staff use with clean, business-ready interface
"""

import gradio as gr
import requests
import json
from datetime import datetime
import time
from typing import List, Tuple, Optional

# API Configuration
API_BASE = "http://192.168.1.77:8088"

class DocumentAssistant:
    """Professional document assistant interface"""
    
    def __init__(self):
        self.session_history = []
        self.system_info = self.get_system_info()
    
    def get_system_info(self) -> dict:
        """Get system status and statistics"""
        try:
            health_response = requests.get(f"{API_BASE}/health", timeout=5)
            stats_response = requests.get(f"{API_BASE}/stats", timeout=5)
            
            health_data = health_response.json() if health_response.status_code == 200 else {}
            stats_data = stats_response.json() if stats_response.status_code == 200 else {}
            
            return {
                "health": health_data,
                "stats": stats_data,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": str(e), "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    def chat(self, message: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
        """Process chat message and return response"""
        if not message.strip():
            return "", history
        
        try:
            # Make API request
            response = requests.post(
                f"{API_BASE}/ask",
                json={"query": message},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No response received")
                citations = data.get("citations", [])
                
                # Format response with citations if available
                formatted_response = answer
                if citations:
                    formatted_response += "\n\n**Sources:**\n"
                    for i, citation in enumerate(citations, 1):
                        title = citation.get("title", "Unknown Document")
                        relevance = citation.get("score", 0) * 100
                        formatted_response += f"{i}. {title} (Relevance: {relevance:.0f}%)\n"
                
                # Update history
                history.append((message, formatted_response))
                return "", history
            else:
                error_msg = f"API Error: {response.status_code}"
                history.append((message, error_msg))
                return "", history
                
        except Exception as e:
            error_msg = f"Connection Error: {str(e)}"
            history.append((message, error_msg))
            return "", history
    
    def get_system_status(self) -> str:
        """Get formatted system status"""
        info = self.get_system_info()
        
        if "error" in info:
            return f"❌ System Error: {info['error']}\nLast checked: {info['last_updated']}"
        
        health = info.get("health", {})
        stats = info.get("stats", {})
        
        # Health status
        components = health.get("components", {})
        status_lines = ["**System Status:**"]
        
        for component, status in components.items():
            icon = "✅" if status == "healthy" else "❌"
            status_lines.append(f"{icon} {component.replace('_', ' ').title()}: {status}")
        
        # Statistics
        if stats:
            docs = stats.get("paperless_documents", "Unknown")
            chunks = stats.get("vector_database", {}).get("points_count", "Unknown")
            model = stats.get("llm_model", "Unknown")
            
            status_lines.extend([
                "",
                "**Statistics:**",
                f"📄 Documents: {docs}",
                f"🔍 Text Chunks: {chunks}",
                f"🤖 Model: {model}"
            ])
        
        status_lines.append(f"\nLast updated: {info['last_updated']}")
        return "\n".join(status_lines)
    
    def clear_chat(self) -> List[Tuple[str, str]]:
        """Clear chat history"""
        return []

def create_interface():
    """Create the Gradio interface"""
    assistant = DocumentAssistant()
    
    # Custom CSS for professional appearance
    custom_css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        max-width: 1200px;
        margin: 0 auto;
    }
    .header {
        text-align: center;
        padding: 20px 0;
        border-bottom: 2px solid #e1e5e9;
        margin-bottom: 20px;
    }
    .chat-container {
        height: 500px;
    }
    .status-panel {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    .quick-actions {
        margin-top: 15px;
    }
    """
    
    with gr.Blocks(css=custom_css, title="Document Assistant", theme=gr.themes.Soft()) as interface:
        # Header
        gr.Markdown(
            """
            # Document Assistant
            ### Professional AI-powered document search and Q&A system
            Ask questions about your documents or engage in general conversation.
            """,
            elem_classes=["header"]
        )
        
        with gr.Row():
            with gr.Column(scale=3):
                # Main chat interface
                chatbot = gr.Chatbot(
                    value=[],
                    height=500,
                    label="Chat",
                    elem_classes=["chat-container"],
                    bubble_full_width=False
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask about your documents or any general question...",
                        label="Message",
                        scale=4,
                        container=False
                    )
                    submit_btn = gr.Button("Send", scale=1, variant="primary")
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
                
                # Quick action buttons
                with gr.Row(elem_classes=["quick-actions"]):
                    gr.Markdown("**Quick Actions:**")
                
                with gr.Row():
                    quick_btn1 = gr.Button("What documents do I have?", size="sm")
                    quick_btn2 = gr.Button("Show recent reports", size="sm")
                    quick_btn3 = gr.Button("List contracts", size="sm")
                
                with gr.Row():
                    quick_btn4 = gr.Button("Find safety protocols", size="sm")
                    quick_btn5 = gr.Button("Show project status", size="sm")
                    quick_btn6 = gr.Button("Quality requirements", size="sm")
            
            with gr.Column(scale=1):
                # System status panel
                status_display = gr.Markdown(
                    assistant.get_system_status(),
                    label="System Status",
                    elem_classes=["status-panel"]
                )
                
                refresh_btn = gr.Button("Refresh Status", variant="secondary")
                
                # System info
                gr.Markdown(
                    """
                    **About:**
                    This system provides AI-powered search and Q&A capabilities across your document library.
                    
                    **Features:**
                    - Natural language queries
                    - Document citations
                    - General knowledge
                    - Real-time search
                    
                    **Support:**
                    For technical support, contact your IT department.
                    """,
                    elem_classes=["status-panel"]
                )
        
        # Event handlers
        def process_message(message, history):
            return assistant.chat(message, history)
        
        def quick_action(action_text, history):
            return assistant.chat(action_text, history)
        
        # Connect events
        msg.submit(process_message, [msg, chatbot], [msg, chatbot])
        submit_btn.click(process_message, [msg, chatbot], [msg, chatbot])
        clear_btn.click(assistant.clear_chat, outputs=[chatbot])
        refresh_btn.click(lambda: assistant.get_system_status(), outputs=[status_display])
        
        # Quick action buttons
        quick_btn1.click(lambda h: quick_action("What documents do I have?", h), [chatbot], [msg, chatbot])
        quick_btn2.click(lambda h: quick_action("Show recent reports", h), [chatbot], [msg, chatbot])
        quick_btn3.click(lambda h: quick_action("List contracts", h), [chatbot], [msg, chatbot])
        quick_btn4.click(lambda h: quick_action("Find safety protocols", h), [chatbot], [msg, chatbot])
        quick_btn5.click(lambda h: quick_action("Show project status", h), [chatbot], [msg, chatbot])
        quick_btn6.click(lambda h: quick_action("Quality requirements", h), [chatbot], [msg, chatbot])
        
        # Footer
        gr.Markdown(
            """
            ---
            *Powered by Paperless-ngx, Qdrant, and OpenRouter | Document Assistant v1.0*
            """,
            elem_classes=["footer"]
        )
    
    return interface

def main():
    """Launch the Gradio interface"""
    interface = create_interface()
    
    # Launch with professional settings
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=False,
        show_error=True,
        quiet=False,
        favicon_path=None,
        ssl_verify=False,
        inbrowser=True
    )

if __name__ == "__main__":
    main()
