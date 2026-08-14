"""Workspace Codebase & Document Indexer with Incremental Hashing & Metadata Tracking."""

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.agent.rag.vector_store import vector_store
from app.models.rag import DocumentChunk

# Target file extensions to index
SUPPORTED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".md", ".json", ".toml",
    ".txt", ".csv", ".html", ".css", ".sql", ".js"
}

# Directory names to skip
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".next", "dist", "build", "out", ".mypy_cache"
}


class CodebaseIndexer:
    """Scans workspace source code and documents to build vector index with incremental hash tracking."""

    _file_hashes: dict[str, str] = {}

    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute SHA256 content hash."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def _chunk_file(
        cls,
        file_path: Path,
        workspace_root: Path,
        user_id: str | None = None,
        workspace_id: str | None = "AgentAI/workspace",
    ) -> tuple[list[DocumentChunk], str]:
        """Split source code file into overlapping line windows with full metadata."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return [], ""

        lines = content.splitlines()
        if not lines:
            return [], ""

        content_hash = cls._compute_hash(content)
        rel_path = file_path.relative_to(workspace_root).as_posix()
        chunks: list[DocumentChunk] = []

        window_size = 25
        overlap = 5
        step = window_size - overlap
        now_iso = datetime.now(timezone.utc).isoformat()
        doc_id = f"doc-{hashlib.md5(rel_path.encode()).hexdigest()[:10]}"

        ext = file_path.suffix.lower()
        lang_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".md": "markdown",
            ".json": "json",
            ".csv": "csv",
        }
        lang = lang_map.get(ext, "text")

        for idx, i in enumerate(range(0, len(lines), step)):
            chunk_lines = lines[i : i + window_size]
            chunk_text = "\n".join(chunk_lines).strip()
            if not chunk_text:
                continue

            chunk_id = f"chunk-{doc_id}-{idx}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    file_path=rel_path,
                    start_line=i + 1,
                    end_line=i + len(chunk_lines),
                    content=chunk_text,
                    metadata={
                        "document_id": doc_id,
                        "file_name": file_path.name,
                        "file_path": rel_path,
                        "user_id": user_id,
                        "workspace_id": workspace_id,
                        "source_type": "code" if ext in {".py", ".ts", ".tsx", ".js"} else "document",
                        "language": lang,
                        "chunk_index": idx,
                        "content_hash": content_hash,
                        "created_at": now_iso,
                    },
                )
            )

        return chunks, content_hash

    @classmethod
    def index_workspace(
        cls, user_id: str | None = None, workspace_id: str | None = "AgentAI/workspace"
    ) -> tuple[int, int]:
        """Incremental workspace scan populating VectorStore. Returns (files_scanned, chunks_created)."""
        workspace_root = Path(__file__).resolve().parents[3]

        files_scanned = 0
        all_chunks: list[DocumentChunk] = []

        for p in workspace_root.rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                if any(ignored in p.parts for ignored in IGNORED_DIRS):
                    continue

                rel_path = p.relative_to(workspace_root).as_posix()
                try:
                    content = p.read_text(encoding="utf-8")
                    file_hash = cls._compute_hash(content)
                except Exception:
                    continue

                # Incremental Check: Skip unchanged files
                if cls._file_hashes.get(rel_path) == file_hash and vector_store.total_chunks() > 0:
                    continue

                chunks, h = cls._chunk_file(p, workspace_root, user_id=user_id, workspace_id=workspace_id)
                if chunks:
                    cls._file_hashes[rel_path] = h
                    files_scanned += 1
                    all_chunks.extend(chunks)

        if all_chunks:
            vector_store.add_chunks(all_chunks)

        return files_scanned, len(all_chunks)

    @classmethod
    def index_raw_document(
        cls,
        name: str,
        content: str,
        user_id: str | None = None,
        workspace_id: str | None = "AgentAI/workspace",
    ) -> tuple[str, int]:
        """Index raw string document into VectorStore owned by user_id."""
        now_iso = datetime.now(timezone.utc).isoformat()
        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        content_hash = cls._compute_hash(content)

        lines = content.splitlines() or [content]
        chunks: list[DocumentChunk] = []
        window_size = 20
        step = 15

        for idx, i in enumerate(range(0, len(lines), step)):
            chunk_lines = lines[i : i + window_size]
            chunk_text = "\n".join(chunk_lines).strip()
            if not chunk_text:
                continue

            chunk_id = f"chunk-{doc_id}-{idx}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    file_path=name,
                    start_line=i + 1,
                    end_line=i + len(chunk_lines),
                    content=chunk_text,
                    metadata={
                        "document_id": doc_id,
                        "file_name": name,
                        "file_path": name,
                        "user_id": user_id,
                        "workspace_id": workspace_id,
                        "source_type": "document",
                        "chunk_index": idx,
                        "content_hash": content_hash,
                        "created_at": now_iso,
                    },
                )
            )

        if chunks:
            vector_store.add_chunks(chunks)

        return doc_id, len(chunks)
