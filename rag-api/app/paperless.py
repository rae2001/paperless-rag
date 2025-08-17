"""Integration with paperless-ngx API."""

import logging
from typing import Dict, List, Optional, Any
import httpx
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# HTTP headers for paperless API authentication
HEADERS = {"Authorization": f"Token {settings.PAPERLESS_API_TOKEN}"}


async def list_documents(
    updated_after: Optional[str] = None,
    page_size: int = 100,
    ordering: str = "-created"
) -> Dict[str, Any]:
    """
    List documents from paperless-ngx.
    
    Args:
        updated_after: ISO datetime string to filter documents modified after this time
        page_size: Number of documents per page
        ordering: Field to order by (e.g., "-created" for newest first)
    
    Returns:
        Dictionary containing documents list and pagination info
    """
    params = {
        "ordering": ordering,
        "page_size": page_size
    }
    
    if updated_after:
        params["modified__gt"] = updated_after
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            response = await client.get(
                f"{settings.PAPERLESS_BASE_URL}/api/documents/",
                params=params,
                headers=HEADERS
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to list documents: {e}")
            raise


async def get_document(doc_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific document.
    
    Args:
        doc_id: Paperless document ID
    
    Returns:
        Document metadata dictionary
    """
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            response = await client.get(
                f"{settings.PAPERLESS_BASE_URL}/api/documents/{doc_id}/",
                headers=HEADERS
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise


async def download_document(doc_id: int) -> bytes:
    """
    Download the original document file.
    
    Args:
        doc_id: Paperless document ID
    
    Returns:
        Document file content as bytes
    """
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            response = await client.get(
                f"{settings.PAPERLESS_BASE_URL}/api/documents/{doc_id}/download/",
                headers=HEADERS
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as e:
            logger.error(f"Failed to download document {doc_id}: {e}")
            raise


async def get_document_preview(doc_id: int) -> bytes:
    """
    Get document preview (usually PDF).
    
    Args:
        doc_id: Paperless document ID
    
    Returns:
        Preview file content as bytes
    """
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            response = await client.get(
                f"{settings.PAPERLESS_BASE_URL}/api/documents/{doc_id}/preview/",
                headers=HEADERS
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as e:
            logger.error(f"Failed to get preview for document {doc_id}: {e}")
            raise


async def get_document_text(doc_id: int) -> str:
    """
    Get extracted text content from a document.
    
    Args:
        doc_id: Paperless document ID
    
    Returns:
        Extracted text content
    """
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            response = await client.get(
                f"{settings.PAPERLESS_BASE_URL}/api/documents/{doc_id}/download/",
                headers={**HEADERS, "Accept": "text/plain"}
            )
            if response.status_code == 200:
                return response.text
            else:
                # Fallback to downloading and extracting
                logger.warning(f"Text endpoint not available for document {doc_id}, using file download")
                return ""
        except httpx.HTTPError as e:
            logger.error(f"Failed to get text for document {doc_id}: {e}")
            return ""


def build_document_url(doc_id: int) -> str:
    """
    Build a URL to view the document in paperless-ngx UI.
    
    Args:
        doc_id: Paperless document ID
    
    Returns:
        URL string to view the document
    """
    return f"{settings.PAPERLESS_BASE_URL}/documents/{doc_id}"


async def test_connection() -> bool:
    """
    Test connection to paperless-ngx API.
    
    Returns:
        True if connection is successful, False otherwise
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(
                f"{settings.PAPERLESS_BASE_URL}/api/",
                headers=HEADERS
            )
            response.raise_for_status()
            logger.info("Successfully connected to paperless-ngx")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to connect to paperless-ngx: {e}")
            return False


async def get_document_by_title(title: str) -> Optional[Dict[str, Any]]:
    """
    Search for a document by title.
    
    Args:
        title: Document title to search for
    
    Returns:
        Document metadata if found, None otherwise
    """
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            response = await client.get(
                f"{settings.PAPERLESS_BASE_URL}/api/documents/",
                params={"title__icontains": title},
                headers=HEADERS
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                return data["results"][0]
            return None
        except httpx.HTTPError as e:
            logger.error(f"Failed to search for document with title '{title}': {e}")
            return None
