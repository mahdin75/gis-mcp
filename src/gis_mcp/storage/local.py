"""Local filesystem storage adapter."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from .base import StorageAdapter, StorageEntry


class LocalStorageAdapter(StorageAdapter):
    """Store files on the local filesystem."""

    provider = "local"

    def __init__(self, root: Optional[Path] = None):
        if root is None:
            root = Path.home() / ".gis_mcp" / "data"
        self._root = Path(root).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def get_local_root(self) -> Path:
        return self._root

    def _resolve(self, path: str = "") -> Path:
        clean = str(path or "").lstrip("/").replace("\\", "/")
        if not clean:
            return self._root
        return (self._root / clean).resolve()

    def write_bytes(self, path: str, data: bytes) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return str(path).lstrip("/").replace("\\", "/")

    def read_bytes(self, path: str) -> bytes:
        target = self._resolve(path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return target.read_bytes()

    def exists(self, path: str = "") -> bool:
        return self._resolve(path).exists()

    def is_file(self, path: str) -> bool:
        return self._resolve(path).is_file()

    def is_dir(self, path: str = "") -> bool:
        return self._resolve(path).is_dir()

    def ensure_dir(self, path: str) -> None:
        self._resolve(path).mkdir(parents=True, exist_ok=True)

    def list_dir(self, path: str = "") -> List[StorageEntry]:
        target = self._resolve(path)
        if not target.exists():
            raise FileNotFoundError(f"Path not found: {path or 'root'}")

        if target.is_file():
            stat = target.stat()
            clean = str(path).lstrip("/").replace("\\", "/")
            return [
                StorageEntry(
                    name=target.name,
                    path=clean,
                    type="file",
                    size=stat.st_size,
                    modified=stat.st_mtime,
                )
            ]

        entries: List[StorageEntry] = []
        for item in target.iterdir():
            stat = item.stat()
            relative = item.relative_to(self._root)
            entries.append(
                StorageEntry(
                    name=item.name,
                    path=str(relative).replace("\\", "/"),
                    type="file" if item.is_file() else "directory",
                    size=stat.st_size if item.is_file() else None,
                    modified=stat.st_mtime,
                )
            )
        entries.sort(key=lambda e: (e.type != "directory", e.name.lower()))
        return entries

    def describe(self) -> str:
        return f"local:{self._root}"
