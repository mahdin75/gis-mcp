"""Google Cloud Storage adapter."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from .base import StorageAdapter, StorageEntry

logger = logging.getLogger("gis-mcp")


class GCPStorageAdapter(StorageAdapter):
    """
    Store files in a Google Cloud Storage bucket.

    A local cache under ``~/.gis_mcp/gcp_cache/<bucket>/`` is used so GIS
    libraries that require real filesystem paths continue to work. Storage
    HTTP endpoints read and write the bucket directly.
    """

    provider = "gcp"

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        credentials: Optional[Union[str, Path]] = None,
        project: Optional[str] = None,
        local_cache: Optional[Path] = None,
        client=None,
    ):
        if not bucket:
            raise ValueError("GCP storage requires a non-empty 'bucket' value")

        self.bucket_name = bucket
        self.prefix = self._normalize_prefix(prefix)
        self.credentials_path = (
            str(Path(credentials).expanduser()) if credentials else None
        )
        self.project = project

        if client is not None:
            self._client = client
        else:
            try:
                from google.cloud import storage as gcs  # type: ignore
            except ImportError as exc:
                raise ImportError(
                    "google-cloud-storage is required for GCP storage. "
                    "Install with: pip install gis-mcp[gcp]"
                ) from exc
            self._client = self._build_client(gcs)

        self._bucket = self._client.bucket(self.bucket_name)

        if local_cache is None:
            local_cache = (
                Path.home() / ".gis_mcp" / "gcp_cache" / self.bucket_name
            )
        self._local_root = Path(local_cache).expanduser().resolve()
        self._local_root.mkdir(parents=True, exist_ok=True)

        logger.info(
            "GCP storage initialized: gs://%s/%s (cache: %s)",
            self.bucket_name,
            self.prefix,
            self._local_root,
        )

    @staticmethod
    def _normalize_prefix(prefix: str) -> str:
        prefix = (prefix or "").replace("\\", "/").lstrip("/")
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        return prefix

    def _build_client(self, gcs_module):
        """
        Build a GCS client using (in order):
        1. Explicit credentials key file from config
        2. GOOGLE_APPLICATION_CREDENTIALS / Application Default Credentials
        """
        if self.credentials_path:
            if not Path(self.credentials_path).is_file():
                raise FileNotFoundError(
                    f"GCP credentials file not found: {self.credentials_path}"
                )
            return gcs_module.Client.from_service_account_json(
                self.credentials_path,
                project=self.project,
            )

        # Env var GOOGLE_APPLICATION_CREDENTIALS or other ADC sources
        env_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if env_creds:
            logger.debug(
                "Using GOOGLE_APPLICATION_CREDENTIALS=%s", env_creds
            )
        return gcs_module.Client(project=self.project)

    def get_local_root(self) -> Path:
        return self._local_root

    def _blob_name(self, path: str) -> str:
        clean = str(path or "").lstrip("/").replace("\\", "/")
        return f"{self.prefix}{clean}" if clean else self.prefix.rstrip("/")

    def _local_path(self, path: str) -> Path:
        clean = str(path or "").lstrip("/").replace("\\", "/")
        if not clean:
            return self._local_root
        return (self._local_root / clean).resolve()

    def write_bytes(self, path: str, data: bytes) -> str:
        clean = str(path).lstrip("/").replace("\\", "/")
        blob = self._bucket.blob(self._blob_name(clean))
        blob.upload_from_string(data)

        # Keep local cache in sync for GIS tool usage
        local = self._local_path(clean)
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        return clean

    def read_bytes(self, path: str) -> bytes:
        clean = str(path).lstrip("/").replace("\\", "/")
        blob = self._bucket.blob(self._blob_name(clean))
        if not blob.exists():
            raise FileNotFoundError(f"File not found in GCS: {clean}")
        data = blob.download_as_bytes()

        local = self._local_path(clean)
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        return data

    def exists(self, path: str = "") -> bool:
        clean = str(path or "").lstrip("/").replace("\\", "/")
        if not clean:
            return True

        blob_name = self._blob_name(clean)
        blob = self._bucket.blob(blob_name)
        if blob.exists():
            return True

        # Treat prefix as a directory if any objects exist under it
        prefix = blob_name if blob_name.endswith("/") else f"{blob_name}/"
        return any(self._client.list_blobs(self.bucket_name, prefix=prefix, max_results=1))

    def is_file(self, path: str) -> bool:
        clean = str(path).lstrip("/").replace("\\", "/")
        if not clean:
            return False
        return self._bucket.blob(self._blob_name(clean)).exists()

    def is_dir(self, path: str = "") -> bool:
        clean = str(path or "").lstrip("/").replace("\\", "/")
        if not clean:
            return True
        if self.is_file(clean):
            return False
        prefix = self._blob_name(clean)
        if not prefix.endswith("/"):
            prefix += "/"
        return any(
            self._client.list_blobs(self.bucket_name, prefix=prefix, max_results=1)
        )

    def ensure_dir(self, path: str) -> None:
        # GCS has no real directories; ensure local cache dir exists.
        self._local_path(path).mkdir(parents=True, exist_ok=True)

    def list_dir(self, path: str = "") -> List[StorageEntry]:
        clean = str(path or "").lstrip("/").replace("\\", "/")

        if clean and self.is_file(clean):
            blob = self._bucket.blob(self._blob_name(clean))
            blob.reload()
            return [
                StorageEntry(
                    name=Path(clean).name,
                    path=clean,
                    type="file",
                    size=blob.size,
                    modified=blob.updated.timestamp() if blob.updated else None,
                )
            ]

        if clean and not self.exists(clean):
            raise FileNotFoundError(f"Path not found: {clean or 'root'}")

        list_prefix = self._blob_name(clean)
        if list_prefix and not list_prefix.endswith("/"):
            list_prefix += "/"
        # Empty path with empty prefix → list from bucket root / configured prefix
        if not clean:
            list_prefix = self.prefix

        iterator = self._client.list_blobs(
            self.bucket_name,
            prefix=list_prefix,
            delimiter="/",
        )
        # Consume iterator so prefixes (directories) are populated
        blobs = list(iterator)
        prefixes = list(iterator.prefixes) if iterator.prefixes else []

        entries: List[StorageEntry] = []
        seen_names = set()

        for prefix in prefixes:
            # Strip storage prefix and list prefix to get relative directory name
            relative = prefix
            if self.prefix and relative.startswith(self.prefix):
                relative = relative[len(self.prefix) :]
            relative = relative.rstrip("/")
            if clean:
                # Child relative to requested path
                if relative.startswith(clean + "/"):
                    name = relative[len(clean) + 1 :].split("/")[0]
                elif relative == clean:
                    continue
                else:
                    name = relative.split("/")[-1]
            else:
                name = relative.split("/")[0] if relative else ""
            if not name or name in seen_names:
                continue
            child_path = f"{clean}/{name}" if clean else name
            entries.append(
                StorageEntry(
                    name=name,
                    path=child_path,
                    type="directory",
                    size=None,
                    modified=None,
                )
            )
            seen_names.add(name)

        for blob in blobs:
            name = blob.name
            if self.prefix and name.startswith(self.prefix):
                name = name[len(self.prefix) :]
            # Skip the directory placeholder itself
            if not name or name.endswith("/"):
                continue
            if clean:
                if not name.startswith(clean + "/"):
                    continue
                remainder = name[len(clean) + 1 :]
            else:
                remainder = name
            # Only immediate children
            if "/" in remainder:
                continue
            if not remainder or remainder in seen_names:
                continue
            child_path = f"{clean}/{remainder}" if clean else remainder
            entries.append(
                StorageEntry(
                    name=remainder,
                    path=child_path,
                    type="file",
                    size=blob.size,
                    modified=blob.updated.timestamp() if blob.updated else None,
                )
            )
            seen_names.add(remainder)

        entries.sort(key=lambda e: (e.type != "directory", e.name.lower()))
        return entries

    def describe(self) -> str:
        return f"gcp:gs://{self.bucket_name}/{self.prefix}"
