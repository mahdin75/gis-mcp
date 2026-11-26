"""GeoPandas-related MCP tool functions and resource listings."""
import os
import logging
from typing import Any, Dict, List, Optional
from .mcp import gis_mcp
from .storage_config import resolve_path
from .compact import vector_preview
from .gdf_cache import read_vector
import geopandas as gpd
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

@gis_mcp.resource("gis://geopandas/io")
def get_geopandas_io() -> Dict[str, List[str]]:
    """List available GeoPandas I/O operations."""
    return {
        "operations": [
            "read_file_gpd",
            "to_file_gpd",
            "overlay_gpd",
            "dissolve_gpd",
            "explode_gpd",
            "clip_vector",
            "write_file_gpd"
        ]
    }

@gis_mcp.resource("gis://geopandas/joins")
def get_geopandas_joins() -> Dict[str, List[str]]:
    """List available GeoPandas join operations."""
    return {
        "operations": [
            "append_gpd",
            "merge_gpd",
            "sjoin_gpd",
            "sjoin_nearest_gpd",
            "point_in_polygon"
        ]
    }

@gis_mcp.tool()
def read_file_gpd(
    file_path: str,
    max_features: int = 5,
    offset: int = 0,
    columns: Optional[str] = None,
    include_geometry: bool = True,
    precision: Optional[int] = None,
    bbox: Optional[str] = None,
    simplify: Optional[float] = None,
) -> Dict[str, Any]:
    """Summarize a vector file: row count, columns, CRS, bounds, and a short attribute preview."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        gdf = read_vector(file_path)
        page = vector_preview(
            gdf,
            max_features=max_features,
            offset=offset,
            columns=columns,
            include_geometry=include_geometry,
            precision=precision,
            bbox=bbox,
            simplify=simplify,
        )

        return {
            "status": "success",
            "columns": list(gdf.columns),
            "column_types": gdf.dtypes.astype(str).to_dict(),
            "num_rows": len(gdf),
            "num_columns": gdf.shape[1],
            "crs": str(gdf.crs),
            "bounds": gdf.total_bounds.tolist(),
            "preview": page["preview"],
            "returned": page["returned"],
            "offset": page["offset"],
            "matched": page["matched"],
            "truncated": page["truncated"],
            "message": f"File loaded successfully with {len(gdf)} rows and {gdf.shape[1]} columns",
        }

    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to read file: {str(e)}"
        }

@gis_mcp.tool()
def append_gpd(shapefile1_path: str, shapefile2_path: str, output_path: str) -> Dict[str, Any]:
    """ Reads two shapefiles directly, concatenates them vertically."""
    try:
        # Configure a basic logger for demonstration
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # Step 1: Read the two shapefiles into GeoDataFrames.
        logger.info(f"Reading {shapefile1_path}...")
        gdf1 = read_vector(shapefile1_path)
        
        logger.info(f"Reading {shapefile2_path}...")
        gdf2 = read_vector(shapefile2_path)

        # Step 2: Ensure the Coordinate Reference Systems (CRS) match.
        if gdf1.crs != gdf2.crs:
            logger.warning(
                f"CRS mismatch: GDF1 has '{gdf1.crs}' and GDF2 has '{gdf2.crs}'. "
                "Reprojecting GDF2."
            )
            gdf2 = gdf2.to_crs(gdf1.crs)

        # Step 3: Concatenate the two GeoDataFrames.
        combined_gdf = pd.concat([gdf1, gdf2], ignore_index=True)

        # Step 4: Save the combined GeoDataFrame to a new shapefile.
        output_path_resolved = resolve_path(output_path, relative_to_storage=True)
        output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving combined shapefile to {output_path_resolved}...")
        combined_gdf.to_file(str(output_path_resolved), driver='ESRI Shapefile')

        return {
            "status": "success",
            "message": f"Shapefiles concatenated successfully into '{output_path_resolved}'.",
            "info": {
                "output_path": str(output_path_resolved),
                "num_features": len(combined_gdf),
                "crs": str(combined_gdf.crs),
                "columns": list(combined_gdf.columns)
            }
        }
    
    except Exception as e:
        logger.error(f"Error processing shapefiles: {str(e)}")
        raise ValueError(f"Failed to process shapefiles: {str(e)}")

@gis_mcp.tool()
def merge_gpd(shapefile1_path: str, shapefile2_path: str, output_path: str) -> Dict[str, Any]:
    """ 
    Merges two shapefiles based on common attribute columns,
    This function performs a database-style join, not a spatial join.
    Args:
        left_shapefile_path: Path to the left shapefile. The geometry from this file is preserved.
        right_shapefile_path: Path to the right shapefile to merge.
        output_path: Path to save the merged output shapefile.
        how: Type of merge. One of 'left', 'right', 'outer', 'inner'. Defaults to 'inner'.
        on: Column name to join on. Must be found in both shapefiles.
        left_on: Column name to join on in the left shapefile.
        right_on: Column name to join on in the right shapefile.
        suffixes: Suffix to apply to overlapping column names.
    """
    try :
        # Step 1: Read the two shapefiles directly into GeoDataFrames.
        logger.info(f"Reading left shapefile: {shapefile1_path}...")
        left_gdf = read_vector(shapefile1_path)
        
        logger.info(f"Reading right shapefile: {shapefile2_path}...")
        # For an attribute join, we only need the attribute data from the right file.
        # We can drop its geometry column to make the merge cleaner and more memory-efficient.
        right_df = pd.DataFrame(read_vector(shapefile2_path).drop(columns='geometry'))

         # Step 2: Perform the merge operation using pandas.merge.
        # This function correctly handles the geometry of the left GeoDataFrame.
        logger.info(f"Performing merge...")
        merged_df = pd.merge(
            left_gdf,
            right_df,
            how='inner',  # Default to inner merge
            suffixes=('_left', '_right')
        )
        
        # Convert back to GeoDataFrame to preserve geometry and CRS
        merged_gdf = gpd.GeoDataFrame(merged_df, crs=left_gdf.crs)

        if merged_gdf.empty:
            logger.warning("The merge result is empty. No matching records were found.")

        # Step 3: Save the merged GeoDataFrame to a new shapefile.
        output_path_resolved = resolve_path(output_path, relative_to_storage=True)
        output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving merged shapefile to {output_path_resolved}...")
        merged_gdf.to_file(str(output_path_resolved), driver='ESRI Shapefile')

        return {
            "status": "success",
            "message": f"Shapefiles merged successfully into '{output_path_resolved}'.",
            "info": {
                "output_path": str(output_path_resolved),
                "merge_type": 'inner',
                "num_features": len(merged_gdf),
                "crs": str(merged_gdf.crs),
                "columns": list(merged_gdf.columns)
            }
        }
    except Exception as e:
        logger.error(f"Error merging shapefiles: {str(e)}")
        raise ValueError(f"Failed to merge shapefiles: {str(e)}")

@gis_mcp.tool()
def overlay_gpd(gdf1_path: str, gdf2_path: str, how: str = "intersection", output_path: str = None, max_features: int = 5, offset: int = 0, columns: Optional[str] = None, include_geometry: bool = True, precision: Optional[int] = None) -> Dict[str, Any]:
    """
    Overlay two GeoDataFrames using geopandas.overlay.
    Args:
        gdf1_path: Path to the first geospatial file.
        gdf2_path: Path to the second geospatial file.
        how: Overlay method ('intersection', 'union', 'identity', 'symmetric_difference', 'difference').
        output_path: Optional path to save the result.
    Returns:
        Dictionary with status, message, and output info.
    """
    try:
        gdf1 = read_vector(gdf1_path)
        gdf2 = read_vector(gdf2_path)
        if gdf1.crs != gdf2.crs:
            gdf2 = gdf2.to_crs(gdf1.crs)
        result = gpd.overlay(gdf1, gdf2, how=how)
        if output_path:
            output_path_resolved = resolve_path(output_path, relative_to_storage=True)
            output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            result.to_file(str(output_path_resolved))
            output_path = str(output_path_resolved)
        page = vector_preview(
            result,
            max_features=max_features,
            offset=offset,
            columns=columns,
            include_geometry=include_geometry,
            precision=precision,
        )
        preview = page["preview"]
        return {
            "status": "success",
            "message": f"Overlay ({how}) completed successfully.",
            "num_features": len(result),
            "crs": str(result.crs),
            "columns": list(result.columns),
            "preview": preview,
            "returned": page["returned"],
            "offset": page["offset"],
            "truncated": page["truncated"],
            "output_path": output_path,
        }
    except Exception as e:
        logger.error(f"Error in overlay_gpd: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def dissolve_gpd(gdf_path: str, by: str = None, output_path: str = None, max_features: int = 5, offset: int = 0, columns: Optional[str] = None, include_geometry: bool = True, precision: Optional[int] = None) -> Dict[str, Any]:
    """
    Dissolve geometries by attribute using geopandas.dissolve.
    Args:
        gdf_path: Path to the geospatial file.
        by: Column to dissolve by (optional).
        output_path: Optional path to save the result.
    Returns:
        Dictionary with status, message, and output info.
    """
    try:
        gdf = read_vector(gdf_path)
        result = gdf.dissolve(by=by)
        if output_path:
            output_path_resolved = resolve_path(output_path, relative_to_storage=True)
            output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            result.to_file(str(output_path_resolved))
            output_path = str(output_path_resolved)
        page = vector_preview(
            result,
            max_features=max_features,
            offset=offset,
            columns=columns,
            include_geometry=include_geometry,
            precision=precision,
        )
        preview = page["preview"]
        return {
            "status": "success",
            "message": f"Dissolve completed successfully.",
            "num_features": len(result),
            "crs": str(result.crs),
            "columns": list(result.columns),
            "preview": preview,
            "returned": page["returned"],
            "offset": page["offset"],
            "truncated": page["truncated"],
            "output_path": output_path,
        }
    except Exception as e:
        logger.error(f"Error in dissolve_gpd: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def explode_gpd(gdf_path: str, output_path: str = None, max_features: int = 5, offset: int = 0, columns: Optional[str] = None, include_geometry: bool = True, precision: Optional[int] = None) -> Dict[str, Any]:
    """
    Split multi-part geometries into single parts using geopandas.explode.
    Args:
        gdf_path: Path to the geospatial file.
        output_path: Optional path to save the result.
    Returns:
        Dictionary with status, message, and output info.
    """
    try:
        gdf = read_vector(gdf_path)
        result = gdf.explode(index_parts=True, ignore_index=True)
        if output_path:
            output_path_resolved = resolve_path(output_path, relative_to_storage=True)
            output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            result.to_file(str(output_path_resolved))
            output_path = str(output_path_resolved)
        page = vector_preview(
            result,
            max_features=max_features,
            offset=offset,
            columns=columns,
            include_geometry=include_geometry,
            precision=precision,
        )
        preview = page["preview"]
        return {
            "status": "success",
            "message": "Explode completed successfully.",
            "num_features": len(result),
            "crs": str(result.crs),
            "columns": list(result.columns),
            "preview": preview,
            "returned": page["returned"],
            "offset": page["offset"],
            "truncated": page["truncated"],
            "output_path": output_path,
        }
    except Exception as e:
        logger.error(f"Error in explode_gpd: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def clip_vector(gdf_path: str, clip_path: str, output_path: str = None, max_features: int = 5, offset: int = 0, columns: Optional[str] = None, include_geometry: bool = True, precision: Optional[int] = None) -> Dict[str, Any]:
    """
    Clip vector geometries using geopandas.clip.
    Args:
        gdf_path: Path to the input geospatial file.
        clip_path: Path to the clipping geometry file.
        output_path: Optional path to save the result.
    Returns:
        Dictionary with status, message, and output info.
    """
    try:
        gdf = read_vector(gdf_path)
        clip_gdf = read_vector(clip_path)
        if gdf.crs != clip_gdf.crs:
            clip_gdf = clip_gdf.to_crs(gdf.crs)
        result = gpd.clip(gdf, clip_gdf)
        if output_path:
            output_path_resolved = resolve_path(output_path, relative_to_storage=True)
            output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            result.to_file(str(output_path_resolved))
            output_path = str(output_path_resolved)
        page = vector_preview(
            result,
            max_features=max_features,
            offset=offset,
            columns=columns,
            include_geometry=include_geometry,
            precision=precision,
        )
        preview = page["preview"]
        return {
            "status": "success",
            "message": "Clip completed successfully.",
            "num_features": len(result),
            "crs": str(result.crs),
            "columns": list(result.columns),
            "preview": preview,
            "returned": page["returned"],
            "offset": page["offset"],
            "truncated": page["truncated"],
            "output_path": output_path,
        }
    except Exception as e:
        logger.error(f"Error in clip_vector: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def sjoin_gpd(left_path: str, right_path: str, how: str = "inner", predicate: str = "intersects", output_path: str = None, max_features: int = 5, offset: int = 0, columns: Optional[str] = None, include_geometry: bool = True, precision: Optional[int] = None) -> Dict[str, Any]:
    """
    Spatial join between two GeoDataFrames using geopandas.sjoin.
    Args:
        left_path: Path to the left geospatial file.
        right_path: Path to the right geospatial file.
        how: Type of join ('left', 'right', 'inner').
        predicate: Spatial predicate ('intersects', 'within', 'contains', etc.).
        output_path: Optional path to save the result.
    Returns:
        Dictionary with status, message, and output info.
    """
    try:
        left = read_vector(left_path)
        right = read_vector(right_path)
        if left.crs != right.crs:
            right = right.to_crs(left.crs)
        result = gpd.sjoin(left, right, how=how, predicate=predicate)
        if output_path:
            output_path_resolved = resolve_path(output_path, relative_to_storage=True)
            output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            result.to_file(str(output_path_resolved))
            output_path = str(output_path_resolved)
        page = vector_preview(
            result,
            max_features=max_features,
            offset=offset,
            columns=columns,
            include_geometry=include_geometry,
            precision=precision,
        )
        preview = page["preview"]
        return {
            "status": "success",
            "message": f"Spatial join ({how}, {predicate}) completed successfully.",
            "num_features": len(result),
            "crs": str(result.crs),
            "columns": list(result.columns),
            "preview": preview,
            "returned": page["returned"],
            "offset": page["offset"],
            "truncated": page["truncated"],
            "output_path": output_path,
        }
    except Exception as e:
        logger.error(f"Error in sjoin_gpd: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def sjoin_nearest_gpd(left_path: str, right_path: str, how: str = "left", max_distance: float = None, output_path: str = None, max_features: int = 5, offset: int = 0, columns: Optional[str] = None, include_geometry: bool = True, precision: Optional[int] = None) -> Dict[str, Any]:
    """
    Nearest neighbor spatial join using geopandas.sjoin_nearest.
    Args:
        left_path: Path to the left geospatial file.
        right_path: Path to the right geospatial file.
        how: Type of join ('left', 'right').
        max_distance: Optional maximum search distance.
        output_path: Optional path to save the result.
    Returns:
        Dictionary with status, message, and output info.
    """
    try:
        left = read_vector(left_path)
        right = read_vector(right_path)
        if left.crs != right.crs:
            right = right.to_crs(left.crs)
        kwargs = {"how": how}
        if max_distance is not None:
            kwargs["max_distance"] = max_distance
        result = gpd.sjoin_nearest(left, right, **kwargs)
        if output_path:
            output_path_resolved = resolve_path(output_path, relative_to_storage=True)
            output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            result.to_file(str(output_path_resolved))
            output_path = str(output_path_resolved)
        page = vector_preview(
            result,
            max_features=max_features,
            offset=offset,
            columns=columns,
            include_geometry=include_geometry,
            precision=precision,
        )
        preview = page["preview"]
        return {
            "status": "success",
            "message": f"Nearest spatial join ({how}) completed successfully.",
            "num_features": len(result),
            "crs": str(result.crs),
            "columns": list(result.columns),
            "preview": preview,
            "returned": page["returned"],
            "offset": page["offset"],
            "truncated": page["truncated"],
            "output_path": output_path,
        }
    except Exception as e:
        logger.error(f"Error in sjoin_nearest_gpd: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def point_in_polygon(points_path: str, polygons_path: str, output_path: str = None, max_features: int = 5, offset: int = 0, columns: Optional[str] = None, include_geometry: bool = True, precision: Optional[int] = None) -> Dict[str, Any]:
    """
    Check if points are inside polygons using spatial join (predicate='within').
    Args:
        points_path: Path to the point geospatial file.
        polygons_path: Path to the polygon geospatial file.
        output_path: Optional path to save the result.
    Returns:
        Dictionary with status, message, and output info.
    """
    try:
        points = read_vector(points_path)
        polygons = read_vector(polygons_path)
        if points.crs != polygons.crs:
            polygons = polygons.to_crs(points.crs)
        result = gpd.sjoin(points, polygons, how="left", predicate="within")
        if output_path:
            output_path_resolved = resolve_path(output_path, relative_to_storage=True)
            output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            result.to_file(str(output_path_resolved))
            output_path = str(output_path_resolved)
        page = vector_preview(
            result,
            max_features=max_features,
            offset=offset,
            columns=columns,
            include_geometry=include_geometry,
            precision=precision,
        )
        preview = page["preview"]
        return {
            "status": "success",
            "message": "Point-in-polygon test completed successfully.",
            "num_features": len(result),
            "crs": str(result.crs),
            "columns": list(result.columns),
            "preview": preview,
            "returned": page["returned"],
            "offset": page["offset"],
            "truncated": page["truncated"],
            "output_path": output_path,
        }
    except Exception as e:
        logger.error(f"Error in point_in_polygon: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def write_file_gpd(gdf_path: str, output_path: str, driver: str = None) -> Dict[str, Any]:
    """
    Export a GeoDataFrame to a file (Shapefile, GeoJSON, GPKG, etc.).
    Args:
        gdf_path: Path to the input geospatial file.
        output_path: Path to save the exported file.
        driver: Optional OGR driver name (e.g., 'ESRI Shapefile', 'GeoJSON', 'GPKG').
    Returns:
        Dictionary with status and message.
    """
    try:
        gdf = read_vector(gdf_path)
        output_path_resolved = resolve_path(output_path, relative_to_storage=True)
        output_path_resolved.parent.mkdir(parents=True, exist_ok=True)
        kwargs = {"driver": driver} if driver else {}
        gdf.to_file(str(output_path_resolved), **kwargs)
        return {
            "status": "success",
            "message": f"GeoDataFrame exported to '{output_path_resolved}' successfully.",
            "output_path": str(output_path_resolved),
            "crs": str(gdf.crs),
            "num_features": len(gdf),
            "columns": list(gdf.columns),
        }
    except Exception as e:
        logger.error(f"Error in write_file_gpd: {str(e)}")
        return {"status": "error", "message": str(e)}

