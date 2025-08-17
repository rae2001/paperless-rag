"""Pydantic models for API requests and responses."""

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request model for the /ask endpoint."""
    query: str = Field(..., description="The question to ask about the documents")
    filter_tags: Optional[List[str]] = Field(None, description="Optional list of paperless tags to filter by")
    top_k: Optional[int] = Field(None, description="Number of top results to retrieve (overrides default)")
    history: Optional[List[dict]] = Field(
        default=None,
        description="Optional recent chat history as a list of {role, content}"
    )
    allow_general_chat: bool = Field(
        default=True,
        description="If true, allow a general (non-RAG) answer when no relevant documents are found"
    )


class Citation(BaseModel):
    """Citation information for a document snippet."""
    doc_id: int = Field(..., description="Paperless document ID")
    title: str = Field(..., description="Document title")
    page: Optional[int] = Field(None, description="Page number where the information was found")
    score: float = Field(..., description="Relevance score from vector search")
    url: Optional[str] = Field(None, description="URL to view the document in paperless")
    snippet: str = Field(..., description="Text snippet that supports the answer")


class AskResponse(BaseModel):
    """Response model for the /ask endpoint."""
    answer: str = Field(..., description="Generated answer to the question")
    citations: List[Citation] = Field(..., description="List of source citations")
    query: str = Field(..., description="Original query for reference")
    model_used: str = Field(..., description="LLM model used to generate the answer")


class IngestRequest(BaseModel):
    """Request model for the /ingest endpoint."""
    doc_id: Optional[int] = Field(None, description="Specific document ID to ingest")
    force_reindex: bool = Field(False, description="Force reindexing even if document already exists")
    updated_after: Optional[str] = Field(
        None,
        description="ISO timestamp to ingest only documents modified after this time"
    )


class IngestResponse(BaseModel):
    """Response model for the /ingest endpoint."""
    message: str = Field(..., description="Status message")
    documents_processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of text chunks created")


class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    components: dict = Field(..., description="Status of system components")


class DocumentInfo(BaseModel):
    """Document information from paperless-ngx."""
    id: int
    title: str
    created: str
    modified: str
    file_type: str
    page_count: Optional[int] = None
    tags: List[str] = []


class ChunkInfo(BaseModel):
    """Information about a text chunk."""
    text: str
    page: Optional[int] = None
    doc_id: int
    title: str
    tags: List[str] = []
