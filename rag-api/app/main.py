"""FastAPI main application for Paperless RAG Q&A system."""

import logging
import sys
from contextlib import asynccontextmanager
from typing import List, Optional
import asyncio

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from . import __version__
from .config import get_settings
from .models import (
    AskRequest, AskResponse, Citation, IngestRequest, IngestResponse,
    HealthResponse, DocumentInfo
)
from .paperless import test_connection as test_paperless_connection, list_documents, get_document
from .retriever import search_similar_chunks, deduplicate_chunks
from .llm import generate_answer, test_llm_connection
from .ingest import ensure_collection, ingest_document, get_collection_stats
from .paperless import build_document_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/app.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Global variables for shared resources
qdrant_client: Optional[QdrantClient] = None
embedding_model: Optional[SentenceTransformer] = None
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting Paperless RAG API...")
    
    global qdrant_client, embedding_model
    
    try:
        # Initialize Qdrant client
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}")
        qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Ensure collection exists
        embedding_dim = embedding_model.get_sentence_embedding_dimension()
        ensure_collection(qdrant_client, embedding_dim)
        
        # Test connections
        await test_paperless_connection()
        await test_llm_connection()
        
        logger.info("Startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Paperless RAG Q&A API",
    description="A RAG system for Q&A over documents stored in paperless-ngx",
    version=__version__,
    lifespan=lifespan
)

# Configure CORS - MUST be added immediately after app creation
# Ensure ALLOWED_ORIGINS is a list
cors_origins = settings.ALLOWED_ORIGINS
if isinstance(cors_origins, str):
    cors_origins = [origin.strip() for origin in cors_origins.split(',')]

# For development, allow all origins if "*" is in the list
if "*" in cors_origins:
    cors_origins = ["*"]

# Add CORS middleware with explicit configuration
from starlette.middleware.cors import CORSMiddleware as StarletteCORS

# Use a permissive CORS policy suitable for LAN access. We avoid credentials so that
# we can safely allow any origin. The middleware will automatically handle preflight
# (OPTIONS) requests and echo the requesting Origin.
app.add_middleware(
    StarletteCORS,
    allow_origins=[],
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"]
)


# Dependency to get Qdrant client
def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client dependency."""
    if qdrant_client is None:
        raise HTTPException(status_code=500, detail="Qdrant client not initialized")
    return qdrant_client


# Dependency to get embedding model
def get_embedding_model() -> SentenceTransformer:
    """Get embedding model dependency."""
    if embedding_model is None:
        raise HTTPException(status_code=500, detail="Embedding model not initialized")
    return embedding_model


@app.get("/health", response_model=HealthResponse)
async def health_check(
    qdrant: QdrantClient = Depends(get_qdrant_client),
    embedder: SentenceTransformer = Depends(get_embedding_model)
):
    """Health check endpoint."""
    components = {
        "qdrant": "unknown",
        "embedding_model": "unknown",
        "paperless": "unknown",
        "llm": "unknown"
    }
    
    # Test Qdrant
    try:
        qdrant.get_collections()
        components["qdrant"] = "healthy"
    except Exception as e:
        components["qdrant"] = f"error: {str(e)[:100]}"
    
    # Test embedding model
    try:
        embedder.encode(["test"])
        components["embedding_model"] = "healthy"
    except Exception as e:
        components["embedding_model"] = f"error: {str(e)[:100]}"
    
    # Test paperless connection
    try:
        paperless_healthy = await test_paperless_connection()
        components["paperless"] = "healthy" if paperless_healthy else "error"
    except Exception as e:
        components["paperless"] = f"error: {str(e)[:100]}"
    
    # Test LLM connection
    try:
        llm_healthy = await test_llm_connection()
        components["llm"] = "healthy" if llm_healthy else "error"
    except Exception as e:
        components["llm"] = f"error: {str(e)[:100]}"
    
    # Determine overall status
    overall_status = "healthy" if all(
        status == "healthy" for status in components.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=__version__,
        components=components
    )


@app.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    qdrant: QdrantClient = Depends(get_qdrant_client),
    embedder: SentenceTransformer = Depends(get_embedding_model)
):
    """Ask a question about the documents."""
    logger.info(f"Received question: {request.query[:100]}...")
    
    try:
        # Determine if this query needs document search
        query_lower = request.query.lower()
        document_keywords = [
            'project', 'document', 'construction', 'methodology', 'procedure', 
            'specification', 'requirement', 'helipad', 'warehouse', 'port',
            'yanbu', 'kkmc', 'neom', 'progress', 'report', 'contract',
            'personnel', 'team', 'engineer', 'safety', 'quality'
        ]
        
        # Only search documents if query contains relevant keywords
        needs_documents = any(keyword in query_lower for keyword in document_keywords)
        
        chunks = []
        if needs_documents:
            # Search for relevant chunks - increase top_k for better coverage
            top_k = request.top_k or settings.RAG_TOP_K
            # Double the search results to ensure we get comprehensive coverage
            search_k = top_k * 2 if top_k < 20 else top_k
            chunks = search_similar_chunks(
                qdrant_client=qdrant,
                embedding_model=embedder,
                query=request.query,
                top_k=search_k,
                filter_tags=request.filter_tags
            )
        
        # If no chunks found and general chat is allowed, fall back to non-RAG response
        if not chunks and request.allow_general_chat:
            logger.info("No RAG context found; falling back to general chat mode")
            llm_result = await generate_answer(request.query, [], history=request.history)
            return AskResponse(
                answer=llm_result["answer"],
                citations=[],
                query=request.query,
                model_used=llm_result["model"]
            )
        elif not chunks:
            logger.warning("No relevant chunks found for query")
            return AskResponse(
                answer="I couldn't find any relevant information in the documents to answer your question.",
                citations=[],
                query=request.query,
                model_used=settings.OPENROUTER_MODEL
            )
        
        # Deduplicate similar chunks
        chunks = deduplicate_chunks(chunks)
        
        # Generate answer using LLM
        llm_result = await generate_answer(request.query, chunks, history=request.history)
        
        # Build citations
        citations = []
        for chunk in chunks:
            citation = Citation(
                doc_id=chunk["doc_id"],
                title=chunk["title"],
                page=chunk.get("page"),
                score=chunk["score"],
                url=build_document_url(chunk["doc_id"]),
                snippet=chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"]
            )
            citations.append(citation)
        
        logger.info(f"Generated answer with {len(citations)} citations")
        
        return AskResponse(
            answer=llm_result["answer"],
            citations=citations,
            query=request.query,
            model_used=llm_result["model"]
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    qdrant: QdrantClient = Depends(get_qdrant_client),
    embedder: SentenceTransformer = Depends(get_embedding_model)
):
    """Ingest documents into the vector database."""
    logger.info(f"Ingest request: doc_id={request.doc_id}, force_reindex={request.force_reindex}")
    
    try:
        if request.doc_id:
            # Ingest specific document
            result = await ingest_document(
                doc_id=request.doc_id,
                qdrant_client=qdrant,
                embedding_model=embedder,
                force_reindex=request.force_reindex
            )
            
            if result["status"] == "success":
                return IngestResponse(
                    message=f"Successfully ingested document {request.doc_id}",
                    documents_processed=1,
                    chunks_created=result["chunks_created"]
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to ingest document {request.doc_id}: {result.get('error', 'Unknown error')}"
                )
        else:
            # Ingest all or recently updated documents (background task)
            background_tasks.add_task(
                ingest_all_documents_background,
                qdrant,
                embedder,
                request.force_reindex,
                request.updated_after
            )
            
            return IngestResponse(
                message="Started background ingestion of documents",
                documents_processed=0,
                chunks_created=0
            )
            
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


async def ingest_all_documents_background(
    qdrant: QdrantClient,
    embedder: SentenceTransformer,
    force_reindex: bool = False,
    updated_after: Optional[str] = None
):
    """Background task to ingest all documents."""
    logger.info("Starting background ingestion of all documents")
    
    try:
        # Get list of documents from paperless
        docs_response = await list_documents(updated_after=updated_after)
        documents = docs_response.get("results", [])
        
        total_docs = len(documents)
        processed = 0
        total_chunks = 0
        
        for doc in documents:
            doc_id = doc["id"]
            try:
                result = await ingest_document(
                    doc_id=doc_id,
                    qdrant_client=qdrant,
                    embedding_model=embedder,
                    force_reindex=force_reindex
                )
                
                if result["status"] == "success":
                    processed += 1
                    total_chunks += result["chunks_created"]
                    logger.info(f"Ingested document {doc_id} ({processed}/{total_docs})")
                else:
                    logger.warning(f"Skipped document {doc_id}: {result.get('reason', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Failed to ingest document {doc_id}: {e}")
                continue
        
        logger.info(f"Background ingestion complete: {processed}/{total_docs} documents, {total_chunks} chunks")
        
    except Exception as e:
        logger.error(f"Background ingestion failed: {e}")


@app.get("/documents/search")
async def search_documents(
    q: str,
    limit: int = 10
):
    """Search for documents by title."""
    try:
        docs_response = await list_documents()
        documents = docs_response.get("results", [])
        
        # Simple title search
        query_lower = q.lower()
        matching_docs = []
        for doc in documents:
            if query_lower in doc.get("title", "").lower():
                matching_docs.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "url": build_document_url(doc["id"])
                })
        
        # Sort by relevance (exact match first)
        matching_docs.sort(key=lambda x: (
            not x["title"].lower().startswith(query_lower),
            x["title"].lower()
        ))
        
        return matching_docs[:limit]
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@app.get("/documents", response_model=List[DocumentInfo])
async def list_paperless_documents(
    limit: int = 20,
    offset: int = 0
):
    """List documents from paperless-ngx."""
    try:
        docs_response = await list_documents()
        documents = docs_response.get("results", [])
        
        # Apply pagination
        paginated_docs = documents[offset:offset + limit]
        
        # Convert to our model
        doc_infos = []
        for doc in paginated_docs:
            doc_info = DocumentInfo(
                id=doc["id"],
                title=doc["title"],
                created=doc["created"],
                modified=doc["modified"],
                file_type=doc.get("file_type", "unknown"),
                page_count=doc.get("page_count"),
                tags=[tag["name"] for tag in doc.get("tags", [])]
            )
            doc_infos.append(doc_info)
        
        return doc_infos
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.get("/documents/{doc_id}", response_model=DocumentInfo)
async def get_document_info(doc_id: int):
    """Get information about a specific document."""
    try:
        doc = await get_document(doc_id)
        
        return DocumentInfo(
            id=doc["id"],
            title=doc["title"],
            created=doc["created"],
            modified=doc["modified"],
            file_type=doc.get("file_type", "unknown"),
            page_count=doc.get("page_count"),
            tags=[tag["name"] for tag in doc.get("tags", [])]
        )
        
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}")


@app.get("/stats")
async def get_statistics(
    qdrant: QdrantClient = Depends(get_qdrant_client)
):
    """Get system statistics."""
    try:
        # Get collection stats
        collection_stats = get_collection_stats(qdrant)
        
        # Get paperless document count
        try:
            docs_response = await list_documents()
            paperless_doc_count = docs_response.get("count", 0)
        except Exception:
            paperless_doc_count = "unknown"
        
        return {
            "vector_database": collection_stats,
            "paperless_documents": paperless_doc_count,
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.OPENROUTER_MODEL
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": "Paperless RAG Q&A API",
        "version": __version__,
        "description": "A RAG system for Q&A over documents stored in paperless-ngx",
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "ingest": "/ingest",
            "documents": "/documents",
            "stats": "/stats"
        }
    }


# OPTIONS handler removed - handled by CORS middleware

@app.get("/cors-debug")
async def cors_debug():
    """Debug endpoint to check CORS configuration."""
    return {
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "allowed_origins_type": type(settings.ALLOWED_ORIGINS).__name__
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=False
    )
