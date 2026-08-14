"""Pydantic schemas for RAG, Vector Embeddings, Metadata, and Codebase Indexing."""

from typing import Any

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Rich metadata for filtering, authorization, and citations."""

    document_id: str | None = Field(default=None, description="Parent document identifier")
    workspace_id: str | None = Field(default=None, description="Workspace identifier")
    user_id: str | None = Field(default=None, description="Owner user identifier")
    project_id: str | None = Field(default=None, description="Project identifier")
    source_type: str = Field(default="code", description="Source type: code|pdf|docx|txt|csv|json")
    file_name: str = Field(..., description="Basename of source file")
    file_path: str = Field(..., description="Workspace relative or storage file path")
    chunk_index: int = Field(default=0, ge=0, description="Index of chunk in parent document")
    language: str | None = Field(default=None, description="Programming or markup language")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")
    embedding_provider: str = Field(default="local", description="Vector provider name")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")
    embedding_dimension: int = Field(default=384, description="Vector dimension size")


class DocumentChunk(BaseModel):
    """Semantic code or document chunk with metadata."""

    chunk_id: str = Field(..., description="Unique chunk identifier string")
    file_path: str = Field(..., description="Workspace relative file path")
    start_line: int = Field(default=1, ge=1, description="Start line number in source file")
    end_line: int = Field(default=1, ge=1, description="End line number in source file")
    content: str = Field(..., description="Text or source code snippet content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata dictionary"
    )


class SearchResult(BaseModel):
    """Scored search match item with citation information."""

    chunk: DocumentChunk = Field(..., description="Matched document chunk")
    score: float = Field(..., description="Similarity relevance score (0.0 to 1.0)")
    citation: str = Field(default="", description="Formatted source citation string")


class RAGQueryRequest(BaseModel):
    """Payload model for querying vector index."""

    query: str = Field(..., min_length=2, description="Natural language search query")
    top_k: int = Field(default=8, ge=1, le=50, description="Number of results to return")
    file_extension: str | None = Field(
        default=None, description="Optional extension filter (e.g. .py, .ts)"
    )
    workspace_id: str | None = Field(default=None, description="Optional workspace filter")
    source_type: str | None = Field(default=None, description="Optional source type filter")


class RAGQueryResponse(BaseModel):
    """Result model containing matching code/document chunks."""

    query: str = Field(..., description="Original search query")
    results: list[SearchResult] = Field(..., description="Top-k matching snippets")
    total_chunks_indexed: int = Field(
        ..., ge=0, description="Total chunks currently in vector store"
    )
    execution_time_ms: float = Field(..., description="Query execution duration in milliseconds")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class IndexWorkspaceResponse(BaseModel):
    """Response returned after workspace indexing."""

    total_files_scanned: int = Field(..., ge=0, description="Total files scanned")
    total_chunks_created: int = Field(..., ge=0, description="Total code chunks created")
    duration_ms: float = Field(..., description="Indexing duration in milliseconds")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class RAGDocumentItem(BaseModel):
    """Indexed document record metadata."""

    document_id: str = Field(..., description="Unique document ID")
    name: str = Field(..., description="Document filename")
    user_id: str | None = Field(default=None, description="Owner user ID")
    chunk_count: int = Field(..., description="Number of indexed chunks")
    status: str = Field(default="indexed", description="Indexing status")
    created_at: str = Field(..., description="Creation ISO timestamp")


class RAGStatusResponse(BaseModel):
    """RAG subsystem status summary response."""

    enabled: bool = Field(..., description="Whether RAG is enabled")
    embedding_provider: str = Field(..., description="Active embedding provider name")
    embedding_model: str = Field(..., description="Active embedding model")
    total_documents: int = Field(..., description="Total indexed documents")
    total_chunks: int = Field(..., description="Total indexed chunks")
    status: str = Field(default="ready", description="Overall RAG status")
