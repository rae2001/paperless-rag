# OpenWebUI Integration Guide for Paperless RAG

This guide covers the complete integration of OpenWebUI with your Paperless RAG system, providing a professional chat interface for document interactions.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Single command setup - handles everything
python setup.py

# Test the installation
python test_setup.py
```

### Option 2: Manual Step-by-Step Setup
```bash
# 1. Start the integrated system (use sudo if needed)
docker compose -f docker-compose-openwebui.yml up -d

# 2. Open http://localhost:3001 and configure manually
# Go to Settings > Connections > Add OpenAI API
# Base URL: http://localhost:8088, API Key: dummy-key-not-needed
```

## 🌐 Access URLs

- **OpenWebUI Interface**: http://localhost:3001
- **RAG API**: http://localhost:8088
- **API Documentation**: http://localhost:8088/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 🔐 Initial Setup

On first visit to OpenWebUI, you'll need to:
1. Create an admin account with your preferred credentials
2. Configure the API connection manually:
   - **API Base URL**: http://localhost:8088
   - **API Key**: dummy-key-not-needed

## 🎯 System Prompts

The integration includes pre-configured system prompts optimized for document interaction:

### 1. Paperless Document Expert (`paperless-expert`)
- **Use for**: Comprehensive document analysis and research
- **Features**: 
  - Semantic document search
  - Document citation
  - Complex question answering
  - Follow-up suggestions

### 2. Quick Document Lookup (`quick-lookup`)
- **Use for**: Fast information retrieval
- **Features**:
  - Concise answers
  - Bullet point summaries
  - Quick fact finding
  - Specific document references

## 💬 Example Interactions

### Document Search
```
User: "What documents do I have about insurance?"
Assistant: Based on your document collection, I found several insurance-related documents:

1. **Auto Insurance Policy** (2024-policy-auto.pdf)
   - Coverage details and premium information
   
2. **Home Insurance Agreement** (home-insurance-2024.pdf)
   - Property coverage and liability terms
   
3. **Health Insurance Summary** (health-benefits-summary.pdf)
   - Plan details and coverage options

Would you like me to provide specific details from any of these documents?
```

### Information Extraction
```
User: "What's my auto insurance deductible?"
Assistant: According to your Auto Insurance Policy (2024-policy-auto.pdf), your deductibles are:

- **Collision**: $500
- **Comprehensive**: $250
- **Glass**: $0 (no deductible)

The document is dated March 2024 and shows this is for policy #AI-789456123.
```

### Document Analysis
```
User: "Summarize all my tax documents from 2023"
Assistant: Here's a summary of your 2023 tax documents:

**Income Sources** (from W-2 and 1099 forms):
- Primary employment: $65,450
- Freelance income: $8,200
- Investment income: $1,340

**Deductions** (from receipts and statements):
- Home office expenses: $2,400
- Professional development: $800
- Charitable contributions: $1,200

**Key Documents**:
- 2023-w2-employer.pdf
- 2023-1099-freelance.pdf
- 2023-investment-summary.pdf
- 2023-deduction-receipts.pdf

Total gross income: $75,990
```

## ⚙️ Configuration Features

### Model Configuration
- **Default Model**: paperless-rag (auto-configured)
- **Temperature**: 0.1 (focused, factual responses)
- **Max Tokens**: 2048
- **RAG Integration**: Enabled by default

### UI Features
- **Title**: "Paperless Document Assistant"
- **Message Rating**: Enabled (help improve responses)
- **Message Editing**: Enabled
- **Conversation History**: Persistent
- **User Management**: Multi-user support

### RAG Settings
- **Chunk Size**: 600 tokens
- **Overlap**: 100 tokens
- **Top-K Results**: 5 most relevant chunks
- **Similarity Threshold**: 0.75

## 🎨 Customization

### Adding Custom System Prompts

1. Go to **Settings** → **Prompts**
2. Click **"+ Add Prompt"**
3. Example custom prompt:

```
Name: Legal Document Analyst
Command: legal-analyst
Content: You are a specialized legal document analyst. Focus on:
- Contract terms and conditions
- Legal obligations and rights
- Important dates and deadlines
- Risk assessment
- Compliance requirements

Always cite specific clauses and document sections when providing legal information.
```

### Modifying Default Settings

Edit `openwebui-config/settings.json`:
```json
{
  "ui": {
    "title": "Your Custom Title",
    "theme": "light"
  },
  "chat": {
    "default_system_prompt": "your-custom-prompt",
    "max_turns": 100
  }
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. OpenWebUI Won't Start
```bash
# Check container logs
sudo docker compose -f docker-compose-openwebui.yml logs open-webui

# Common fix: Port conflict
# Edit docker-compose-openwebui.yml and change port 3001 to another port
```

#### 2. Model Not Found
```bash
# Check RAG API is running
curl http://192.168.1.77:8088/health

# Restart services in order
sudo docker compose -f docker-compose-openwebui.yml restart rag-api
sudo docker compose -f docker-compose-openwebui.yml restart open-webui
```

#### 3. No Documents Found
- Ensure documents are indexed in your RAG system
- Check Qdrant dashboard: http://192.168.1.77:6333/dashboard
- Verify Paperless connection in RAG API

#### 4. Authentication Issues
```bash
# Reset OpenWebUI data (removes all users and settings)
sudo docker compose -f docker-compose-openwebui.yml down
sudo docker volume rm paperless-rag_open-webui-data
sudo docker compose -f docker-compose-openwebui.yml up -d
```

### Log Locations

- **OpenWebUI Logs**: `docker compose -f docker-compose-openwebui.yml logs open-webui`
- **RAG API Logs**: `./logs/rag-api.log`
- **Qdrant Logs**: `docker compose -f docker-compose-openwebui.yml logs qdrant`

## 🔄 Maintenance

### Regular Tasks

#### Weekly
- Review conversation quality and model performance
- Update system prompts based on usage patterns
- Check storage usage in Qdrant

#### Monthly
- Update OpenWebUI image: `docker compose -f docker-compose-openwebui.yml pull`
- Backup OpenWebUI data volume
- Review and organize document categories

### Backup Strategy

```bash
# Backup OpenWebUI data
sudo docker run --rm -v paperless-rag_open-webui-data:/data -v $(pwd):/backup alpine tar czf /backup/openwebui-backup.tar.gz /data

# Restore OpenWebUI data
sudo docker run --rm -v paperless-rag_open-webui-data:/data -v $(pwd):/backup alpine tar xzf /backup/openwebui-backup.tar.gz -C /
```

## 🚀 Advanced Features

### API Integration

OpenWebUI provides a full REST API compatible with OpenAI:

```python
import requests

# Chat completion
response = requests.post("http://192.168.1.77:3001/api/chat/completions", 
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "model": "paperless-rag",
        "messages": [{"role": "user", "content": "Find my insurance documents"}]
    }
)
```

### Webhook Integration

Configure webhooks for:
- New document notifications
- Search analytics
- User activity monitoring

### Custom Themes

Modify the UI appearance by editing CSS in OpenWebUI settings.

## 📞 Support

### Getting Help

1. **Check logs first**: All services log detailed information
2. **Review this guide**: Most issues are covered here
3. **Test individual components**: RAG API, Qdrant, OpenWebUI separately
4. **Check network connectivity**: Ensure all services can communicate

### Useful Commands

```bash
# Full system status
sudo docker compose -f docker-compose-openwebui.yml ps

# Restart everything
sudo docker compose -f docker-compose-openwebui.yml restart

# View real-time logs
sudo docker compose -f docker-compose-openwebui.yml logs -f

# Update all images
sudo docker compose -f docker-compose-openwebui.yml pull
sudo docker compose -f docker-compose-openwebui.yml up -d
```

---

**🎉 Congratulations!** You now have a fully integrated Paperless RAG system with a professional chat interface. Start exploring your documents with natural language queries!
