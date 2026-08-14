"""VectorStore with User Isolation, Hybrid Search, Relevance Threshold & Document Metadata."""

from typing import Any

from app.agent.rag.embeddings import BaseEmbeddingProvider, EmbeddingProviderFactory
from app.core.config import settings
from app.models.rag import DocumentChunk, SearchResult


class VectorStore:
    """Manages document chunks and performs security-isolated vector similarity search."""

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []
        self._vectors: list[Any] = []

    def clear(self) -> None:
        """Clear all stored vectors and chunks."""
        self._chunks.clear()
        self._vectors.clear()

    def delete_document_chunks(self, document_id: str) -> int:
        """Remove all chunks associated with a specific document_id."""
        removed = 0
        new_chunks: list[DocumentChunk] = []
        new_vectors: list[Any] = []

        for chunk, vec in zip(self._chunks, self._vectors, strict=False):
            chunk_doc_id = chunk.metadata.get("document_id")
            if chunk_doc_id == document_id:
                removed += 1
            else:
                new_chunks.append(chunk)
                new_vectors.append(vec)

        self._chunks = new_chunks
        self._vectors = new_vectors
        return removed

    def add_chunks(self, chunks: list[DocumentChunk], provider_name: str | None = None) -> int:
        """Embed and add document chunks to vector index with metadata."""
        provider = EmbeddingProviderFactory.get_provider(provider_name)
        added = 0
        for chunk in chunks:
            vector = provider.embed_text(chunk.content)
            chunk.metadata["embedding_provider"] = provider.provider_name
            chunk.metadata["embedding_dimension"] = provider.embedding_dimension
            self._chunks.append(chunk)
            self._vectors.append(vector)
            added += 1
        return added

    def search_similar(
        self,
        query: str,
        user_id: str | None = None,
        workspace_id: str | None = None,
        top_k: int = 8,
        file_extension: str | None = None,
        provider_name: str | None = None,
        min_score: float | None = None,
    ) -> list[SearchResult]:
        """Perform user-isolated hybrid search with relevance threshold score filtering."""
        if not self._chunks:
            return []

        provider = EmbeddingProviderFactory.get_provider(provider_name)
        query_vec = provider.embed_text(query)
        effective_min_score = min_score if min_score is not None else settings.RAG_MIN_SCORE
        query_keywords = set(query.lower().split())

        scored_results: list[SearchResult] = []
        for chunk, doc_vec in zip(self._chunks, self._vectors, strict=False):
            # 1. Security Isolation Filter: user_id check
            chunk_user_id = chunk.metadata.get("user_id")
            if user_id and chunk_user_id and chunk_user_id != user_id:
                continue

            # 2. Workspace Filter
            chunk_ws_id = chunk.metadata.get("workspace_id")
            if workspace_id and chunk_ws_id and chunk_ws_id != workspace_id:
                continue

            # 3. File Extension Filter
            if file_extension and not chunk.file_path.endswith(file_extension):
                continue

            # 4. Semantic Similarity
            sem_score = BaseEmbeddingProvider.cosine_similarity(query_vec, doc_vec)

            # 5. Hybrid Keyword Matching Boost
            content_lower = chunk.content.lower()
            keyword_matches = sum(1 for kw in query_keywords if kw in content_lower and len(kw) > 2)
            lexical_boost = min(keyword_matches * 0.08, 0.3)

            total_score = min(sem_score + lexical_boost, 1.0)

            # 6. Relevance Threshold Filter
            if total_score >= effective_min_score:
                file_name = chunk.metadata.get("file_name", chunk.file_path)
                citation = (
                    f"📄 `{file_name}` — Lines {chunk.start_line}–{chunk.end_line}"
                )
                scored_results.append(
                    SearchResult(chunk=chunk, score=round(total_score, 4), citation=citation)
                )

        # Sort descending by similarity score
        scored_results.sort(key=lambda r: r.score, reverse=True)
        return scored_results[:top_k]

    def list_user_documents(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """Return list of distinct indexed documents for specified user."""
        docs_map: dict[str, dict[str, Any]] = {}
        for chunk in self._chunks:
            chunk_user_id = chunk.metadata.get("user_id")
            if user_id and chunk_user_id and chunk_user_id != user_id:
                continue

            doc_id = chunk.metadata.get("document_id", chunk.file_path)
            if doc_id not in docs_map:
                docs_map[doc_id] = {
                    "document_id": doc_id,
                    "name": chunk.metadata.get("file_name", chunk.file_path),
                    "user_id": chunk_user_id,
                    "chunk_count": 0,
                    "status": "indexed",
                    "created_at": chunk.metadata.get("created_at", "2026-08-15T00:00:00Z"),
                }
            docs_map[doc_id]["chunk_count"] += 1

        return list(docs_map.values())

    def total_chunks(self) -> int:
        """Return total count of indexed chunks."""
        return len(self._chunks)


# Global singleton instance
vector_store = VectorStore()
