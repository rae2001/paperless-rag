"""Document ingestion and text chunking for the vector database."""

import logging
import math
from typing import List, Dict, Any, Optional
from datetime import datetime
import tiktoken
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

from .config import get_settings
from .extractors import extract_text_from_file
from .paperless import get_document, download_document

logger = logging.getLogger(__name__)
settings = get_settings()

# Collection name for storing document chunks
COLLECTION_NAME = "paperless_chunks"

# Initialize tokenizer for counting tokens
try:
    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:
    logger.warning("Failed to load tiktoken, using approximate token counting")
    tokenizer = None


def count_tokens(text: str) -> int:
    """
    Count tokens in text.
    
    Args:
        text: Input text
    
    Returns:
        Approximate token count
    """
    if tokenizer:
        return len(tokenizer.encode(text))
    else:
        # Approximate: 1 token ≈ 4 characters
        return len(text) // 4


def chunk_text(text: str, chunk_tokens: int = None, overlap_tokens: int = None) -> List[str]:
    """
    Split text into overlapping chunks based on token count.
    
    Args:
        text: Text to chunk
        chunk_tokens: Maximum tokens per chunk
        overlap_tokens: Token overlap between chunks
    
    Returns:
        List of text chunks
    """
    if chunk_tokens is None:
        chunk_tokens = settings.CHUNK_TOKENS
    if overlap_tokens is None:
        overlap_tokens = settings.CHUNK_OVERLAP
    
    if not text.strip():
        return []
    
    if tokenizer:
        # Use actual tokenization
        tokens = tokenizer.encode(text)
        chunks = []
        
        step = chunk_tokens - overlap_tokens
        for i in range(0, len(tokens), step):
            chunk_tokens_slice = tokens[i:i + chunk_tokens]
            chunk_text = tokenizer.decode(chunk_tokens_slice)
            chunks.append(chunk_text.strip())
        
        return [chunk for chunk in chunks if chunk]
    else:
        # Fallback to character-based chunking
        chars_per_chunk = chunk_tokens * 4  # Approximate
        overlap_chars = overlap_tokens * 4
        
        chunks = []
        step = chars_per_chunk - overlap_chars
        
        for i in range(0, len(text), step):
            chunk = text[i:i + chars_per_chunk].strip()
            if chunk:
                chunks.append(chunk)
        
        return chunks


def ensure_collection(qdrant_client: QdrantClient, embedding_dimension: int):
    """
    Ensure the Qdrant collection exists with the correct configuration.
    
    Args:
        qdrant_client: Qdrant client instance
        embedding_dimension: Dimension of embedding vectors
    """
    try:
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if COLLECTION_NAME not in collection_names:
            logger.info(f"Creating collection '{COLLECTION_NAME}'")
            qdrant_client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=embedding_dimension, distance=Distance.COSINE)
            )
        else:
            logger.info(f"Collection '{COLLECTION_NAME}' already exists")
            
    except Exception as e:
        logger.error(f"Failed to ensure collection: {e}")
        raise


def upsert_chunks_to_qdrant(
    qdrant_client: QdrantClient,
    chunks: List[Dict[str, Any]],
    vectors: List[List[float]]
):
    """
    Upsert document chunks and their vectors to Qdrant.
    
    Args:
        qdrant_client: Qdrant client instance
        chunks: List of chunk metadata dictionaries
        vectors: List of embedding vectors
    """
    if len(chunks) != len(vectors):
        raise ValueError("Number of chunks must match number of vectors")
    
    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        # Generate a unique ID based on doc_id, page, and chunk index
        doc_id = chunk['doc_id']
        page = chunk.get('page', 0) or 0
        point_id = f"{doc_id}_{page}_{i}"
        
        points.append(PointStruct(
            id=point_id,
            vector=vector,
            payload=chunk
        ))
    
    try:
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info(f"Upserted {len(points)} chunks to Qdrant")
    except Exception as e:
        logger.error(f"Failed to upsert chunks to Qdrant: {e}")
        raise


async def ingest_document(
    doc_id: int,
    qdrant_client: QdrantClient,
    embedding_model: SentenceTransformer,
    force_reindex: bool = False
) -> Dict[str, Any]:
    """
    Ingest a single document into the vector database.
    
    Args:
        doc_id: Paperless document ID
        qdrant_client: Qdrant client instance
        embedding_model: Sentence transformer model for embeddings
        force_reindex: Whether to reindex even if document already exists
    
    Returns:
        Dictionary with ingestion results
    """
    logger.info(f"Starting ingestion of document {doc_id}")
    
    try:
        # Get document metadata
        doc_metadata = await get_document(doc_id)
        title = doc_metadata.get('title', f'Document {doc_id}')
        file_type = doc_metadata.get('file_type', 'unknown')
        tags = [tag['name'] for tag in doc_metadata.get('tags', [])]
        
        # Check if document already exists (unless force reindex)
        if not force_reindex:
            existing_chunks = qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                ),
                limit=1
            )[0]
            
            if existing_chunks:
                logger.info(f"Document {doc_id} already indexed, skipping")
                return {
                    "doc_id": doc_id,
                    "title": title,
                    "status": "skipped",
                    "chunks_created": 0,
                    "reason": "already_exists"
                }
        
        # Download document content
        doc_content = await download_document(doc_id)
        filename = doc_metadata.get('original_filename', f'document_{doc_id}.pdf')
        
        # Extract text
        extracted_pages = extract_text_from_file(filename, doc_content)
        
        if not extracted_pages:
            logger.warning(f"No text extracted from document {doc_id}")
            return {
                "doc_id": doc_id,
                "title": title,
                "status": "failed",
                "chunks_created": 0,
                "reason": "no_text_extracted"
            }
        
        # Process each page and create chunks
        all_chunks = []
        for page_num, page_text in extracted_pages:
            if not page_text.strip():
                continue
            
            # Split page text into chunks
            text_chunks = chunk_text(page_text)
            
            for text_chunk in text_chunks:
                chunk_metadata = {
                    "text": text_chunk,
                    "doc_id": doc_id,
                    "title": title,
                    "page": page_num,
                    "file_type": file_type,
                    "tags": tags,
                    "ingested_at": datetime.utcnow().isoformat(),
                    "token_count": count_tokens(text_chunk)
                }
                all_chunks.append(chunk_metadata)
        
        if not all_chunks:
            logger.warning(f"No chunks created from document {doc_id}")
            return {
                "doc_id": doc_id,
                "title": title,
                "status": "failed",
                "chunks_created": 0,
                "reason": "no_chunks_created"
            }
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
        chunk_texts = [chunk["text"] for chunk in all_chunks]
        embeddings = embedding_model.encode(chunk_texts, convert_to_tensor=False)
        
        # Convert to list of lists if needed
        if hasattr(embeddings, 'tolist'):
            embeddings = embeddings.tolist()
        
        # Remove existing chunks for this document if reindexing
        if force_reindex:
            qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                )
            )
        
        # Upsert chunks to Qdrant
        upsert_chunks_to_qdrant(qdrant_client, all_chunks, embeddings)
        
        logger.info(f"Successfully ingested document {doc_id} with {len(all_chunks)} chunks")
        
        return {
            "doc_id": doc_id,
            "title": title,
            "status": "success",
            "chunks_created": len(all_chunks),
            "pages_processed": len(extracted_pages)
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest document {doc_id}: {e}")
        return {
            "doc_id": doc_id,
            "title": f"Document {doc_id}",
            "status": "error",
            "chunks_created": 0,
            "error": str(e)
        }


async def remove_document(doc_id: int, qdrant_client: QdrantClient) -> bool:
    """
    Remove all chunks for a document from the vector database.
    
    Args:
        doc_id: Paperless document ID
        qdrant_client: Qdrant client instance
    
    Returns:
        True if successful, False otherwise
    """
    try:
        result = qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )
        )
        
        logger.info(f"Removed document {doc_id} from vector database")
        return True
        
    except Exception as e:
        logger.error(f"Failed to remove document {doc_id}: {e}")
        return False


def get_collection_stats(qdrant_client: QdrantClient) -> Dict[str, Any]:
    """
    Get statistics about the vector database collection.
    
    Args:
        qdrant_client: Qdrant client instance
    
    Returns:
        Dictionary with collection statistics
    """
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        
        return {
            "collection_name": COLLECTION_NAME,
            "vectors_count": collection_info.vectors_count,
            "points_count": collection_info.points_count,
            "segments_count": collection_info.segments_count,
            "status": collection_info.status.value if collection_info.status else "unknown"
        }
        
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return {"error": str(e)}
