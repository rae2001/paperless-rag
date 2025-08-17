# Paperless RAG Q&A System

A Retrieval-Augmented Generation (RAG) system that enables natural language Q&A over documents stored in [paperless-ngx](https://github.com/paperless-ngx/paperless-ngx). The system uses local embeddings, vector search, and OpenRouter LLMs to provide accurate answers with citations.

## Features

- 🔍 **Natural Language Q&A**: Ask questions about your documents in plain English
- 🖥️ **Beautiful Web UI**: Modern chat interface with real-time system monitoring
- 📚 **Multiple File Types**: Supports PDF, DOCX, and TXT files
- 🌍 **Multilingual**: Uses BAAI/bge-m3 embeddings supporting 100+ languages
- 🏠 **Privacy-First**: All document processing happens locally, only queries go to LLM
- 🔗 **Source Citations**: Every answer includes document references with page numbers
- 🐳 **Dockerized**: Easy deployment with docker-compose
- ⚡ **Fast Search**: Vector similarity search with Qdrant database
- 🔄 **Auto-Sync**: Incremental document indexing from paperless-ngx
- 📊 **Live Stats**: Real-time monitoring of documents, chunks, and system health

## Architecture

```
[paperless-ngx] <--REST--> [rag-api]
                            |\
                            | \__ [embedding worker] 
                            |____ [Qdrant vector DB]
                            
[client] --> /ask --> [RAG API] --> [OpenRouter LLM]
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Running paperless-ngx instance
- OpenRouter API key ([get one here](https://openrouter.ai/))
- Paperless-ngx API token

### 1. Clone and Setup

```bash
git clone <this-repo>
cd paperless-rag

# Copy environment template
cp env.example .env
```

### 2. Configure Environment

Edit `.env` file with your settings:

```bash
# Paperless-ngx Configuration  
PAPERLESS_BASE_URL=http://192.168.1.77:8000
PAPERLESS_API_TOKEN=your_paperless_token_here

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# Other settings use defaults...
```

**Getting Paperless API Token:**
1. Log into your paperless-ngx instance
2. Go to Settings → API Tokens
3. Create a new token and copy it

**Getting OpenRouter API Key:**
1. Sign up at [OpenRouter](https://openrouter.ai/)
2. Go to Keys section and create an API key
3. Add credits to your account for API usage

### 3. Start Services

```bash
docker-compose up -d
```

This starts:
- `qdrant` - Vector database (port 6333)
- `rag-api` - FastAPI service (port 8088)

### 4. Check Health

```bash
curl http://localhost:8088/health
```

You should see all components as "healthy".

### 5. Start Web UI (Optional but Recommended)

```bash
python3 start_ui.py
```

This will:
- ✅ Update API CORS settings 
- ✅ Start web server at http://localhost:3000
- ✅ Open browser automatically
- ✅ Provide a beautiful chat interface

### 6. Ingest Documents

Index all your paperless documents:

```bash
curl -X POST http://localhost:8088/ingest \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or ingest a specific document:

```bash
curl -X POST http://localhost:8088/ingest \
  -H "Content-Type: application/json" \
  -d '{"doc_id": 123}'
```

### 7. Ask Questions

**Option A: Use the Web UI (Recommended)**
```bash
python3 start_ui.py
```
This opens a beautiful web interface at http://localhost:3000

**Option B: Use curl commands**
```bash
curl -X POST http://localhost:8088/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the warranty period for the belt conveyor?"}'
```

## API Endpoints

### `POST /ask`
Ask questions about your documents.

**Request:**
```json
{
  "query": "What is the warranty period?",
  "filter_tags": ["contracts", "warranties"],  // optional
  "top_k": 6  // optional, override default
}
```

**Response:**
```json
{
  "answer": "The warranty period is 24 months...",
  "citations": [
    {
      "doc_id": 123,
      "title": "Equipment Manual",
      "page": 15,
      "score": 0.89,
      "url": "http://192.168.1.77:8000/documents/123",
      "snippet": "Warranty coverage extends for..."
    }
  ],
  "query": "What is the warranty period?",
  "model_used": "openai/gpt-4o-mini"
}
```

### `POST /ingest`
Index documents into the vector database.

**Request:**
```json
{
  "doc_id": 123,         // optional, ingest specific doc
  "force_reindex": false // optional, reindex existing
}
```

### `GET /documents`
List paperless documents.

### `GET /health`
System health check.

### `GET /stats`
System statistics and metrics.

## Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PAPERLESS_BASE_URL` | - | Your paperless-ngx URL |
| `PAPERLESS_API_TOKEN` | - | Paperless API token |
| `OPENROUTER_API_KEY` | - | OpenRouter API key |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | LLM model to use |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Embedding model |
| `RAG_TOP_K` | `6` | Number of chunks to retrieve |
| `CHUNK_TOKENS` | `800` | Max tokens per chunk |
| `CHUNK_OVERLAP` | `120` | Token overlap between chunks |

## Supported File Types

- **PDF**: Text extraction with page numbers
- **DOCX**: Full document text and tables
- **TXT**: Plain text files

## How It Works

1. **Document Ingestion**: 
   - Downloads documents from paperless-ngx
   - Extracts text using appropriate parsers
   - Splits into overlapping chunks (~800 tokens)
   - Generates embeddings using BGE-M3 model
   - Stores in Qdrant vector database

2. **Question Answering**:
   - Converts question to embedding vector
   - Searches similar document chunks
   - Sends top chunks + question to LLM
   - Returns answer with source citations

## Troubleshooting

### Common Issues

**Connection Errors:**
```bash
# Check paperless connection
curl http://192.168.1.77:8000/api/

# Check Qdrant
curl http://localhost:6333/collections

# Check API health
curl http://localhost:8088/health
```

**No Results Found:**
- Ensure documents are ingested: `curl http://localhost:8088/stats`
- Try broader questions
- Check if documents contain searchable text (OCR for scanned PDFs)

**High Latency:**
- Reduce `RAG_TOP_K` (fewer chunks)
- Use faster OpenRouter model
- Reduce `MAX_SNIPPETS_TOKENS`

**Memory Issues:**
- Reduce `CHUNK_TOKENS` for smaller chunks
- Process fewer documents at once
- Use CPU-optimized embedding model

**Torch Security Error (CVE-2025-32434):**
- The requirements.txt includes `torch>=2.6.0` for security
- If you see torch loading errors, rebuild: `python3 quick_rebuild.py`

### Logs

View application logs:
```bash
docker-compose logs -f rag-api
```

Log files are also stored in `./logs/` directory.

## Development

### Local Development

```bash
cd rag-api
pip install -r requirements.txt

# Set environment variables
export PAPERLESS_BASE_URL=http://192.168.1.77:8000
# ... other vars

# Run locally
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
```

### Adding New File Types

1. Add extraction logic in `app/extractors.py`
2. Update `detect_file_type()` function
3. Add file extension to `get_supported_extensions()`

### Custom Embedding Models

Change `EMBEDDING_MODEL` in `.env` to any sentence-transformers compatible model:
- `BAAI/bge-large-en-v1.5` (English only, high quality)
- `sentence-transformers/all-MiniLM-L6-v2` (Fast, multilingual)
- `intfloat/e5-large-v2` (High performance)

## Performance Tuning

### Chunk Settings
- **Large chunks** (1000+ tokens): Better context but slower, more expensive
- **Small chunks** (400-600 tokens): Faster but may miss context
- **High overlap** (150+ tokens): Better continuity but more storage

### Search Settings
- **Higher TOP_K** (8-12): More comprehensive but slower
- **Lower TOP_K** (3-5): Faster but may miss relevant info

### Model Selection
- **Free models**: `openai/gpt-4o-mini`, slower but cost-effective
- **Paid models**: `openai/gpt-4`, `anthropic/claude-3-sonnet`, faster and higher quality

## Security

- API keys stored in environment variables
- CORS restricted to specified origins
- No document content sent to external services (only search results)
- All processing happens locally except LLM inference

## Roadmap

- [ ] Web UI for easy querying
- [ ] User authentication and per-user document filtering
- [ ] Advanced hybrid search (vector + keyword)
- [ ] Document summarization
- [ ] Real-time sync via webhooks
- [ ] Excel/PowerPoint support
- [ ] Multi-modal support (images, tables)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 Documentation: This README
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

Built with ❤️ for the paperless-ngx community
