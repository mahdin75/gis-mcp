"""Tests for MCP catalog and payload token optimizations."""

import json
import os

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from fastmcp import Client
from rasterio.transform import from_bounds
from shapely.geometry import Point

# EPSG:4326 as WKT. Passing "EPSG:4326" to rasterio fails in some PROJ setups.
_WGS84_WKT = (
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,'
    'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,'
    'AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,'
    'AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
)

from gis_mcp.catalog import measure_catalog
from gis_mcp.compact import cap_sequence, vector_preview
from gis_mcp.gdf_cache import clear_cache, read_vector
from gis_mcp.mcp import gis_mcp
from gis_mcp.tool_groups import apply_module_filter, enabled_tool_names
from tests.test_helpers import get_result_data


def test_output_schemas_are_omitted():
    for tool in gis_mcp._tool_manager._tools.values():
        assert tool.output_schema is None


def test_descriptions_do_not_repeat_parameter_blocks():
    merge = gis_mcp._tool_manager._tools["merge_gpd"]
    assert "Args:" not in (merge.description or "")
    assert "join" in merge.description.lower()
    buffer = gis_mcp._tool_manager._tools["buffer"]
    assert "buffer" in buffer.description.lower()
    sjoin = gis_mcp._tool_manager._tools["sjoin_gpd"]
    assert "within" in sjoin.description


def test_catalog_has_no_empty_output_schema_or_meta():
    stats = measure_catalog(gis_mcp, include_fastmcp_meta=False)
    assert stats["tool_count"] >= 87
    assert stats["output_schema_chars"] == 0
    assert stats["meta_chars"] == 0
    assert stats["description_chars"] < 14643


def test_module_filter_hides_groups_and_restores_them():
    previous_include = gis_mcp.include_tags
    previous_exclude = gis_mcp.exclude_tags
    try:
        apply_module_filter(gis_mcp, modules="geometry", exclude="")
        names = set(enabled_tool_names(gis_mcp))
        assert "buffer" in names
        assert "morans_i" not in names
        assert "read_file_gpd" not in names
    finally:
        gis_mcp.include_tags = previous_include
        gis_mcp.exclude_tags = previous_exclude


def test_cap_sequence_keeps_short_lists_and_summarizes_long_ones():
    assert cap_sequence([1, 2, 3], limit=10) == [1, 2, 3]
    capped = cap_sequence(range(150), limit=10)
    assert capped["truncated"] is True
    assert capped["count"] == 150
    assert len(capped["head"]) == 10


def test_vector_preview_omits_geometry_until_requested():
    gdf = gpd.GeoDataFrame(
        {"name": ["A", "B"], "value": [1.23456789, 2]},
        geometry=[Point(0, 0), Point(1, 1)],
        crs="EPSG:4326",
    )
    page = vector_preview(gdf, max_features=1, include_geometry=False, precision=2)
    assert page["truncated"] is True
    assert "geometry" not in page["preview"][0]
    assert page["preview"][0]["value"] == 1.23
    full = vector_preview(gdf, precision=2)
    assert "POINT" in full["preview"][0]["geometry"]


def test_read_vector_uses_the_cache(sample_geodataframe):
    _, path = sample_geodataframe
    calls = {"n": 0}
    original = gpd.read_file

    def wrapped(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    gpd.read_file = wrapped
    try:
        clear_cache()
        first = read_vector(path)
        second = read_vector(path)
        assert len(first) == len(second) == 3
        assert calls["n"] == 1
    finally:
        gpd.read_file = original
        clear_cache()


@pytest.mark.asyncio
async def test_read_file_preview_is_compact(sample_geodataframe):
    _, path = sample_geodataframe
    async with Client(gis_mcp) as client:
        result = await client.call_tool(
            "read_file_gpd",
            {"file_path": path, "max_features": 1, "include_geometry": False},
        )
        data = get_result_data(result)
        assert data["status"] == "success"
        assert data["num_rows"] == 3
        assert data["returned"] == 1
        assert data["truncated"] is True
        assert "geometry" not in data["preview"][0]
        assert "message" in data

        default = await client.call_tool("read_file_gpd", {"file_path": path})
        default_data = get_result_data(default)
        assert "POINT" in default_data["preview"][0]["geometry"]

        with_geom = await client.call_tool(
            "read_file_gpd",
            {"file_path": path, "include_geometry": True, "columns": "name"},
        )
        geom_data = get_result_data(with_geom)
        assert set(geom_data["preview"][0]) == {"name", "geometry"}


@pytest.mark.asyncio
async def test_available_crs_is_capped():
    async with Client(gis_mcp) as client:
        result = await client.call_tool("get_available_crs", {})
        data = get_result_data(result)
        assert data["status"] == "success"
        assert "message" in data
        assert 0 < len(data["crs_list"]) <= 100


@pytest.mark.asyncio
async def test_tool_result_is_not_duplicated_as_structured_content():
    previous = os.environ.get("GIS_MCP_STRUCTURED_CONTENT")
    os.environ["GIS_MCP_STRUCTURED_CONTENT"] = "0"
    try:
        async with Client(gis_mcp) as client:
            raw = await client.call_tool_mcp(
                "buffer",
                {"geometry": "POINT (0 0)", "distance": 1},
            )
            assert raw.structuredContent is None
            parsed = json.loads(raw.content[0].text)
            assert parsed["status"] == "success"
            assert "geometry" in parsed
    finally:
        if previous is None:
            os.environ.pop("GIS_MCP_STRUCTURED_CONTENT", None)
        else:
            os.environ["GIS_MCP_STRUCTURED_CONTENT"] = previous


@pytest.mark.asyncio
async def test_histogram_compact_caps_bins(temp_dir):
    path = os.path.join(temp_dir, "hist.tif")
    data = np.arange(100, dtype=np.uint8).reshape(1, 10, 10)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs=_WGS84_WKT,
        transform=from_bounds(0, 0, 10, 10, 10, 10),
    ) as dst:
        dst.write(data)
    async with Client(gis_mcp) as client:
        result = await client.call_tool(
            "raster_histogram",
            {"source": path, "bins": 256, "compact": True},
        )
        data = get_result_data(result)
        band = data["histograms"]["Band 1"]
        assert band["bins"] <= 32
        assert len(band["histogram"]) <= 32
