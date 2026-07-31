"""Factory for creating storage adapters from configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .base import StorageAdapter
from .local import LocalStorageAdapter


def _as_dict(config: Union[str, Dict[str, Any], Path, None]) -> Optional[Dict[str, Any]]:
    """Normalize config input into a dict, or None for default local storage."""
    if config is None:
        return None

    if isinstance(config, dict):
        return config

    if isinstance(config, Path):
        config = str(config)

    if isinstance(config, str):
        text = config.strip()
        if not text:
            return None
        # JSON object → structured storage config
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid storage_config JSON: {exc}"
                ) from exc
            if not isinstance(parsed, dict):
                raise ValueError("storage_config JSON must be an object")
            return parsed
        # Plain path string → local filesystem (backward compatible)
        return {"provider": "local", "path": text}

    raise TypeError(f"Unsupported storage_config type: {type(config)!r}")


def create_storage_adapter(
    config: Union[str, Dict[str, Any], Path, None] = None,
) -> StorageAdapter:
    """
    Create a storage adapter from configuration.

    Supported forms:
    - None → default local path (~/.gis_mcp/data/)
    - "/some/path" or {"provider": "local", "path": "..."} → local filesystem
    - {"provider": "gcp", "bucket": "...", "prefix": "...", ...} → GCS
    """
    cfg = _as_dict(config)
    if cfg is None:
        return LocalStorageAdapter()

    provider = str(cfg.get("provider", "local")).lower().strip()

    if provider in ("local", "filesystem", "fs"):
        path = cfg.get("path") or cfg.get("storage_path")
        return LocalStorageAdapter(Path(path) if path else None)

    if provider in ("gcp", "gcs", "google", "google_cloud_storage"):
        from .gcp import GCPStorageAdapter

        bucket = cfg.get("bucket") or cfg.get("bucket_name")
        if not bucket:
            raise ValueError(
                "GCP storage_config requires a 'bucket' field, e.g. "
                '{"provider": "gcp", "bucket": "my-bucket"}'
            )
        return GCPStorageAdapter(
            bucket=str(bucket),
            prefix=str(cfg.get("prefix", "") or ""),
            credentials=cfg.get("credentials")
            or cfg.get("credentials_path")
            or cfg.get("key_file"),
            project=cfg.get("project"),
            local_cache=Path(cfg["local_cache"]) if cfg.get("local_cache") else None,
        )

    raise ValueError(
        f"Unsupported storage provider: {provider!r}. "
        'Supported providers: "local", "gcp".'
    )
