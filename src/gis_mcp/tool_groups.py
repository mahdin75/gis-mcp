"""Tool groups for server-side MCP catalog filtering.

Tags are not sent to clients. ``include_fastmcp_meta`` is disabled so an
empty ``_fastmcp.tags`` object is not added to every tool. Filtering uses
FastMCP's include_tags / exclude_tags, which run before tools/list.
"""

from __future__ import annotations

import logging
import os
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

GEOMETRY = {
    "buffer",
    "intersection",
    "union",
    "difference",
    "symmetric_difference",
    "convex_hull",
    "envelope",
    "minimum_rotated_rectangle",
    "get_centroid",
    "get_bounds",
    "get_coordinates",
    "get_geometry_type",
    "rotate_geometry",
    "scale_geometry",
    "translate_geometry",
    "triangulate_geometry",
    "voronoi",
    "unary_union_geometries",
    "get_length",
    "get_area",
    "is_valid",
    "make_valid",
    "simplify",
    "snap_geometry",
    "nearest_point_on_geometry",
    "normalize_geometry",
    "geometry_to_geojson",
    "geojson_to_geometry",
}

VECTOR = {
    "read_file_gpd",
    "append_gpd",
    "merge_gpd",
    "overlay_gpd",
    "dissolve_gpd",
    "explode_gpd",
    "clip_vector",
    "sjoin_gpd",
    "sjoin_nearest_gpd",
    "point_in_polygon",
    "write_file_gpd",
}

RASTER = {
    "zonal_statistics",
    "reclassify_raster",
    "focal_statistics",
    "hillshade",
    "write_raster",
    "metadata_raster",
    "get_raster_crs",
    "clip_raster_with_shapefile",
    "resample_raster",
    "reproject_raster",
    "extract_band",
    "raster_band_statistics",
    "tile_raster",
    "raster_histogram",
    "compute_ndvi",
    "raster_algebra",
    "concat_bands",
    "weighted_band_sum",
}

CRS = {
    "transform_coordinates",
    "project_geometry",
    "get_crs_info",
    "get_available_crs",
    "get_geod_info",
    "calculate_geodetic_distance",
    "calculate_geodetic_point",
    "calculate_geodetic_area",
    "get_utm_zone",
    "get_utm_crs",
    "get_geocentric_crs",
}

STATISTICS = {
    "getis_ord_g",
    "morans_i",
    "gearys_c",
    "gamma_statistic",
    "moran_local",
    "getis_ord_g_local",
    "join_counts",
    "join_counts_local",
    "adbscan",
    "weights_from_shapefile",
    "distance_band_weights",
    "knn_weights",
    "build_transform_and_save_weights",
    "ols_with_spatial_diagnostics_safe",
    "build_and_transform_weights",
    "spatial_markov",
    "dynamic_lisa",
    "gm_lag",
}

IO = {"save_results"}
VISUALIZE = {"create_map", "create_web_map"}
BOUNDARIES = {"download_boundaries"}
CLIMATE = {"download_climate_data"}
ECOLOGY = {"get_species_info", "download_species_occurrences"}
MOVEMENT = {"download_street_network", "calculate_shortest_path"}
SATELLITE = {"download_satellite_imagery"}
LANDCOVER = {"download_worldcover", "compute_s2_ndvi"}

GROUPS = {
    "geometry": GEOMETRY,
    "vector": VECTOR,
    "raster": RASTER,
    "crs": CRS,
    "statistics": STATISTICS,
    "io": IO,
    "visualize": VISUALIZE,
    "boundaries": BOUNDARIES,
    "climate": CLIMATE,
    "ecology": ECOLOGY,
    "movement": MOVEMENT,
    "satellite": SATELLITE,
    "landcover": LANDCOVER,
}

RESOURCE_GROUPS = {
    "gis://operations/basic": "geometry",
    "gis://operations/geometric": "geometry",
    "gis://operations/transformations": "geometry",
    "gis://operations/advanced": "geometry",
    "gis://operations/measurements": "geometry",
    "gis://operations/validation": "geometry",
    "gis://operations/shapely_util": "geometry",
    "gis://geopandas/io": "vector",
    "gis://geopandas/joins": "vector",
    "gis://operation/rasterio": "raster",
    "gis://crs/transformations": "crs",
    "gis://crs/info": "crs",
    "gis://crs/geodetic": "crs",
    "gis://operations/esda": "statistics",
    "gis://operations/administrative_boundaries": "boundaries",
    "gis://operations/climate": "climate",
    "gis://operations/ecology": "ecology",
    "gis://operations/movement": "movement",
    "gis://operations/satellite_imagery": "satellite",
    "gis://operations/land_products": "landcover",
}


def _split(value: Optional[str]) -> list:
    if not value:
        return []
    return [part.strip().lower() for part in value.split(",") if part.strip()]


def known_groups() -> list:
    return list(GROUPS)


def apply_tags(mcp) -> None:
    membership = {}
    for group, names in GROUPS.items():
        for name in names:
            membership.setdefault(name, set()).add(group)

    for name, tool in mcp._tool_manager._tools.items():
        groups = membership.get(name)
        if groups:
            tool.tags = set(tool.tags) | groups
        elif "ungrouped" not in tool.tags:
            tool.tags = set(tool.tags) | {"ungrouped"}
            logger.warning("Tool %s is not in a catalog group", name)

    manager = getattr(mcp, "_resource_manager", None)
    resources = getattr(manager, "_resources", None) if manager is not None else None
    if not isinstance(resources, dict):
        return
    for key, resource in resources.items():
        uri = str(getattr(resource, "uri", None) or key)
        group = RESOURCE_GROUPS.get(uri) or RESOURCE_GROUPS.get(key)
        if group:
            resource.tags = set(resource.tags) | {group}


def apply_module_filter(
    mcp,
    modules: Optional[str] = None,
    exclude: Optional[str] = None,
) -> None:
    """Show a subset of tools. ``all`` or empty keeps the full catalog.

    This only affects the running server. Clients that already cached
    tools/list need to reconnect.
    """
    if modules is None:
        modules = os.getenv("GIS_MCP_MODULES", "all")
    if exclude is None:
        exclude = os.getenv("GIS_MCP_EXCLUDE", "")

    selected = _split(modules)
    excluded = _split(exclude)
    valid = set(GROUPS)

    if not selected or selected == ["all"] or selected == ["*"]:
        mcp.include_tags = None
    else:
        unknown = [name for name in selected if name not in valid]
        if unknown:
            logger.warning("Unknown GIS_MCP_MODULES entries ignored: %s", ", ".join(unknown))
        mcp.include_tags = {name for name in selected if name in valid} or None

    if not excluded:
        mcp.exclude_tags = None
    else:
        unknown = [name for name in excluded if name not in valid]
        if unknown:
            logger.warning("Unknown GIS_MCP_EXCLUDE entries ignored: %s", ", ".join(unknown))
        mcp.exclude_tags = {name for name in excluded if name in valid} or None


def enabled_tool_names(mcp) -> Iterable[str]:
    for tool in mcp._tool_manager._tools.values():
        if mcp._should_enable_component(tool):
            yield tool.name
