"""Small mtime-keyed cache for repeated vector reads in one server process."""

from __future__ import annotations

import os
from collections import OrderedDict
from typing import Any

_CACHE: "OrderedDict[tuple, Any]" = OrderedDict()
_MAX_ENTRIES = 16


def clear_cache() -> None:
    _CACHE.clear()


def read_vector(path: str) -> Any:
    """Read a vector file, reusing the previous GeoDataFrame when the file is unchanged."""
    import geopandas as gpd

    stat = os.stat(path)
    key = (os.path.abspath(path), stat.st_mtime_ns, stat.st_size)
    cached = _CACHE.get(key)
    if cached is not None:
        _CACHE.move_to_end(key)
        return cached.copy()

    gdf = gpd.read_file(path)
    _CACHE[key] = gdf
    while len(_CACHE) > _MAX_ENTRIES:
        _CACHE.popitem(last=False)
    return gdf.copy()
