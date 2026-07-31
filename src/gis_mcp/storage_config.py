"""
Storage configuration for GIS MCP Server.

Supports local filesystem (default) and optional cloud backends such as GCP.
Backward compatible with ``--storage-path`` / ``GIS_MCP_STORAGE_PATH``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .storage.base import StorageAdapter
from .storage.factory import create_storage_adapter
from .storage.local import LocalStorageAdapter

# Global storage state — initialized on server startup
_storage_adapter: Optional[StorageAdapter] = None
_storage_path: Optional[Path] = None


def get_default_storage_path() -> Path:
    """
    Get the default storage path: ~/.gis_mcp/data/

    Returns:
        Path object pointing to the default storage directory
    """
    return Path.home() / ".gis_mcp" / "data"


def _load_config_from_env_and_args(
    storage_config: Optional[Union[str, Dict[str, Any]]] = None,
) -> Optional[Union[str, Dict[str, Any]]]:
    """
    Resolve storage configuration from (highest priority first):
    1. Explicit ``storage_config`` argument (dict or JSON/path string)
    2. ``GIS_MCP_STORAGE_CONFIG`` environment variable (JSON)
    3. Discrete GCP env vars (``GIS_MCP_STORAGE_PROVIDER=gcp``, ...)
    4. ``GIS_MCP_STORAGE_PATH`` / plain path string (local)
    """
    if storage_config is not None:
        return storage_config

    env_json = os.getenv("GIS_MCP_STORAGE_CONFIG")
    if env_json:
        return env_json

    provider = (os.getenv("GIS_MCP_STORAGE_PROVIDER") or "").lower().strip()
    if provider in ("gcp", "gcs", "google", "google_cloud_storage"):
        bucket = os.getenv("GIS_MCP_GCS_BUCKET") or os.getenv("GIS_MCP_GCP_BUCKET")
        if not bucket:
            raise ValueError(
                "GIS_MCP_STORAGE_PROVIDER=gcp requires GIS_MCP_GCS_BUCKET "
                "(or GIS_MCP_GCP_BUCKET) to be set"
            )
        cfg: Dict[str, Any] = {
            "provider": "gcp",
            "bucket": bucket,
            "prefix": os.getenv("GIS_MCP_GCS_PREFIX")
            or os.getenv("GIS_MCP_GCP_PREFIX")
            or "",
        }
        creds = (
            os.getenv("GIS_MCP_GCS_CREDENTIALS")
            or os.getenv("GIS_MCP_GCP_CREDENTIALS")
        )
        if creds:
            cfg["credentials"] = creds
        project = os.getenv("GIS_MCP_GCS_PROJECT") or os.getenv("GIS_MCP_GCP_PROJECT")
        if project:
            cfg["project"] = project
        return cfg

    env_path = os.getenv("GIS_MCP_STORAGE_PATH")
    if env_path:
        return env_path

    return None


def initialize_storage(
    storage_config: Optional[Union[str, Dict[str, Any]]] = None,
) -> Path:
    """
    Initialize the storage configuration.

    Args:
        storage_config: One of:
            - None: use env vars or default local path
            - str path: local filesystem (``--storage-path`` behavior)
            - JSON str / dict with ``"provider": "local"|"gcp"``

    Returns:
        Path to the local storage root (or local cache for cloud backends)
    """
    global _storage_adapter, _storage_path

    resolved = _load_config_from_env_and_args(storage_config)
    adapter = create_storage_adapter(resolved)

    _storage_adapter = adapter
    _storage_path = adapter.get_local_root()
    return _storage_path


def get_storage_adapter() -> StorageAdapter:
    """
    Get the active storage adapter.

    Initializes default local storage if not already initialized.
    """
    global _storage_adapter, _storage_path

    if _storage_adapter is None:
        initialize_storage()
    assert _storage_adapter is not None
    return _storage_adapter


def get_storage_path() -> Path:
    """
    Get the current local storage path.

    For cloud backends this is the local cache directory used by GIS tools.
    If not initialized, initializes with the default path.
    """
    global _storage_path

    if _storage_path is None:
        initialize_storage()
    assert _storage_path is not None
    return _storage_path


def resolve_path(file_path: str, relative_to_storage: bool = True) -> Path:
    """
    Resolve a file path, optionally making it relative to the storage directory.

    If the path is absolute, it's used as-is. If relative and relative_to_storage
    is True, it's resolved relative to the storage directory (or GCP local cache).
    """
    return get_storage_adapter().resolve_local_path(
        file_path, relative_to_storage=relative_to_storage
    )


def parse_storage_config_arg(value: Optional[str]) -> Optional[Union[str, Dict[str, Any]]]:
    """
    Parse a CLI ``--storage-config`` value.

    Accepts a JSON object string or a path to a JSON file. Returns None if empty.
    """
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text.startswith("{"):
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("--storage-config JSON must be an object")
        return parsed
    path = Path(text).expanduser()
    if path.is_file():
        with path.open("r", encoding="utf-8") as fh:
            parsed = json.load(fh)
        if not isinstance(parsed, dict):
            raise ValueError("storage config file must contain a JSON object")
        return parsed
    raise ValueError(
        f"--storage-config must be a JSON object or path to a JSON file: {value}"
    )


# Re-export for convenience / typing
__all__ = [
    "get_default_storage_path",
    "initialize_storage",
    "get_storage_adapter",
    "get_storage_path",
    "resolve_path",
    "parse_storage_config_arg",
    "StorageAdapter",
    "LocalStorageAdapter",
]
