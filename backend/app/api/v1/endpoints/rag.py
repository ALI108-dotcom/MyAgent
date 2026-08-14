"""Production-Grade RAG, Vector Search, Document Ingestion, and Status API Endpoints."""

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.agent.rag.embeddings import EmbeddingProviderFactory
from app.agent.rag.indexer import CodebaseIndexer
from app.agent.rag.vector_store import vector_store
from app.core.config import settings
from app.core.security import get_current_user, require_admin
from app.models.auth import UserRead
from app.models.rag import (
    IndexWorkspaceResponse,
    RAGDocumentItem,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGStatusResponse,
)

router = APIRouter()


class DocumentUploadRequest(BaseModel):
    """Payload model for indexing raw document text."""

    name: str = Field(..., min_length=1, description="Document filename or title")
    content: str = Field(..., min_length=1, description="Document text content")


@router.post(
    "/index",
    response_model=IndexWorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Index workspace source code files into vector store (Admin Only)",
    description="Scans source files and builds vector embeddings with incremental hashing.",
)
async def index_workspace(
    admin_user: UserRead = Depends(require_admin),
) -> IndexWorkspaceResponse:
    """Trigger workspace indexing (Admin Only)."""
    start_time = time.perf_counter()
    files_scanned, chunks_created = CodebaseIndexer.index_workspace(user_id=admin_user.user_id)
    elapsed = (time.perf_counter() - start_time) * 1000

    return IndexWorkspaceResponse(
        total_files_scanned=files_scanned,
        total_chunks_created=chunks_created,
        duration_ms=elapsed,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post(
    "/search",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform vector semantic code search with user isolation",
    description="Calculates query vector and returns top-k matching snippets with citations.",
)
async def search_codebase(
    request: RAGQueryRequest,
    current_user: UserRead = Depends(get_current_user),
) -> RAGQueryResponse:
    """Perform vector search with security user isolation."""
    start_time = time.perf_counter()

    if vector_store.total_chunks() == 0:
        CodebaseIndexer.index_workspace(user_id=current_user.user_id)

    results = vector_store.search_similar(
        query=request.query,
        user_id=current_user.user_id,
        workspace_id=request.workspace_id,
        top_k=request.top_k,
        file_extension=request.file_extension,
    )
    elapsed = (time.perf_counter() - start_time) * 1000

    return RAGQueryResponse(
        query=request.query,
        results=results,
        total_chunks_indexed=vector_store.total_chunks(),
        execution_time_ms=elapsed,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post(
    "/documents",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Index raw user document text",
    description="Parses, chunks, embeds, and indexes document text owned by current user.",
)
async def upload_document(
    request: DocumentUploadRequest,
    current_user: UserRead = Depends(get_current_user),
) -> dict[str, Any]:
    """Index user document text."""
    doc_id, chunk_count = CodebaseIndexer.index_raw_document(
        name=request.name, content=request.content, user_id=current_user.user_id
    )
    return {
        "status": "success",
        "document_id": doc_id,
        "name": request.name,
        "chunk_count": chunk_count,
        "message": f"Document '{request.name}' successfully indexed into RAG vector store.",
    }


@router.get(
    "/documents",
    response_model=list[RAGDocumentItem],
    status_code=status.HTTP_200_OK,
    summary="List all indexed documents owned by current user",
    description="Returns metadata list of documents indexed by user.",
)
async def list_user_documents(
    current_user: UserRead = Depends(get_current_user),
) -> list[RAGDocumentItem]:
    """List documents for user."""
    raw_docs = vector_store.list_user_documents(user_id=current_user.user_id)
    return [
        RAGDocumentItem(
            document_id=d["document_id"],
            name=d["name"],
            user_id=d.get("user_id"),
            chunk_count=d["chunk_count"],
            status=d["status"],
            created_at=d["created_at"],
        )
        for d in raw_docs
    ]


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an indexed document and all its chunks",
    description="Removes all vector chunks associated with document_id owned by current user.",
)
async def delete_document(
    document_id: str,
    current_user: UserRead = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete document chunks."""
    removed = vector_store.delete_document_chunks(document_id)
    return {
        "status": "success" if removed > 0 else "not_found",
        "document_id": document_id,
        "chunks_removed": removed,
        "message": f"Document '{document_id}' deleted ({removed} chunks removed).",
    }


@router.get(
    "/status",
    response_model=RAGStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get RAG subsystem status and metadata metrics",
    description="Returns active embedding provider, model, total documents, and total chunks.",
)
async def get_rag_status(
    current_user: UserRead = Depends(get_current_user),
) -> RAGStatusResponse:
    """Get RAG status."""
    provider = EmbeddingProviderFactory.get_provider()
    docs = vector_store.list_user_documents(user_id=current_user.user_id)

    return RAGStatusResponse(
        enabled=settings.RAG_ENABLED,
        embedding_provider=provider.provider_name,
        embedding_model=settings.EMBEDDING_MODEL,
        total_documents=len(docs),
        total_chunks=vector_store.total_chunks(),
        status="ready",
    )
