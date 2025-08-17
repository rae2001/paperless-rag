"""Vector search and retrieval functionality."""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchAny
from sentence_transformers import SentenceTransformer

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

COLLECTION_NAME = "paperless_chunks"


def search_similar_chunks(
    qdrant_client: QdrantClient,
    embedding_model: SentenceTransformer,
    query: str,
    top_k: int = None,
    filter_tags: Optional[List[str]] = None,
    score_threshold: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Search for similar document chunks using vector similarity.
    
    Args:
        qdrant_client: Qdrant client instance
        embedding_model: Sentence transformer model for embeddings
        query: Search query text
        top_k: Number of top results to return
        filter_tags: Optional list of tags to filter by
        score_threshold: Minimum similarity score threshold
    
    Returns:
        List of similar chunks with metadata and scores
    """
    if top_k is None:
        top_k = settings.RAG_TOP_K
    
    try:
        # Generate query embedding
        query_vector = embedding_model.encode([query], convert_to_tensor=False)
        if hasattr(query_vector, 'tolist'):
            query_vector = query_vector.tolist()
        query_vector = query_vector[0]  # Get the first (and only) embedding
        
        # Build search filter
        search_filter = None
        if filter_tags:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="tags",
                        match=MatchAny(any=filter_tags)
                    )
                ]
            )
        
        # Perform vector search
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=top_k,
            score_threshold=score_threshold
        )
        
        # Format results
        formatted_results = []
        for result in search_results:
            chunk_data = {
                "text": result.payload.get("text", ""),
                "doc_id": result.payload.get("doc_id"),
                "title": result.payload.get("title", f"Document {result.payload.get('doc_id')}"),
                "page": result.payload.get("page"),
                "file_type": result.payload.get("file_type", "unknown"),
                "tags": result.payload.get("tags", []),
                "score": float(result.score),
                "token_count": result.payload.get("token_count", 0)
            }
            formatted_results.append(chunk_data)
        
        logger.info(f"Found {len(formatted_results)} similar chunks for query")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Failed to search similar chunks: {e}")
        raise


def search_by_document_id(
    qdrant_client: QdrantClient,
    doc_id: int,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieve all chunks for a specific document.
    
    Args:
        qdrant_client: Qdrant client instance
        doc_id: Paperless document ID
        limit: Maximum number of chunks to return
    
    Returns:
        List of chunks for the document
    """
    try:
        search_filter = Filter(
            must=[FieldCondition(key="doc_id", match=doc_id)]
        )
        
        # Use scroll for better performance with large results
        chunks, _ = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=search_filter,
            limit=limit
        )
        
        formatted_chunks = []
        for chunk in chunks:
            chunk_data = {
                "text": chunk.payload.get("text", ""),
                "doc_id": chunk.payload.get("doc_id"),
                "title": chunk.payload.get("title", f"Document {chunk.payload.get('doc_id')}"),
                "page": chunk.payload.get("page"),
                "file_type": chunk.payload.get("file_type", "unknown"),
                "tags": chunk.payload.get("tags", []),
                "token_count": chunk.payload.get("token_count", 0)
            }
            formatted_chunks.append(chunk_data)
        
        return formatted_chunks
        
    except Exception as e:
        logger.error(f"Failed to search chunks for document {doc_id}: {e}")
        raise


def hybrid_search(
    qdrant_client: QdrantClient,
    embedding_model: SentenceTransformer,
    query: str,
    top_k: int = None,
    filter_tags: Optional[List[str]] = None,
    keyword_boost: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining vector similarity and keyword matching.
    
    Args:
        qdrant_client: Qdrant client instance
        embedding_model: Sentence transformer model for embeddings
        query: Search query text
        top_k: Number of top results to return
        filter_tags: Optional list of tags to filter by
        keyword_boost: Weight for keyword matching (0.0 to 1.0)
    
    Returns:
        List of chunks with combined scores
    """
    if top_k is None:
        top_k = settings.RAG_TOP_K
    
    # Get vector search results
    vector_results = search_similar_chunks(
        qdrant_client=qdrant_client,
        embedding_model=embedding_model,
        query=query,
        top_k=top_k * 2,  # Get more results for reranking
        filter_tags=filter_tags,
        score_threshold=0.1  # Lower threshold for hybrid search
    )
    
    # Simple keyword matching boost
    query_keywords = set(query.lower().split())
    
    for result in vector_results:
        text_words = set(result["text"].lower().split())
        keyword_overlap = len(query_keywords & text_words) / len(query_keywords)
        
        # Combine vector score with keyword score
        vector_score = result["score"]
        keyword_score = keyword_overlap
        
        # Weighted combination
        combined_score = (1 - keyword_boost) * vector_score + keyword_boost * keyword_score
        result["score"] = combined_score
        result["vector_score"] = vector_score
        result["keyword_score"] = keyword_score
    
    # Re-sort by combined score and return top_k
    vector_results.sort(key=lambda x: x["score"], reverse=True)
    return vector_results[:top_k]


def get_chunks_summary(
    qdrant_client: QdrantClient,
    doc_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Get summary information about chunks in the database.
    
    Args:
        qdrant_client: Qdrant client instance
        doc_ids: Optional list of document IDs to filter by
    
    Returns:
        Summary statistics
    """
    try:
        # Build filter if doc_ids provided
        search_filter = None
        if doc_ids:
            search_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchAny(any=doc_ids))]
            )
        
        # Get all chunks (using scroll for efficiency)
        all_chunks = []
        offset = None
        
        while True:
            chunks, next_offset = qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=search_filter,
                limit=1000,
                offset=offset
            )
            
            all_chunks.extend(chunks)
            
            if next_offset is None:
                break
            offset = next_offset
        
        # Calculate statistics
        total_chunks = len(all_chunks)
        unique_docs = set()
        total_tokens = 0
        file_types = {}
        tag_counts = {}
        
        for chunk in all_chunks:
            payload = chunk.payload
            
            unique_docs.add(payload.get("doc_id"))
            total_tokens += payload.get("token_count", 0)
            
            file_type = payload.get("file_type", "unknown")
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            for tag in payload.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "total_chunks": total_chunks,
            "unique_documents": len(unique_docs),
            "total_tokens": total_tokens,
            "average_tokens_per_chunk": total_tokens / total_chunks if total_chunks > 0 else 0,
            "file_type_distribution": file_types,
            "top_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }
        
    except Exception as e:
        logger.error(f"Failed to get chunks summary: {e}")
        return {"error": str(e)}


def deduplicate_chunks(chunks: List[Dict[str, Any]], similarity_threshold: float = 0.95) -> List[Dict[str, Any]]:
    """
    Remove highly similar chunks to improve result diversity.
    
    Args:
        chunks: List of chunk dictionaries
        similarity_threshold: Threshold for considering chunks too similar
    
    Returns:
        Deduplicated list of chunks
    """
    if len(chunks) <= 1:
        return chunks
    
    deduplicated = []
    
    for chunk in chunks:
        is_duplicate = False
        chunk_text = chunk["text"].lower()
        
        for existing in deduplicated:
            existing_text = existing["text"].lower()
            
            # Simple similarity check based on text overlap
            overlap = len(set(chunk_text.split()) & set(existing_text.split()))
            total_words = len(set(chunk_text.split()) | set(existing_text.split()))
            
            if total_words > 0 and overlap / total_words > similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            deduplicated.append(chunk)
    
    logger.info(f"Deduplicated {len(chunks)} chunks to {len(deduplicated)} unique chunks")
    return deduplicated
