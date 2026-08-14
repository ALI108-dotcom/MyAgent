"""Workspace Project Context Analyzer & Tree Generator."""

from datetime import datetime, timezone
from pathlib import Path

from app.models.memory import ProjectContext

# Standard directories to skip during scanning
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".next", "dist", "build", "out", ".mypy_cache"
}

# Key configuration files to highlight in context
KEY_FILE_NAMES = {
    "README.md", ".gitignore", "pyproject.toml", "requirements.txt",
    "package.json", "tsconfig.json", "next.config.ts", "main.py"
}


class ProjectContextBuilder:
    """Scans workspace directory structure and constructs project context summaries."""

    @staticmethod
    def get_workspace_root() -> Path:
        """Return workspace root path."""
        return Path(__file__).resolve().parents[3]

    @classmethod
    def build_context(cls) -> ProjectContext:
        """Scan workspace and generate ProjectContext Pydantic model."""
        workspace_root = cls.get_workspace_root()
        file_count = 0
        key_files_found: list[str] = []
        tree_lines: list[str] = [f"{workspace_root.name}/"]

        def _scan(current_dir: Path, prefix: str = "  ") -> None:
            nonlocal file_count
            try:
                children = sorted(
                    current_dir.iterdir(),
                    key=lambda p: (not p.is_dir(), p.name.lower())
                )
            except PermissionError:
                return

            for child in children:
                if child.name in IGNORED_DIRS:
                    continue

                rel_path = child.relative_to(workspace_root).as_posix()

                if child.is_dir():
                    tree_lines.append(f"{prefix}├── {child.name}/")
                    _scan(child, prefix + "│   ")
                else:
                    file_count += 1
                    tree_lines.append(f"{prefix}└── {child.name}")
                    if child.name in KEY_FILE_NAMES or child.name.endswith((".py", ".ts", ".tsx")):
                        if len(key_files_found) < 15:
                            key_files_found.append(rel_path)

        _scan(workspace_root)

        return ProjectContext(
            workspace_root=str(workspace_root),
            file_count=file_count,
            structure_summary="\n".join(tree_lines[:100]),
            key_files=key_files_found,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
