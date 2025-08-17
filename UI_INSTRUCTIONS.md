# 🖥️ Web UI Instructions

## 🚀 Quick Start

To launch the beautiful web interface for your Paperless RAG system:

```bash
python3 start_ui.py
```

This will:
- ✅ Update the API with proper CORS settings
- ✅ Start a web server at http://localhost:3000  
- ✅ Automatically open your browser
- ✅ Show you a modern chat interface

## 🎨 Web UI Features

### 📱 **Chat Interface**
- Clean, modern design similar to ChatGPT
- Real-time Q&A with your documents
- Automatic scrolling and message history
- Mobile-responsive layout

### 📊 **Live System Monitoring**
- **Real-time status indicators** for:
  - Qdrant (vector database)
  - Paperless-ngx connection
  - OpenRouter LLM
  - Embedding model
- **Live statistics**:
  - Total documents indexed
  - Number of text chunks
  - Auto-refresh every 30 seconds

### 🔍 **Enhanced Citations**
- **Clickable links** to view documents in Paperless
- **Page numbers** for precise references
- **Relevance scores** showing match confidence
- **Document snippets** for quick context
- **Clean formatting** of sources

### 💡 **Quick Question Buttons**
Pre-made buttons for common queries:
- "What documents do I have?"
- "What topics are covered?"
- "Show me contracts"
- "Welding procedures"
- "Quality requirements"

### ⚡ **Performance Features**
- **Loading indicators** during processing
- **Error handling** with user-friendly messages
- **Auto-focus** on input after responses
- **Keyboard shortcuts** (Enter to send)

## 🌐 **Access URLs**

When running:
- **Web UI**: http://localhost:3000 (main interface)
- **API**: http://localhost:8088 (backend)
- **Paperless**: http://192.168.1.77:8000 (document management)
- **Qdrant**: http://localhost:6333 (vector database)

## 🎯 **How to Use**

1. **Start the UI**: `python3 start_ui.py`
2. **Wait for startup**: Check that all status indicators are green
3. **Ask questions**: Type naturally, like "What welding procedures do I have?"
4. **Click citations**: View full documents in Paperless
5. **Use quick buttons**: Try the pre-made questions
6. **Monitor system**: Watch stats update in real-time

## 🔧 **Troubleshooting**

### **UI won't load**
```bash
# Check if port 3000 is available
netstat -an | grep 3000

# Try different port
python3 serve_ui.py  # Uses simple HTTP server
```

### **API not responding**
```bash
# Check API status
curl http://localhost:8088/health

# Restart API if needed
python3 restart_api.py
```

### **CORS errors in browser**
The `start_ui.py` script automatically updates CORS settings. If you still get errors:
```bash
# Manually restart API with new settings
sudo docker compose restart rag-api
```

### **Browser won't open automatically**
Manually navigate to: http://localhost:3000

## 📱 **Mobile Support**

The UI is fully responsive and works on:
- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Tablets (iPad, Android tablets)
- ✅ Mobile phones (responsive layout)

## 🎨 **UI Screenshots**

The interface includes:
- **Purple gradient header** with title and description
- **Status bar** with real-time health indicators
- **Chat area** with user/assistant message bubbles
- **Citation panels** with document links and snippets
- **Statistics sidebar** with live document counts
- **Quick question buttons** for common queries

## 🛑 **Stopping the UI**

Press `Ctrl+C` in the terminal where you ran `start_ui.py`

## 🔄 **Alternative: Simple Server**

If `start_ui.py` has issues, use the simple server:

```bash
python3 serve_ui.py
```

This provides a basic HTTP server without auto-restart features.

---

🎉 **Enjoy your beautiful Paperless RAG interface!**
