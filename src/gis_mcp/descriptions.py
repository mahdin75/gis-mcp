"""Concise MCP descriptions.

FastMCP publishes the function docstring as the tool description. These
overrides replace the long docstrings in the catalog sent to clients.
The one-line text still names the operation and any enum the model must
choose. Parameter names and types stay in the JSON schema.
"""

from __future__ import annotations

DESCRIPTIONS = {
    "read_file_gpd": "Summarize a vector file: row count, columns, CRS, bounds, and a 5-row preview that includes WKT. Pass include_geometry=false to omit geometry.",
    "append_gpd": "Vertically concatenate two vector files and save a shapefile.",
    "merge_gpd": "Attribute join of two vector files. Keeps the first file's geometry and uses an inner join on shared column names.",
    "overlay_gpd": "Spatial overlay of two vector files. how is intersection, union, identity, symmetric_difference, or difference.",
    "dissolve_gpd": "Dissolve vector features, optionally grouped by one attribute column.",
    "explode_gpd": "Split multi-part geometries into single-part features.",
    "clip_vector": "Clip vector features to the polygon extent of another vector file.",
    "sjoin_gpd": "Spatial join of two vector files. how is left, right, or inner. predicate is intersects, within, contains, crosses, overlaps, or touches.",
    "sjoin_nearest_gpd": "Join each feature to the nearest feature in another file. Optional max_distance is in CRS units.",
    "point_in_polygon": "Assign each point the attributes of the polygon that contains it.",
    "write_file_gpd": "Export a vector file to another path. driver may be ESRI Shapefile, GeoJSON, or GPKG.",
    "zonal_statistics": "Summarize raster values inside each polygon. stats can include mean, min, max, std, and count.",
    "reclassify_raster": "Replace raster cell values using a mapping of old value to new value and save the raster.",
    "focal_statistics": "Moving-window statistic on a raster. statistic is mean, min, max, or std. size is the window width in pixels.",
    "hillshade": "Create a hillshade raster from an elevation raster.",
    "write_raster": "Write a 2D array as a raster using the grid of a reference raster.",
    "metadata_raster": "Raster grid metadata: size, band count, dtype, nodata, CRS, bounds, and affine transform. Accepts a local path or HTTPS URL.",
    "get_raster_crs": "Raster CRS as a PROJ dict and WKT. Accepts a local path or HTTPS URL.",
    "clip_raster_with_shapefile": "Clip a raster to shapefile polygons and save it. The shapefile is reprojected to the raster CRS when needed.",
    "resample_raster": "Resample a raster by a scale factor and save the result.",
    "reproject_raster": "Reproject a raster to a target CRS and save the result.",
    "extract_band": "Extract one band by index and save a single-band raster.",
    "raster_band_statistics": "Min, max, mean, and standard deviation for each raster band.",
    "tile_raster": "Split a raster into square tiles of tile_size pixels and save them.",
    "raster_histogram": "Per-band histogram of pixel values. The default uses the requested bins. compact=true returns at most 32 bins.",
    "compute_ndvi": "Compute NDVI from red and near-infrared band indexes and save a GeoTIFF.",
    "raster_algebra": "Add or subtract two raster bands and save the result.",
    "concat_bands": "Stack single-band rasters into one multi-band raster.",
    "weighted_band_sum": "Weighted sum of raster bands, saved as one band.",
    "get_available_crs": "List EPSG coordinate reference systems, 100 by default, same as before. query filters by code or name. limit caps the list.",
    "weights_from_shapefile": "Build queen or rook contiguity weights. Returns a neighbor summary, not the full weights matrix.",
    "distance_band_weights": "Build distance-band spatial weights from point coordinates. threshold is in CRS units.",
    "knn_weights": "Build k-nearest-neighbor spatial weights from point coordinates.",
    "build_transform_and_save_weights": "Build spatial weights, optionally transform them, and save a GAL or GWT file. method is queen, rook, distance_band, or knn.",
    "build_and_transform_weights": "Build and transform spatial weights in memory. method is queen, rook, distance_band, or knn.",
    "ols_with_spatial_diagnostics_safe": "Ordinary least squares with spatial diagnostics. weights_method is queen, rook, distance_band, or knn.",
    "gm_lag": "Spatial lag regression (GM/GMM). Returns coefficients, standard errors, and fit statistics.",
    "spatial_markov": "Spatial Markov transition matrix for a panel of regional values stored as columns.",
    "dynamic_lisa": "Directional LISA (Rose diagram) for a panel of regional values.",
    "moran_local": "Local Moran's I. Pass max_records to cap per-feature arrays.",
    "getis_ord_g_local": "Local Getis-Ord G. Pass max_records to cap per-feature arrays.",
    "join_counts_local": "Local join counts for a binary attribute. Pass max_records to cap the per-feature array.",
    "save_results": "Save a previous tool result dictionary to files under the storage folder.",
    "create_map": "Render a static map image from vector files, rasters, or WKT geometries.",
    "create_web_map": "Render an interactive HTML map from vector files or WKT geometries.",
    "download_satellite_imagery": "Download a low-cloud STAC scene from Planetary Computer and save a multi-band GeoTIFF.",
    "download_worldcover": "Download ESA WorldCover for an area and year and save a categorical GeoTIFF.",
    "compute_s2_ndvi": "Download Sentinel-2 L2A and save an NDVI GeoTIFF for an area and date range.",
    "download_climate_data": "Download an ERA5 climate variable from CDS and save NetCDF or GRIB.",
    "get_species_info": "Look up a species name in GBIF and return the backbone record. Pass full=false for a short taxonomy summary.",
    "download_species_occurrences": "Download GBIF occurrence records for a species and save them as JSON.",
    "download_boundaries": "Download GADM administrative boundaries as GeoJSON. level 0 is the country, 1 is states.",
    "download_street_network": "Download a street network with OSMnx and save GraphML. network_type is drive, walk, or bike.",
    "calculate_shortest_path": "Shortest path on a saved street network. origin and destination are (latitude, longitude). Pass max_nodes to cap the node list.",
    "get_coordinates": "List coordinates of a point or line. precision rounds values. max_coords and offset page long lines.",
}


def apply_descriptions(mcp) -> None:
    tools = mcp._tool_manager._tools
    for name, text in DESCRIPTIONS.items():
        tool = tools.get(name)
        if tool is not None:
            tool.description = text
