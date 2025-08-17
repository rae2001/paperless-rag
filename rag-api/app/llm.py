"""LLM integration with OpenRouter for generating answers."""

import logging
from typing import List, Dict, Any, Optional
import httpx
import json
from datetime import datetime

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# System prompt for RAG Q&A
SYSTEM_PROMPT = """You are a helpful and intelligent document assistant. Today's date is {today}. You have access to a knowledge base of documents and can answer questions based on their content. When documents appear to be from the same project or related topics, make connections between them to provide comprehensive insights.

Key guidelines:
1. ALWAYS provide comprehensive, detailed answers when documents contain relevant information
2. Look for ALL related documents and synthesize information from multiple sources
3. Identify relationships between documents (same project, methodologies, specifications, etc.)
4. Include specific details like:
   - Technical specifications and requirements
   - Methodologies and procedures
   - Key personnel and responsibilities
   - Timeline and milestones
   - Safety and quality requirements
5. Structure your response with clear sections when covering multiple aspects
6. Do NOT include numbered citations like [1] or [2] in your response
7. Mention document titles naturally when referencing sources (e.g., "According to the Helipad Construction Methodology...")

Remember: Users expect thorough, actionable answers that cover all relevant aspects found in the documents."""


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Args:
        text: Input text
    
    Returns:
        Estimated token count
    """
    # Rough approximation: 1 token ≈ 4 characters
    return len(text) // 4


def build_context_prompt(query: str, chunks: List[Dict[str, Any]], history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """
    Build the conversation prompt with context and query.
    
    Args:
        query: User's question
        chunks: List of relevant document chunks
    
    Returns:
        List of message dictionaries for the LLM
    """
    # Build context from chunks, grouping by document
    doc_groups = {}
    for chunk in chunks:
        doc_id = chunk.get("doc_id")
        if doc_id not in doc_groups:
            doc_groups[doc_id] = {
                "title": chunk.get("title", "Unknown Document"),
                "chunks": []
            }
        doc_groups[doc_id]["chunks"].append(chunk)
    
    context_parts = []
    total_tokens = 0
    max_tokens = settings.MAX_SNIPPETS_TOKENS
    
    # Format context by document
    for doc_id, doc_info in doc_groups.items():
        title = doc_info["title"]
        
        # Start document section
        doc_header = f"\n=== From document: {title} ===\n"
        context_parts.append(doc_header)
        
        # Add chunks from this document
        for chunk in doc_info["chunks"]:
            page = chunk.get("page")
            text = chunk.get("text", "")
            
            if page:
                context_entry = f"Page {page}:\n{text}\n"
            else:
                context_entry = f"{text}\n"
            
            # Check token limit
            entry_tokens = estimate_tokens(context_entry)
            if total_tokens + entry_tokens > max_tokens:
                logger.warning(f"Reached token limit, truncating context")
                break
            
            context_parts.append(context_entry)
            total_tokens += entry_tokens
    
    context = "\n".join(context_parts)
    
    # Build user message
    user_message = f"""Question: {query}

Context from documents:
{context}

Please answer the question based on the provided context. When referencing information, mention the document titles naturally in your response."""
    
    # Format system prompt with today's date
    from datetime import date
    system_prompt = SYSTEM_PROMPT.format(today=date.today().strftime("%B %d, %Y"))
    messages = [{"role": "system", "content": system_prompt}]
    # Append recent history (bounded to last 6 exchanges)
    if history:
        trimmed = history[-12:]
        for msg in trimmed:
            if msg.get("role") in {"user", "assistant", "system"} and isinstance(msg.get("content"), str):
                messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    
    return messages


async def call_openrouter(messages: List[Dict[str, str]], model: Optional[str] = None) -> Dict[str, Any]:
    """
    Call OpenRouter API to generate a response.
    
    Args:
        messages: List of conversation messages
        model: Optional model override
    
    Returns:
        Dictionary with response data
    """
    if model is None:
        model = settings.OPENROUTER_MODEL
    
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://paperless-rag.local",
        "X-Title": "Paperless RAG Q&A System"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 1000,  # Reasonable limit for answers
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract response
            if "choices" in data and len(data["choices"]) > 0:
                message_content = data["choices"][0]["message"]["content"]
                
                return {
                    "answer": message_content.strip(),
                    "model": model,
                    "usage": data.get("usage", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise ValueError("No valid response from OpenRouter")
                
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling OpenRouter: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.content}")
        raise
    except Exception as e:
        logger.error(f"Error calling OpenRouter: {e}")
        raise


async def generate_answer(
    query: str,
    chunks: List[Dict[str, Any]],
    model: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Generate an answer to a query using the provided document chunks.
    
    Args:
        query: User's question
        chunks: Relevant document chunks from vector search
        model: Optional LLM model override
    
    Returns:
        Dictionary with generated answer and metadata
    """
    if not chunks:
        return {
            "answer": "I couldn't find any relevant information in the documents to answer your question.",
            "model": model or settings.OPENROUTER_MODEL,
            "usage": {},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Build prompt with context and optional chat history
    messages = build_context_prompt(query, chunks, history)
    
    # Log prompt for debugging (without sensitive data)
    logger.info(f"Generating answer for query: {query[:100]}...")
    logger.debug(f"Context chunks: {len(chunks)}")
    
    # Call LLM
    result = await call_openrouter(messages, model)
    
    # Log usage
    usage = result.get("usage", {})
    if usage:
        logger.info(f"LLM usage - Prompt tokens: {usage.get('prompt_tokens', 0)}, "
                   f"Completion tokens: {usage.get('completion_tokens', 0)}, "
                   f"Total tokens: {usage.get('total_tokens', 0)}")
    
    return result


async def test_llm_connection(model: Optional[str] = None) -> bool:
    """
    Test connection to OpenRouter API.
    
    Args:
        model: Optional model to test
    
    Returns:
        True if connection successful, False otherwise
    """
    test_messages = [
        {"role": "user", "content": "Hello, can you respond with just 'OK'?"}
    ]
    
    try:
        result = await call_openrouter(test_messages, model)
        logger.info("LLM connection test successful")
        return True
    except Exception as e:
        logger.error(f"LLM connection test failed: {e}")
        return False


def extract_citations_from_answer(answer: str) -> List[str]:
    """
    Extract citation references from the generated answer.
    
    Args:
        answer: Generated answer text
    
    Returns:
        List of citation strings found in the answer
    """
    import re
    
    # Look for patterns like [Document Title, Page 1] or [Document Title]
    citation_patterns = [
        r'\[([^\]]+)\]',  # Basic [citation] pattern
        r'\(([^)]+, [Pp]age \d+)\)',  # (citation, page X) pattern
        r'\(([^)]+)\)'  # Basic (citation) pattern
    ]
    
    citations = []
    for pattern in citation_patterns:
        matches = re.findall(pattern, answer)
        citations.extend(matches)
    
    # Remove duplicates while preserving order
    unique_citations = []
    for citation in citations:
        if citation not in unique_citations:
            unique_citations.append(citation)
    
    return unique_citations


def validate_answer_quality(answer: str, query: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate the quality of the generated answer.
    
    Args:
        answer: Generated answer
        query: Original query
        chunks: Source chunks
    
    Returns:
        Dictionary with quality metrics
    """
    metrics = {
        "answer_length": len(answer),
        "has_citations": bool(extract_citations_from_answer(answer)),
        "not_found_response": "couldn't find" in answer.lower() or "not in the" in answer.lower(),
        "chunk_coverage": 0
    }
    
    # Check how many chunks are referenced
    answer_lower = answer.lower()
    referenced_chunks = 0
    
    for chunk in chunks:
        # Simple check for key terms from chunk in answer
        chunk_words = set(chunk.get("text", "").lower().split())
        answer_words = set(answer_lower.split())
        
        # If there's significant overlap, consider chunk referenced
        overlap = len(chunk_words & answer_words)
        if overlap > 5:  # Arbitrary threshold
            referenced_chunks += 1
    
    if chunks:
        metrics["chunk_coverage"] = referenced_chunks / len(chunks)
    
    return metrics
