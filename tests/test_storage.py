"""Tests for local storage configuration and adapters."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gis_mcp.storage.factory import create_storage_adapter
from gis_mcp.storage.local import LocalStorageAdapter
from gis_mcp import storage_config


@pytest.fixture(autouse=True)
def reset_storage_globals():
    """Reset module-level storage state between tests."""
    storage_config._storage_adapter = None
    storage_config._storage_path = None
    yield
    storage_config._storage_adapter = None
    storage_config._storage_path = None


@pytest.fixture
def local_root(tmp_path):
    return tmp_path / "storage"


class TestLocalStorageAdapter:
    def test_write_read_roundtrip(self, local_root):
        adapter = LocalStorageAdapter(local_root)
        path = adapter.write_bytes("outputs/hello.txt", b"hello")
        assert path == "outputs/hello.txt"
        assert adapter.read_bytes("outputs/hello.txt") == b"hello"
        assert adapter.is_file("outputs/hello.txt")
        assert adapter.exists("outputs")

    def test_list_dir(self, local_root):
        adapter = LocalStorageAdapter(local_root)
        adapter.write_bytes("a.txt", b"a")
        adapter.ensure_dir("subdir")
        adapter.write_bytes("subdir/b.txt", b"b")

        entries = adapter.list_dir("")
        names = {e.name: e.type for e in entries}
        assert names["a.txt"] == "file"
        assert names["subdir"] == "directory"

    def test_resolve_local_path(self, local_root):
        adapter = LocalStorageAdapter(local_root)
        resolved = adapter.resolve_local_path("foo/bar.tif")
        assert resolved == (local_root.resolve() / "foo" / "bar.tif")


class TestCreateStorageAdapter:
    def test_default_is_local(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        adapter = create_storage_adapter(None)
        assert isinstance(adapter, LocalStorageAdapter)
        assert adapter.provider == "local"

    def test_plain_path_string(self, local_root):
        adapter = create_storage_adapter(str(local_root))
        assert isinstance(adapter, LocalStorageAdapter)
        assert adapter.get_local_root() == local_root.resolve()

    def test_local_dict_config(self, local_root):
        adapter = create_storage_adapter({"provider": "local", "path": str(local_root)})
        assert isinstance(adapter, LocalStorageAdapter)

    def test_json_string_local(self, local_root):
        cfg = json.dumps({"provider": "local", "path": str(local_root)})
        adapter = create_storage_adapter(cfg)
        assert isinstance(adapter, LocalStorageAdapter)

    def test_unsupported_provider(self):
        with pytest.raises(ValueError, match="Unsupported storage provider"):
            create_storage_adapter({"provider": "azure"})


class TestInitializeStorage:
    def test_local_path_backward_compatible(self, local_root):
        path = storage_config.initialize_storage(str(local_root))
        assert path == local_root.resolve()
        assert storage_config.get_storage_path() == path
        assert storage_config.get_storage_adapter().provider == "local"

    def test_storage_config_env_json(self, local_root, monkeypatch):
        monkeypatch.setenv(
            "GIS_MCP_STORAGE_CONFIG",
            json.dumps({"provider": "local", "path": str(local_root)}),
        )
        path = storage_config.initialize_storage(None)
        assert path == local_root.resolve()

    def test_resolve_path_uses_storage(self, local_root):
        storage_config.initialize_storage(str(local_root))
        resolved = storage_config.resolve_path("out/file.tif")
        assert resolved == (local_root.resolve() / "out" / "file.tif")

    def test_parse_storage_config_arg_json(self):
        cfg = storage_config.parse_storage_config_arg(
            '{"provider":"local","path":"/tmp/x"}'
        )
        assert cfg == {"provider": "local", "path": "/tmp/x"}

    def test_parse_storage_config_arg_file(self, tmp_path):
        cfg_file = tmp_path / "storage.json"
        cfg_file.write_text('{"provider":"local","path":"/tmp/x"}')
        cfg = storage_config.parse_storage_config_arg(str(cfg_file))
        assert cfg["provider"] == "local"
