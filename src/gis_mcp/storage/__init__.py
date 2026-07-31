"""Storage adapters for local filesystem and cloud backends."""

from .base import StorageAdapter, StorageEntry
from .local import LocalStorageAdapter

__all__ = [
    "StorageAdapter",
    "StorageEntry",
    "LocalStorageAdapter",
    "GCPStorageAdapter",
    "create_storage_adapter",
]


def __getattr__(name: str):
    # Lazy import so google-cloud-storage is only required when GCP is used.
    if name == "GCPStorageAdapter":
        from .gcp import GCPStorageAdapter

        return GCPStorageAdapter
    if name == "create_storage_adapter":
        from .factory import create_storage_adapter

        return create_storage_adapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
