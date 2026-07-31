"""Abstract storage adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class StorageEntry:
    """Metadata for a file or directory in storage."""

    name: str
    path: str
    type: str  # "file" or "directory"
    size: Optional[int] = None
    modified: Optional[float] = None


class StorageAdapter(ABC):
    """Interface for reading and writing files in a storage backend."""

    provider: str = "base"

    @abstractmethod
    def write_bytes(self, path: str, data: bytes) -> str:
        """Write bytes to ``path`` (relative to storage root). Returns the stored path."""

    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        """Read bytes from ``path``."""

    @abstractmethod
    def exists(self, path: str = "") -> bool:
        """Return True if the path exists."""

    @abstractmethod
    def is_file(self, path: str) -> bool:
        """Return True if the path is a file."""

    @abstractmethod
    def is_dir(self, path: str = "") -> bool:
        """Return True if the path is a directory (or storage root)."""

    @abstractmethod
    def list_dir(self, path: str = "") -> List[StorageEntry]:
        """List immediate children of a directory."""

    @abstractmethod
    def ensure_dir(self, path: str) -> None:
        """Create a directory (and parents) if needed."""

    @abstractmethod
    def get_local_root(self) -> Path:
        """
        Return a local filesystem root for GIS libraries that need real paths.

        Cloud adapters may use a local cache directory and sync as needed.
        """

    def resolve_local_path(self, file_path: str, relative_to_storage: bool = True) -> Path:
        """
        Resolve ``file_path`` to a local Path.

        Absolute paths are returned as-is. Relative paths are joined to the
        local storage root when ``relative_to_storage`` is True.
        """
        path = Path(file_path)
        if path.is_absolute():
            return path.expanduser().resolve()
        if relative_to_storage:
            return (self.get_local_root() / path).resolve()
        return path.expanduser().resolve()

    def describe(self) -> str:
        """Human-readable description of this storage backend."""
        return f"{self.provider}:{self.get_local_root()}"
