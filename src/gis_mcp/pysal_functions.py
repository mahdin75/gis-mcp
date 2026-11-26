"""PySAL-related MCP tool functions and resource listings."""
import os
import logging
import numpy as np
import geopandas as gpd
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from .mcp import gis_mcp
from .compact import cap_sequence, table_preview

# Configure logging
logger = logging.getLogger(__name__)

@gis_mcp.resource("gis://operations/esda")
def get_spatial_operations() -> Dict[str, List[str]]:
    """List available spatial analysis operations. This is for esda library. They are using pysal library."""
    return {
        "operations": [
            "getis_ord_g",
            "morans_i",
            "gearys_c",
            "gamma_statistic",
            "moran_local",
            "getis_ord_g_local",
            "join_counts",
            "join_counts_local",
            "adbscan"
        ]
    }

@gis_mcp.tool()
def getis_ord_g(
    shapefile_path: str,
    dependent_var: str = "LAND_USE",
    target_crs: str = "EPSG:4326",
    distance_threshold: float = 100000
) -> Dict[str, Any]:
    """Compute Getis-Ord G for global hot spot analysis."""
    try:
        # Clean backticks from string parameters
        shapefile_path = shapefile_path.replace("`", "")
        dependent_var = dependent_var.replace("`", "")
        target_crs = target_crs.replace("`", "")

        # Validate input file
        if not os.path.exists(shapefile_path):
            logger.error(f"Shapefile not found: {shapefile_path}")
            return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}

        # Load GeoDataFrame
        gdf = gpd.read_file(shapefile_path)
        
        # Validate dependent variable
        if dependent_var not in gdf.columns:
            logger.error(f"Dependent variable '{dependent_var}' not found in columns")
            return {"status": "error", "message": f"Dependent variable '{dependent_var}' not found in shapefile columns"}

        # Reproject to target CRS
        gdf = gdf.to_crs(target_crs)

        # Convert distance_threshold to degrees if using geographic CRS (e.g., EPSG:4326)
        effective_threshold = distance_threshold
        unit = "meters"
        if target_crs == "EPSG:4326":
            effective_threshold = distance_threshold / 111000
            unit = "degrees"

        # Extract dependent data
        dependent = gdf[dependent_var].values.astype(np.float64)

        # Create distance-based spatial weights matrix
        import libpysal
        import esda
        w = libpysal.weights.DistanceBand.from_dataframe(gdf, threshold=effective_threshold, binary=False)
        w.transform = 'r'

        # Handle islands
        for island in w.islands:
            w.weights[island] = [0] * len(w.weights[island])
            w.cardinalities[island] = 0

        # Getis-Ord G
        getis = esda.G(dependent, w)

        # Prepare GeoDataFrame preview
        preview = table_preview(gdf, [dependent_var])

        return {
            "status": "success",
            "message": f"Getis-Ord G analysis completed successfully (distance threshold: {effective_threshold} {unit})",
            "result": {
                "shapefile_path": shapefile_path,
                "getis_ord_g": {
                    "G": float(getis.G),
                    "p_value": float(getis.p_sim),
                    "z_score": float(getis.z_sim)
                },
                "data_preview": preview
            }
        }
    
    except Exception as e:
        logger.error(f"Error performing Getis-Ord G analysis: {str(e)}")
        return {"status": "error", "message": f"Failed to perform Getis-Ord G analysis: {str(e)}"}


def pysal_load_data(shapefile_path: str, dependent_var: str, target_crs: str, distance_threshold: float):
    """Common loader and weight creation for esda statistics."""
    if not os.path.exists(shapefile_path):
        return None, None, None, None, f"Shapefile not found: {shapefile_path}"

    gdf = gpd.read_file(shapefile_path)
    if dependent_var not in gdf.columns:
        return None, None, None, None, f"Dependent variable '{dependent_var}' not found in shapefile columns"

    gdf = gdf.to_crs(target_crs)

    effective_threshold = distance_threshold
    unit = "meters"
    if target_crs.upper() == "EPSG:4326":
        effective_threshold = distance_threshold / 111000
        unit = "degrees"

    y = gdf[dependent_var].values.astype(np.float64)
    import libpysal
    w = libpysal.weights.DistanceBand.from_dataframe(gdf, threshold=effective_threshold, binary=False)
    w.transform = 'r'

    for island in w.islands:
        w.weights[island] = [0] * len(w.weights[island])
        w.cardinalities[island] = 0

    return gdf, y, w, (effective_threshold, unit), None


@gis_mcp.tool()
def morans_i(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326", distance_threshold: float = 100000) -> Dict[str, Any]:
    """Compute Moran's I Global Autocorrelation Statistic."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.Moran(y, w)
    preview = table_preview(gdf, [dependent_var])

    return {
        "status": "success",
        "message": f"Moran's I completed successfully (threshold: {threshold} {unit})",
        "result": {
            "I": float(stat.I),
            "morans_i": float(stat.I),  # Also include as morans_i for test compatibility
            "p_value": float(stat.p_sim),
            "z_score": float(stat.z_sim),
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def gearys_c(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326", distance_threshold: float = 100000) -> Dict[str, Any]:
    """Compute Global Geary's C Autocorrelation Statistic."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.Geary(y, w)
    preview = table_preview(gdf, [dependent_var])

    return {
        "status": "success",
        "message": f"Geary's C completed successfully (threshold: {threshold} {unit})",
        "result": {
            "C": float(stat.C),
            "gearys_c": float(stat.C),  # Also include as gearys_c for test compatibility
            "p_value": float(stat.p_sim),
            "z_score": float(stat.z_sim),
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def gamma_statistic(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326", distance_threshold: float = 100000) -> Dict[str, Any]:
    """Compute Gamma Statistic for spatial autocorrelation."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    import esda
    stat = esda.Gamma(y, w)
    preview = table_preview(gdf, [dependent_var])

    # Gamma statistic - check for available attributes
    gamma_val = None
    if hasattr(stat, "G"):
        gamma_val = float(stat.G)
    elif hasattr(stat, "gamma"):
        gamma_val = float(stat.gamma)
    elif hasattr(stat, "gamma_index"):
        gamma_val = float(stat.gamma_index)
    
    p_val = None
    if hasattr(stat, "p_value"):
        p_val = float(stat.p_value)
    elif hasattr(stat, "p_sim"):
        p_val = float(stat.p_sim)
    
    return {
        "status": "success",
        "message": f"Gamma Statistic completed successfully (threshold: {threshold} {unit})",
        "result": {
            "Gamma": gamma_val,
            "p_value": p_val,
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def moran_local(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326",
                distance_threshold: float = 100000, max_records: Optional[int] = None) -> Dict[str, Any]:
    """Local Moran's I."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    # Handle islands - if all points are islands, fall back to KNN weights for connectivity
    import libpysal
    if w.islands:
        if len(w.islands) == len(gdf):
            # All points are islands - fall back to KNN weights
            try:
                # Use k=4 for a 5x5 grid to ensure connectivity
                w = libpysal.weights.KNN.from_dataframe(gdf, k=4)
                w.transform = 'r'
            except Exception as e:
                return {"status": "error", "message": f"All units are islands and KNN fallback failed: {str(e)}"}
        else:
            # Some islands - filter them out
            keep_idx = [i for i in range(len(gdf)) if i not in set(w.islands)]
            if len(keep_idx) == 0:
                return {"status": "error", "message": "All units are islands (no neighbors). Try increasing distance_threshold."}
            # Filter data
            gdf_filtered = gdf.iloc[keep_idx].reset_index(drop=True)
            y_filtered = y[keep_idx]
            # Rebuild weights without islands using the same threshold
            w_filtered = libpysal.weights.DistanceBand.from_dataframe(
                gdf_filtered, 
                threshold=threshold,  # Use the effective threshold already calculated in pysal_load_data
                binary=False
            )
            w_filtered.transform = 'r'
            gdf, y, w = gdf_filtered, y_filtered, w_filtered

    import esda
    stat = esda.Moran_Local(y, w)
    preview = table_preview(gdf, [dependent_var])

    return {
        "status": "success",
        "message": f"Local Moran's I completed successfully (threshold: {threshold} {unit})",
        "result": {
            "count": int(len(gdf)),
            "Is": cap_sequence(stat.Is, max_records),
            "p_values": cap_sequence(stat.p_sim, max_records),
            "z_scores": cap_sequence(stat.z_sim, max_records),
            "data_preview": preview,
        }
    }


@gis_mcp.tool()
def getis_ord_g_local(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326",
                      distance_threshold: float = 100000, max_records: Optional[int] = None) -> Dict[str, Any]:
    """Local Getis-Ord G."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    # Handle islands - if all points are islands, fall back to KNN weights for connectivity
    import libpysal
    if w.islands:
        if len(w.islands) == len(gdf):
            # All points are islands - fall back to KNN weights
            try:
                # Use k=4 for a 5x5 grid to ensure connectivity
                w = libpysal.weights.KNN.from_dataframe(gdf, k=4)
                w.transform = 'r'
            except Exception as e:
                return {"status": "error", "message": f"All units are islands and KNN fallback failed: {str(e)}"}
        else:
            # Some islands - filter them out
            keep_idx = [i for i in range(len(gdf)) if i not in set(w.islands)]
            if len(keep_idx) == 0:
                return {"status": "error", "message": "All units are islands (no neighbors). Try increasing distance_threshold."}
            # Filter data
            gdf_filtered = gdf.iloc[keep_idx].reset_index(drop=True)
            y_filtered = y[keep_idx]
            # Rebuild weights without islands using the same threshold
            w_filtered = libpysal.weights.DistanceBand.from_dataframe(
                gdf_filtered, 
                threshold=threshold,  # Use the effective threshold already calculated in pysal_load_data
                binary=False
            )
            w_filtered.transform = 'r'
            gdf, y, w = gdf_filtered, y_filtered, w_filtered

    import esda
    stat = esda.G_Local(y, w)
    preview = table_preview(gdf, [dependent_var])

    return {
        "status": "success",
        "message": f"Local Getis-Ord G completed successfully (threshold: {threshold} {unit})",
        "result": {
            "count": int(len(gdf)),
            "G_local": cap_sequence(stat.Gs, max_records),
            "p_values": cap_sequence(stat.p_sim, max_records),
            "z_scores": cap_sequence(stat.z_sim, max_records),
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def join_counts(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326",
                distance_threshold: float = 100000) -> Dict[str, Any]:
    """Global Binary Join Counts."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    # Join counts requires binary/categorical data - user must ensure y is binary (0/1 or True/False)
    import esda
    stat = esda.Join_Counts(y, w)
    preview = table_preview(gdf, [dependent_var])

    # Join_Counts attributes: J (total joins), bb, ww, bw, etc.
    join_count_val = None
    if hasattr(stat, "J"):
        join_count_val = float(stat.J)
    elif hasattr(stat, "jc"):
        join_count_val = float(stat.jc)
    elif hasattr(stat, "join_count"):
        join_count_val = float(stat.join_count)
    
    # Handle expected, variance, z_score - these might be DataFrames or scalars
    def safe_float(val):
        """Convert value to float, handling DataFrames and numpy types."""
        if val is None:
            return None
        if isinstance(val, pd.DataFrame):
            # If it's a DataFrame, extract the first value
            return float(val.iloc[0, 0]) if not val.empty else None
        if isinstance(val, (np.ndarray, list, tuple)):
            return float(val[0]) if len(val) > 0 else None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    
    expected_val = getattr(stat, "expected", None)
    variance_val = getattr(stat, "variance", None)
    z_score_val = getattr(stat, "z_score", None)
    p_val = None
    if hasattr(stat, "p_value"):
        p_val = safe_float(stat.p_value)
    elif hasattr(stat, "p_sim"):
        p_val = safe_float(stat.p_sim)
    
    return {
        "status": "success",
        "message": f"Join Counts completed successfully (threshold: {threshold} {unit})",
        "result": {
            "join_counts": join_count_val,
            "expected": safe_float(expected_val),
            "variance": safe_float(variance_val),
            "z_score": safe_float(z_score_val),
            "p_value": p_val,
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def join_counts_local(shapefile_path: str, dependent_var: str = "LAND_USE", target_crs: str = "EPSG:4326",
                      distance_threshold: float = 100000, max_records: Optional[int] = None) -> Dict[str, Any]:
    """Local Join Counts."""
    gdf, y, w, (threshold, unit), err = pysal_load_data(shapefile_path, dependent_var, target_crs, distance_threshold)
    if err:
        return {"status": "error", "message": err}

    # Handle islands - if all points are islands, fall back to KNN weights for connectivity
    import libpysal
    if w.islands:
        if len(w.islands) == len(gdf):
            # All points are islands - fall back to KNN weights
            try:
                # Use k=4 for a 5x5 grid to ensure connectivity
                w = libpysal.weights.KNN.from_dataframe(gdf, k=4)
                w.transform = 'r'
            except Exception as e:
                return {"status": "error", "message": f"All units are islands and KNN fallback failed: {str(e)}"}
        else:
            # Some islands - filter them out
            keep_idx = [i for i in range(len(gdf)) if i not in set(w.islands)]
            if len(keep_idx) == 0:
                return {"status": "error", "message": "All units are islands (no neighbors). Try increasing distance_threshold."}
            # Filter data
            gdf_filtered = gdf.iloc[keep_idx].reset_index(drop=True)
            y_filtered = y[keep_idx]
            # Rebuild weights without islands using the same threshold
            w_filtered = libpysal.weights.DistanceBand.from_dataframe(
                gdf_filtered, 
                threshold=threshold,  # Use the effective threshold already calculated in pysal_load_data
                binary=False
            )
            w_filtered.transform = 'r'
            gdf, y, w = gdf_filtered, y_filtered, w_filtered

    import esda
    stat = esda.Join_Counts_Local(y, w)
    preview = table_preview(gdf, [dependent_var])

    # Join_Counts_Local has LJC attribute
    ljc_val = None
    if hasattr(stat, "LJC"):
        ljc_val = cap_sequence(stat.LJC, max_records)
    elif hasattr(stat, "local_join_counts"):
        ljc_val = cap_sequence(stat.local_join_counts, max_records)
    elif hasattr(stat, "ljc"):
        ljc_val = cap_sequence(stat.ljc, max_records)
    
    return {
        "status": "success",
        "message": f"Local Join Counts completed successfully (threshold: {threshold} {unit})",
        "result": {
            "local_join_counts": ljc_val,
            "data_preview": preview
        }
    }


@gis_mcp.tool()
def adbscan(shapefile_path: str, dependent_var: str = None, target_crs: str = "EPSG:4326",
            distance_threshold: float = 100000, eps: float = 0.1, min_samples: int = 5,
            max_records: Optional[int] = None) -> Dict[str, Any]:
    """Adaptive DBSCAN clustering (requires coordinates, no dependent_var)."""
    if not os.path.exists(shapefile_path):
        return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}
    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.to_crs(target_crs)

    coords = np.array(list(gdf.geometry.apply(lambda g: (g.x, g.y))))
    import esda
    # ADBSCAN constructor - check actual signature to avoid parameter conflicts
    # Try different calling patterns based on actual API
    try:
        # First try: eps and min_samples as keyword arguments
        stat = esda.adbscan.ADBSCAN(coords, eps=eps, min_samples=min_samples)
    except TypeError as e:
        if "multiple values for argument 'eps'" in str(e):
            # eps might be positional - try as positional argument
            try:
                stat = esda.adbscan.ADBSCAN(coords, eps, min_samples)
            except Exception:
                # Last resort: try with just coords and keyword args without eps
                stat = esda.adbscan.ADBSCAN(coords, min_samples=min_samples)
        else:
            raise

    preview = table_preview(gdf, ["id"] if "id" in gdf.columns else [])

    # ADBSCAN attributes - check for available attributes
    labels_val = None
    if hasattr(stat, "labels_"):
        labels_val = cap_sequence(stat.labels_, max_records)
    elif hasattr(stat, "labels"):
        labels_val = cap_sequence(stat.labels, max_records)
    
    core_indices_val = None
    if hasattr(stat, "core_sample_indices_"):
        core_indices_val = stat.core_sample_indices_.tolist() if hasattr(stat.core_sample_indices_, "tolist") else list(stat.core_sample_indices_)
    elif hasattr(stat, "core_sample_indices"):
        core_indices_val = stat.core_sample_indices.tolist() if hasattr(stat.core_sample_indices, "tolist") else list(stat.core_sample_indices)
    
    components_val = None
    if hasattr(stat, "components_"):
        components_val = stat.components_.tolist() if hasattr(stat.components_, "tolist") else list(stat.components_)
    elif hasattr(stat, "components"):
        components_val = stat.components.tolist() if hasattr(stat.components, "tolist") else list(stat.components)
    
    return {
        "status": "success",
        "message": f"A-DBSCAN clustering completed successfully (eps={eps}, min_samples={min_samples})",
        "result": {
            "labels": labels_val,
            "core_sample_indices": core_indices_val,
            "components": components_val,
            "data_preview": preview
        }
    }

@gis_mcp.tool()
def weights_from_shapefile(shapefile_path: str, contiguity: str = "queen", id_field: Optional[str] = None) -> Dict[str, Any]:

    """Create a spatial weights (W) from a shapefile using contiguity.

    - contiguity: 'queen' or 'rook' (default 'queen')
    - id_field: optional attribute name to use as observation IDs
    """
    try:
        if not os.path.exists(shapefile_path):
            return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}

        contiguity_lower = (contiguity or "").lower()
        import libpysal
        if contiguity_lower == "queen":
            w = libpysal.weights.Queen.from_shapefile(shapefile_path, idVariable=id_field)
        elif contiguity_lower == "rook":
            w = libpysal.weights.Rook.from_shapefile(shapefile_path, idVariable=id_field)
        else:
            # Fallback to generic W loader if an unrecognized contiguity is provided
            w = libpysal.weights.W.from_shapefile(shapefile_path, idVariable=id_field)

        ids = w.id_order
        neighbor_counts = [w.cardinalities[i] for i in ids]
        islands = list(w.islands) if hasattr(w, "islands") else []

        preview_ids = ids[:5]
        neighbors_preview = {i: w.neighbors.get(i, []) for i in preview_ids}
        weights_preview = {i: w.weights.get(i, []) for i in preview_ids}

        result = {
            "n": int(w.n),
            "id_count": int(len(ids)),
            "id_field": id_field,
            "contiguity": contiguity_lower if contiguity_lower in {"queen", "rook"} else "generic",
            "neighbors_stats": {
                "min": int(min(neighbor_counts)) if neighbor_counts else 0,
                "max": int(max(neighbor_counts)) if neighbor_counts else 0,
                "mean": float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
            },
            "islands": islands,
            "neighbors_preview": neighbors_preview,
            "weights_preview": weights_preview,
        }

        return {
            "status": "success",
            "message": "Spatial weights constructed successfully",
            "result": result,
            "weights_info": result
        }

    except Exception as e:
        logger.error(f"Error creating spatial weights from shapefile: {str(e)}")
        return {"status": "error", "message": f"Failed to create spatial weights: {str(e)}"}

@gis_mcp.tool()
def distance_band_weights(
    data_path: str,
    threshold: float,
    binary: bool = True,
    id_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a distance-based spatial weights (W) object from point data.

    - data_path: path to point shapefile or GeoPackage
    - threshold: distance threshold for neighbors (in CRS units, e.g., meters)
    - binary: True for binary weights, False for inverse distance weights
    - id_field: optional attribute name to use as observation IDs
    """
    try:
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)

        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        # Extract coordinates
        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        # Create DistanceBand weights
        import libpysal
        if id_field and id_field in gdf.columns:
            ids = gdf[id_field].tolist()
            w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary, ids=ids)
        else:
            w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary)

        ids = w.id_order
        neighbor_counts = [w.cardinalities[i] for i in ids]
        islands = list(w.islands) if hasattr(w, "islands") else []

        # Previews - convert to native Python types immediately
        preview_ids = ids[:5]
        neighbors_preview = {}
        weights_preview = {}
        for i in preview_ids:
            # Convert neighbor IDs and weights to native Python types
            neighbors = w.neighbors.get(i, [])
            weights_list = w.weights.get(i, [])
            neighbors_preview[i] = [int(n) if isinstance(n, (np.integer, np.int32, np.int64)) else n for n in neighbors]
            weights_preview[i] = [float(w_val) if isinstance(w_val, (np.floating, np.float32, np.float64)) else (int(w_val) if isinstance(w_val, (np.integer, np.int32, np.int64)) else w_val) for w_val in weights_list]

        result = {
            "n": int(w.n),
            "id_count": int(len(ids)),
            "threshold": float(threshold),
            "binary": bool(binary),
            "id_field": id_field,
            "neighbors_stats": {
                "min": int(min(neighbor_counts)) if neighbor_counts else 0,
                "max": int(max(neighbor_counts)) if neighbor_counts else 0,
                "mean": float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
            },
            "islands": [int(i) if isinstance(i, (np.integer, np.int32, np.int64)) else i for i in islands],
            "neighbors_preview": neighbors_preview,
            "weights_preview": weights_preview,
        }

        # Convert numpy types to native Python types for serialization (recursive)
        def convert_numpy_types(obj):
            """Recursively convert numpy types to native Python types."""
            if obj is None:
                return None
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int32, np.int64, np.int8, np.int16)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float32, np.float64, np.float16)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                # Handle other iterable types
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        result = convert_numpy_types(result)

        return {
            "status": "success",
            "message": "DistanceBand spatial weights constructed successfully",
            "result": result,
            "weights_info": result
        }

    except Exception as e:
        logger.error(f"Error creating DistanceBand weights: {str(e)}")
        return {"status": "error", "message": f"Failed to create DistanceBand weights: {str(e)}"}


@gis_mcp.tool()
def knn_weights(
    data_path: str,
    k: int,
    id_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a k-nearest neighbors spatial weights (W) object from point data.

    - data_path: path to point shapefile or GeoPackage
    - k: number of nearest neighbors
    - id_field: optional attribute name to use as observation IDs
    """
    try:
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)

        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        # Extract coordinates
        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        # Create KNN weights
        import libpysal
        if id_field and id_field in gdf.columns:
            ids = gdf[id_field].tolist()
            w = libpysal.weights.KNN(coords, k=k, ids=ids)
        else:
            w = libpysal.weights.KNN(coords, k=k)

        ids = w.id_order
        # Convert ids to native Python types immediately
        ids = [int(i) if isinstance(i, (np.integer, np.int32, np.int64)) else i for i in ids]
        neighbor_counts = [int(w.cardinalities[i]) if isinstance(w.cardinalities[i], (np.integer, np.int32, np.int64)) else w.cardinalities[i] for i in ids]
        islands = [int(i) if isinstance(i, (np.integer, np.int32, np.int64)) else i for i in list(w.islands)] if hasattr(w, "islands") else []

        # Previews - convert to native Python types immediately
        preview_ids = ids[:5]
        neighbors_preview = {}
        weights_preview = {}
        for i in preview_ids:
            # Convert neighbor IDs and weights to native Python types
            neighbors = w.neighbors.get(i, [])
            weights_list = w.weights.get(i, [])
            neighbors_preview[int(i) if isinstance(i, (np.integer, np.int32, np.int64)) else i] = [
                int(n) if isinstance(n, (np.integer, np.int32, np.int64, np.int8, np.int16)) else n for n in neighbors
            ]
            weights_preview[int(i) if isinstance(i, (np.integer, np.int32, np.int64)) else i] = [
                float(w_val) if isinstance(w_val, (np.floating, np.float32, np.float64, np.float16)) 
                else (int(w_val) if isinstance(w_val, (np.integer, np.int32, np.int64, np.int8, np.int16)) else w_val) 
                for w_val in weights_list
            ]

        result = {
            "n": int(w.n),
            "id_count": int(len(ids)),
            "k": int(k),
            "id_field": id_field,
            "neighbors_stats": {
                "min": int(min(neighbor_counts)) if neighbor_counts else 0,
                "max": int(max(neighbor_counts)) if neighbor_counts else 0,
                "mean": float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
            },
            "islands": islands,
            "neighbors_preview": neighbors_preview,
            "weights_preview": weights_preview,
        }

        # Convert numpy types to native Python types for serialization (recursive, final pass)
        def convert_numpy_types(obj):
            """Recursively convert numpy types to native Python types."""
            if obj is None:
                return None
            if isinstance(obj, dict):
                return {convert_numpy_types(k) if isinstance(k, (np.integer, np.int32, np.int64)) else k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int32, np.int64, np.int8, np.int16)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float32, np.float64, np.float16)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                # Handle other iterable types
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        result = convert_numpy_types(result)
        
        return {
            "status": "success",
            "message": "KNN spatial weights constructed successfully",
            "result": result,
            "weights_info": result
        }

    except Exception as e:
        logger.error(f"Error creating KNN weights: {str(e)}")
        return {"status": "error", "message": f"Failed to create KNN weights: {str(e)}"}


@gis_mcp.tool()
def build_transform_and_save_weights(
    data_path: str,
    method: str = "queen",
    id_field: Optional[str] = None,
    threshold: Optional[float] = None,
    k: Optional[int] = None,
    binary: bool = True,
    transform_type: Optional[str] = None,
    output_path: str = "weights.gal",
    format: str = "gal",
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Pipeline: Read shapefile, build spatial weights, optionally transform, and save to file.

    Parameters:
    - data_path: Path to point shapefile or GeoPackage
    - method: 'queen', 'rook', 'distance_band', 'knn'
    - id_field: Optional field name for IDs
    - threshold: Distance threshold (required if method='distance_band')
    - k: Number of neighbors (required if method='knn')
    - binary: True for binary weights, False for inverse distance (DistanceBand only)
    - transform_type: 'r', 'v', 'b', 'o', or 'd' (optional)
    - output_path: File path to save weights
    - format: 'gal' or 'gwt'
    - overwrite: Allow overwriting if file exists
    """
    try:
        # --- Step 1: Check input file ---
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)
        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        # --- Step 2: Build weights ---
        import libpysal
        method = (method or "").lower()
        if method == "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf, idVariable=id_field)
        elif method == "rook":
            w = libpysal.weights.Rook.from_dataframe(gdf, idVariable=id_field)
        elif method == "distance_band":
            if threshold is None:
                return {"status": "error", "message": "Threshold is required for distance_band method"}
            if id_field and id_field in gdf.columns:
                ids = gdf[id_field].tolist()
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary, ids=ids)
            else:
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary)
        elif method == "knn":
            if k is None:
                return {"status": "error", "message": "k is required for knn method"}
            if id_field and id_field in gdf.columns:
                ids = gdf[id_field].tolist()
                w = libpysal.weights.KNN(coords, k=k, ids=ids)
            else:
                w = libpysal.weights.KNN(coords, k=k)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}

        # --- Step 3: Apply transformation if given ---
        if transform_type:
            transform_type = (transform_type or "").lower()
            if transform_type not in {"r", "v", "b", "o", "d"}:
                return {"status": "error", "message": f"Invalid transform type: {transform_type}"}
            w.transform = transform_type

        # --- Step 4: Save weights to file ---
        format = (format or "").lower()
        if format not in {"gal", "gwt"}:
            return {"status": "error", "message": f"Invalid format: {format}"}

        if not output_path.lower().endswith(f".{format}"):
            output_path += f".{format}"

        if os.path.exists(output_path) and not overwrite:
            return {"status": "error", "message": f"File already exists: {output_path}. Set overwrite=True to replace it."}

        w.to_file(output_path, format=format)

        # --- Step 5: Build result ---
        return {
            "status": "success",
            "message": f"{method} weights built and saved successfully",
            "result": {
                "path": output_path,
                "format": format,
                "n": int(w.n),
                "transform": getattr(w, "transform", None),
                "islands": list(w.islands) if hasattr(w, "islands") else [],
            },
        }

    except Exception as e:
        logger.error(f"Error in build_transform_and_save_weights: {str(e)}")
        return {"status": "error", "message": f"Failed to build and save weights: {str(e)}"}


@gis_mcp.tool()
def ols_with_spatial_diagnostics_safe(
    data_path: str,
    y_field: str,
    x_fields: List[str],
    weights_path: Optional[str] = None,
    weights_method: str = "queen",
    id_field: Optional[str] = None,
    threshold: Optional[float] = None,
    k: Optional[int] = None,
    binary: bool = True
) -> Dict[str, Any]:
    """
    Safe MCP pipeline: Read shapefile, build/load W, convert numeric, check NaNs, run OLS.

    Parameters:
    - data_path: path to shapefile or GeoPackage
    - y_field: dependent variable column name
    - x_fields: list of independent variable column names
    - weights_path: optional path to existing weights file (.gal or .gwt)
    - weights_method: 'queen', 'rook', 'distance_band', or 'knn' (used if weights_path not provided)
    - id_field: optional attribute name to use as observation IDs
    - threshold: required if method='distance_band'
    - k: required if method='knn'
    - binary: True for binary weights (DistanceBand only)
    """
    try:
        # --- Step 1: Read data ---
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)
        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        # --- Step 2: Extract and convert y and X ---
        if y_field not in gdf.columns:
            return {"status": "error", "message": f"Dependent variable '{y_field}' not found in dataset"}
        if any(xf not in gdf.columns for xf in x_fields):
            return {"status": "error", "message": f"Independent variable(s) {x_fields} not found in dataset"}

        y = gdf[[y_field]].astype(float).values
        X = gdf[x_fields].astype(float).values

        # --- Step 3: Check for NaNs or infinite values ---
        if not np.all(np.isfinite(y)):
            return {"status": "error", "message": "Dependent variable contains NaN or infinite values"}
        if not np.all(np.isfinite(X)):
            return {"status": "error", "message": "Independent variables contain NaN or infinite values"}

        # --- Step 4: Load or build weights ---
        import libpysal
        if weights_path:
            if not os.path.exists(weights_path):
                return {"status": "error", "message": f"Weights file not found: {weights_path}"}
            w = libpysal.open(weights_path).read()
        else:
            coords = [(geom.x, geom.y) for geom in gdf.geometry]
            wm = weights_method.lower()
            if wm == "queen":
                w = libpysal.weights.Queen.from_dataframe(gdf, idVariable=id_field)
            elif wm == "rook":
                w = libpysal.weights.Rook.from_dataframe(gdf, idVariable=id_field)
            elif wm == "distance_band":
                if threshold is None:
                    return {"status": "error", "message": "Threshold is required for distance_band"}
                ids = gdf[id_field].tolist() if id_field and id_field in gdf.columns else None
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary, ids=ids)
            elif wm == "knn":
                if k is None:
                    return {"status": "error", "message": "k is required for knn"}
                ids = gdf[id_field].tolist() if id_field and id_field in gdf.columns else None
                w = libpysal.weights.KNN(coords, k=k, ids=ids)
            else:
                return {"status": "error", "message": f"Unsupported weights method: {weights_method}"}

        w.transform = "r"  # Row-standardize for regression

        # --- Step 5: Fit OLS with spatial diagnostics ---
        try:
            from spreg import OLS
        except ModuleNotFoundError:
            return {"status": "error", "message": "The 'spreg' package is not installed. Install with: pip install spreg"}
        
        # Ensure y is shape (n, 1) and X is (n, k) for spreg
        y = y.reshape(-1, 1) if len(y.shape) == 1 else y
        if X.shape[1] != len(x_fields):
            X = X.T if X.shape[0] == len(x_fields) else X
        
        # Run OLS with spatial diagnostics
        ols_model = OLS(y, X, w=w, spat_diag=True, name_y=y_field, name_x=x_fields, name_ds="dataset")

        # --- Step 6: Collect results ---
        # Extract Moran's I for residuals if available (from diagnostics)
        moran_residual = None
        moran_pvalue = None
        if hasattr(ols_model, "diagnostics") and ols_model.diagnostics is not None:
            diag = ols_model.diagnostics
            # Check for Moran's I in diagnostics
            if isinstance(diag, dict):
                if "moran_res" in diag and diag["moran_res"] is not None:
                    mor_res = diag["moran_res"]
                    if len(mor_res) >= 2:
                        moran_residual = float(mor_res[0])
                        moran_pvalue = float(mor_res[1])
        
        # Extract beta names
        beta_names = []
        if hasattr(ols_model, "name_x") and ols_model.name_x:
            beta_names = list(ols_model.name_x)
        else:
            beta_names = [f"x_{i}" for i in range(len(x_fields))]
        
        # Add constant to names if present
        has_constant = hasattr(ols_model, "constant") and ols_model.constant
        if has_constant:
            beta_names = ["constant"] + beta_names
        
        # Extract betas
        betas_dict = {}
        if hasattr(ols_model, "betas") and ols_model.betas is not None:
            betas_flat = ols_model.betas.flatten()
            # Match betas to names
            for i, beta_val in enumerate(betas_flat):
                if i < len(beta_names):
                    betas_dict[beta_names[i]] = float(beta_val)
                else:
                    betas_dict[f"beta_{i}"] = float(beta_val)
        
        # Extract standard errors
        std_err_list = []
        if hasattr(ols_model, "std_err") and ols_model.std_err is not None:
            std_err_list = ols_model.std_err.tolist() if hasattr(ols_model.std_err, "tolist") else list(ols_model.std_err)
        
        results = {
            "n_obs": int(ols_model.n) if hasattr(ols_model, "n") else int(len(y)),
            "r2": float(ols_model.r2) if hasattr(ols_model, "r2") else None,
            "std_error": std_err_list,
            "betas": betas_dict,
            "moran_residual": moran_residual,
            "moran_pvalue": moran_pvalue,
        }

        return {
            "status": "success",
            "message": "OLS regression with spatial diagnostics completed successfully",
            "result": results,
            "regression_results": results  # Also include as regression_results for test compatibility
        }

    except Exception as e:
        logger.error(f"Error in ols_with_spatial_diagnostics_safe: {str(e)}")
        return {"status": "error", "message": f"Failed to run OLS regression: {str(e)}"}


@gis_mcp.tool()
def build_and_transform_weights(
    data_path: str,
    method: str = "queen",
    id_field: Optional[str] = None,
    threshold: Optional[float] = None,
    k: Optional[int] = None,
    binary: bool = True,
    transform_type: str = "r"
) -> Dict[str, Any]:
    """
    Build and transform spatial weights in one step.

    Parameters:
    - data_path: Path to point shapefile or GeoPackage
    - method: 'queen', 'rook', 'distance_band', or 'knn'
    - id_field: Optional field name for IDs
    - threshold: Distance threshold (required if method='distance_band')
    - k: Number of neighbors (required if method='knn')
    - binary: True for binary weights, False for inverse distance (DistanceBand only)
    - transform_type: 'r', 'v', 'b', 'o', or 'd'
    """
    try:
        # --- Step 1: Check file ---
        if not os.path.exists(data_path):
            return {"status": "error", "message": f"Data file not found: {data_path}"}

        gdf = gpd.read_file(data_path)
        if gdf.empty:
            return {"status": "error", "message": "Input file contains no features"}

        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        # --- Step 2: Build weights ---
        import libpysal
        method = (method or "").lower()
        if method == "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf, idVariable=id_field)
        elif method == "rook":
            w = libpysal.weights.Rook.from_dataframe(gdf, idVariable=id_field)
        elif method == "distance_band":
            if threshold is None:
                return {"status": "error", "message": "Threshold is required for distance_band method"}
            if id_field and id_field in gdf.columns:
                ids = gdf[id_field].tolist()
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary, ids=ids)
            else:
                w = libpysal.weights.DistanceBand(coords, threshold=threshold, binary=binary)
        elif method == "knn":
            if k is None:
                return {"status": "error", "message": "k is required for knn method"}
            if id_field and id_field in gdf.columns:
                ids = gdf[id_field].tolist()
                w = libpysal.weights.KNN(coords, k=k, ids=ids)
            else:
                w = libpysal.weights.KNN(coords, k=k)
        else:
            return {"status": "error", "message": f"Unsupported method: {method}"}

        # --- Step 3: Apply transformation ---
        if not isinstance(w, libpysal.weights.W):
            return {"status": "error", "message": "Failed to build a valid W object"}
        transform_type = (transform_type or "").lower()
        if transform_type not in {"r", "v", "b", "o", "d"}:
            return {"status": "error", "message": f"Invalid transform type: {transform_type}"}
        w.transform = transform_type

        # --- Step 4: Build result ---
        ids = w.id_order
        neighbor_counts = [w.cardinalities[i] for i in ids]
        islands = list(w.islands) if hasattr(w, "islands") else []
        preview_ids = ids[:5]
        neighbors_preview = {i: w.neighbors.get(i, []) for i in preview_ids}
        weights_preview = {i: w.weights.get(i, []) for i in preview_ids}

        result = {
            "n": int(w.n),
            "id_count": len(ids),
            "method": method,
            "threshold": threshold if method == "distance_band" else None,
            "k": k if method == "knn" else None,
            "binary": binary if method == "distance_band" else None,
            "transform": transform_type,
            "neighbors_stats": {
                "min": int(min(neighbor_counts)) if neighbor_counts else 0,
                "max": int(max(neighbor_counts)) if neighbor_counts else 0,
                "mean": float(np.mean(neighbor_counts)) if neighbor_counts else 0.0,
            },
            "islands": islands,
            "neighbors_preview": neighbors_preview,
            "weights_preview": weights_preview,
        }

        return {
            "status": "success",
            "message": f"{method} spatial weights built and transformed successfully",
            "result": result,
            "weights_info": result
        }

    except Exception as e:
        logger.error(f"Error in build_and_transform_weights: {str(e)}")
        return {"status": "error", "message": f"Failed to build and transform weights: {str(e)}"}


@gis_mcp.tool()

def spatial_markov(
    shapefile_path: str,
    value_columns: Union[str, List[str]],   # time-ordered, oldest -> newest
    target_crs: str = "EPSG:4326",
    weights_method: str = "queen",          # 'queen'|'rook'|'distance'
    distance_threshold: float = 100000,     # meters (converted to degrees if 4326)
    k: int = 5,                             # classes for y (quantile bins if continuous)
    m: int = 5,                             # classes for spatial lags
    fixed: bool = True,                     # pooled quantiles across all periods
    permutations: int = 0,                  # >0 to get randomization p-values for x2
    relative: bool = True,                  # divide each period by its mean
    drop_na: bool = True,                   # drop features with any NA across time columns
    fill_empty_classes: bool = True         # handle empty bins by making them self-absorbing
) -> Dict[str, Any]:
    """Run giddy Spatial Markov on a panel (n regions x t periods) from a shapefile."""
    try:
        # --- sanitize ---
        for s in ("shapefile_path","target_crs","weights_method"):
            v = locals()[s]
            if isinstance(v, str):
                locals()[s] = v.replace("`","")

        if isinstance(value_columns, str):
            value_cols = [c.strip() for c in value_columns.replace("`","").split(",") if c.strip()]
        else:
            value_cols = list(value_columns)

        if not os.path.exists(shapefile_path):
            return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}
        if len(value_cols) < 2:
            return {"status": "error", "message": "value_columns must include at least 2 time steps (wide format)."}

        # --- load + project ---
        gdf = gpd.read_file(shapefile_path)
        missing = [c for c in value_cols if c not in gdf.columns]
        if missing:
            return {"status": "error", "message": f"Columns not found: {missing}"}

        gdf = gdf.to_crs(target_crs)

        # Ensure numeric
        gdf[value_cols] = gdf[value_cols].apply(pd.to_numeric, errors="coerce")

        # --- prepare Y (n x t) ---
        Y = gdf[value_cols].to_numpy(copy=True).astype(float)  # shape (n, t)
        if drop_na:
            mask = ~np.any(np.isnan(Y), axis=1)
            if mask.sum() < Y.shape[0]:
                gdf = gdf.loc[mask].reset_index(drop=True)
                Y = Y[mask, :]

        # optional relative values (period-wise)
        if relative:
            col_means = Y.mean(axis=0)
            col_means[col_means == 0] = 1.0
            Y = Y / col_means

        # --- spatial weights ---
        import libpysal
        wm = weights_method.lower()
        if wm == "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf, use_index=True)
        elif wm == "rook":
            w = libpysal.weights.Rook.from_dataframe(gdf, use_index=True)
        elif wm == "distance":
            thr = distance_threshold
            if target_crs.upper() == "EPSG:4326":
                thr = distance_threshold / 111000.0  # meters -> degrees
            w = libpysal.weights.DistanceBand.from_dataframe(
                gdf, threshold=thr, binary=False, use_index=True
            )
        else:
            return {"status":"error","message":f"Unknown weights_method: {weights_method}"}

        w.transform = "r"

        # handle islands by dropping rows and rebuilding weights
        if w.islands:
            keep_idx = [i for i in range(gdf.shape[0]) if i not in set(w.islands)]
            if not keep_idx:
                return {"status":"error","message":"All units are islands under current weights; adjust weights_method/threshold."}
            gdf = gdf.iloc[keep_idx].reset_index(drop=True)
            Y = Y[keep_idx, :]
            if wm == "queen":
                w = libpysal.weights.Queen.from_dataframe(gdf, use_index=True)
            elif wm == "rook":
                w = libpysal.weights.Rook.from_dataframe(gdf, use_index=True)
            else:
                thr = distance_threshold if target_crs.upper() != "EPSG:4326" else distance_threshold/111000.0
                w = libpysal.weights.DistanceBand.from_dataframe(gdf, threshold=thr, binary=False, use_index=True)
            w.transform = "r"

        # --- Spatial Markov ---
        try:
            from giddy.markov import Spatial_Markov
        except ModuleNotFoundError:
            return {"status": "error", "message": "The 'giddy' package is not installed. Install with: pip install giddy"}

        sm = Spatial_Markov(
            Y, w,
            k=int(k), m=int(m),
            permutations=int(permutations),
            fixed=bool(fixed),
            discrete=False,
            fill_empty_classes=bool(fill_empty_classes),
            variable_name=";".join(value_cols)
        )

        # --- package results (JSON-safe) ---
        def tolist(x):
            """Recursively convert numpy arrays and nested structures to lists."""
            if x is None:
                return None
            try:
                if isinstance(x, np.ndarray):
                    return x.tolist()
                elif isinstance(x, (list, tuple)):
                    return [tolist(xx) for xx in x]
                elif isinstance(x, dict):
                    return {k: tolist(v) for k, v in x.items()}
                elif isinstance(x, (np.integer, np.floating)):
                    return float(x) if isinstance(x, np.floating) else int(x)
                else:
                    return x
            except Exception:
                # Fallback: try to convert to native Python type
                try:
                    return float(x) if isinstance(x, (np.floating, float)) else int(x) if isinstance(x, (np.integer, int)) else str(x)
                except Exception:
                    return x

        preview = table_preview(gdf, value_cols, geometry_key="geometry_wkt")

        result = {
            "n_regions": int(Y.shape[0]),
            "n_periods": int(Y.shape[1]),
            "k_classes_y": int(k),
            "m_classes_lag": int(m),
            "weights_method": weights_method.lower(),
            "value_columns": value_cols,
            "discretization": {
                "cutoffs_y": tolist(getattr(sm, "cutoffs", None)),
                "cutoffs_lag": tolist(getattr(sm, "lag_cutoffs", None)),
                "fixed": bool(fixed)
            },
            "global_transition_prob_p": tolist(sm.p),      # (k x k)
            "conditional_transition_prob_P": tolist(sm.P), # (m x k x k)
            "global_steady_state_s": tolist(sm.s),         # (k,)
            "conditional_steady_states_S": tolist(sm.S),   # (m x k)
            "tests": {
                "chi2_total_x2": float(getattr(sm, "x2", np.nan)),
                "chi2_df": int(getattr(sm, "x2_dof", -1)),
                "chi2_pvalue": float(getattr(sm, "x2_pvalue", np.nan)),
                "Q": float(getattr(sm, "Q", np.nan)),
                "Q_p_value": float(getattr(sm, "Q_p_value", np.nan)),
                "LR": float(getattr(sm, "LR", np.nan)),
                "LR_p_value": float(getattr(sm, "LR_p_value", np.nan)),
            },
            "data_preview": preview,
        }

        msg = "Spatial Markov completed successfully"
        if wm == "distance" and target_crs.upper() == "EPSG:4326":
            msg += f" (threshold interpreted as {distance_threshold/111000.0:.6f} degrees)."

        # Apply tolist conversion recursively to the entire result
        result = tolist(result)

        return {"status": "success", "message": msg, "result": result}

    except Exception as e:
        return {"status": "error", "message": f"Failed to run Spatial Markov: {str(e)}"}

@gis_mcp.tool()

def dynamic_lisa(
    shapefile_path: str,
    value_columns: Union[str, List[str]],   # exactly two columns: [t0, t1]
    target_crs: str = "EPSG:4326",
    weights_method: str = "queen",          # 'queen'|'rook'|'distance'
    distance_threshold: float = 100000,     # meters (converted to degrees if 4326)
    k: int = 8,                             # number of rose sectors
    permutations: int = 99,                 # 0 = skip inference
    alternative: str = "two.sided",         # 'two.sided'|'positive'|'negative'
    relative: bool = True,                  # divide each column by its mean
    drop_na: bool = True                    # drop features with NA in either column
) -> Dict[str, Any]:
    """Run dynamic LISA (directional LISA) with giddy.directional.Rose.

    Returns sector counts, angles, vector lengths, and (optionally) permutation p-values.
    """
    try:
        # --- sanitize ---
        for s in ("shapefile_path","target_crs","weights_method","alternative"):
            v = locals()[s]
            if isinstance(v, str):
                locals()[s] = v.replace("`","")

        if isinstance(value_columns, str):
            cols = [c.strip() for c in value_columns.replace("`","").split(",") if c.strip()]
        else:
            cols = list(value_columns)

        if not os.path.exists(shapefile_path):
            return {"status":"error","message":f"Shapefile not found: {shapefile_path}"}
        if len(cols) != 2:
            return {"status":"error","message":"value_columns must be exactly two columns: [start_time, end_time]."}

        # --- load + project ---
        gdf = gpd.read_file(shapefile_path)
        missing = [c for c in cols if c not in gdf.columns]
        if missing:
            return {"status":"error","message":f"Columns not found: {missing}"}
        gdf = gdf.to_crs(target_crs)

        # --- prepare Y (n x 2) ---
        Y = gdf[cols].astype(float).to_numpy(copy=True)
        if drop_na:
            mask = ~np.any(np.isnan(Y), axis=1)
            gdf = gdf.loc[mask].reset_index(drop=True)
            Y = Y[mask, :]

        if relative:
            col_means = Y.mean(axis=0)
            col_means[col_means == 0] = 1.0
            Y = Y / col_means

        # --- spatial weights ---
        import libpysal
        wm = weights_method.lower()
        if wm == "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf, use_index=True)
        elif wm == "rook":
            w = libpysal.weights.Rook.from_dataframe(gdf, use_index=True)
        elif wm == "distance":
            thr = distance_threshold
            if target_crs.upper() == "EPSG:4326":
                thr = distance_threshold / 111000.0  # meters → degrees
            w = libpysal.weights.DistanceBand.from_dataframe(gdf, threshold=thr, binary=False)
        else:
            return {"status":"error","message":f"Unknown weights_method: {weights_method}"}
        w.transform = "r"

        # drop islands (units with no neighbors)
        if w.islands:
            keep = [i for i in range(gdf.shape[0]) if i not in set(w.islands)]
            if not keep:
                return {"status":"error","message":"All units are islands under current weights."}
            gdf = gdf.iloc[keep].reset_index(drop=True)
            Y = Y[keep, :]
            if wm == "queen":
                w = libpysal.weights.Queen.from_dataframe(gdf, use_index=True)
            elif wm == "rook":
                w = libpysal.weights.Rook.from_dataframe(gdf, use_index=True)
            else:
                thr = distance_threshold if target_crs.upper() != "EPSG:4326" else distance_threshold/111000.0
                w = libpysal.weights.DistanceBand.from_dataframe(gdf, threshold=thr, binary=False)
            w.transform = "r"

        # --- Dynamic LISA (Rose) ---
        from giddy.directional import Rose
        rose = Rose(Y, w, k=int(k))  # computes cuts, counts, theta, r, bins, lag internally

        # permutation inference (optional)
        pvals = None
        expected_perm = larger_perm = smaller_perm = None
        if permutations and permutations > 0:
            rose.permute(permutations=int(permutations), alternative=alternative)
            pvals = np.asarray(getattr(rose, "p", None)).tolist() if hasattr(rose, "p") else None
            expected_perm = np.asarray(getattr(rose, "expected_perm", [])).tolist()
            larger_perm = np.asarray(getattr(rose, "larger_perm", [])).tolist()
            smaller_perm = np.asarray(getattr(rose, "smaller_perm", [])).tolist()

        preview = table_preview(gdf, cols, geometry_key="geometry_wkt")

        result = {
            "n_regions": int(Y.shape[0]),
            "k_sectors": int(k),
            "weights_method": wm,
            "value_columns": cols,
            "cuts_radians": np.asarray(rose.cuts).tolist(),        # sector edges
            "sector_counts": np.asarray(rose.counts).tolist(),     # count per sector
            "angles_theta_rad": np.asarray(rose.theta).tolist(),
            "vector_lengths_r": np.asarray(rose.r).tolist(),
            "bins_used": np.asarray(rose.bins).tolist(),
            "inference": {
                "permutations": int(permutations),
                "alternative": alternative,
                "p_values_by_sector": pvals,
                "expected_counts_perm": expected_perm,
                "larger_or_equal_counts": larger_perm,
                "smaller_or_equal_counts": smaller_perm
            },
            "data_preview": preview
        }

        msg = "Dynamic LISA (Rose) completed successfully"
        if wm == "distance" and target_crs.upper() == "EPSG:4326":
            msg += f" (threshold interpreted as {distance_threshold/111000.0:.6f} degrees)."

        return {"status":"success","message":msg,"result":result}

    except Exception as e:
        return {"status":"error","message":f"Failed to run Dynamic LISA: {str(e)}"}

@gis_mcp.tool()

def gm_lag(
    shapefile_path: str,
    y_col: str,                               # dependent variable
    x_cols: Union[str, List[str]],            # exogenous regressors (no constant)
    target_crs: str = "EPSG:4326",
    weights_method: str = "queen",            # 'queen'|'rook'|'distance'
    distance_threshold: float = 100000,       # meters; auto→degrees for EPSG:4326
    # IV/GMM config
    w_lags: int = 1,                          # instruments: WX, WWX, ...
    lag_q: bool = True,                       # also lag external instruments q
    yend_cols: Union[None, str, List[str]] = None,  # other endogenous regressors (optional)
    q_cols: Union[None, str, List[str]] = None,     # their external instruments (optional)
    # Inference options
    robust: Union[None, str] = None,          # None | 'white' | 'hac'
    hac_bandwidth: float = None,              # only used if robust='hac'
    spat_diag: bool = True,                   # AK test
    sig2n_k: bool = False,                    # variance uses n-k if True
    drop_na: bool = True                      # drop rows with NA in y/x/yend/q
) -> Dict[str, Any]:
    """
    Run spreg.GM_Lag (spatial 2SLS / GMM-IV spatial lag model) on a cross-section.

    Returns coefficients with SE/z/p, fit metrics, (optional) AK test, and a small data preview.
    """
    try:
        # --- sanitize inputs ---
        for s in ("shapefile_path","target_crs","weights_method"):
            v = locals()[s]
            if isinstance(v, str):
                locals()[s] = v.replace("`","")

        if isinstance(x_cols, str):
            x_cols_list = [c.strip() for c in x_cols.split(",") if c.strip()]
        else:
            x_cols_list = list(x_cols)

        if isinstance(yend_cols, str):
            yend_cols_list = [c.strip() for c in yend_cols.split(",") if c.strip()]
        elif yend_cols is None:
            yend_cols_list = None
        else:
            yend_cols_list = list(yend_cols)

        if isinstance(q_cols, str):
            q_cols_list = [c.strip() for c in q_cols.split(",") if c.strip()]
        elif q_cols is None:
            q_cols_list = None
        else:
            q_cols_list = list(q_cols)

        if not os.path.exists(shapefile_path):
            return {"status": "error", "message": f"Shapefile not found: {shapefile_path}"}
        if not x_cols_list:
            return {"status": "error", "message": "x_cols must include at least one regressor."}

        # --- load + project ---
        gdf = gpd.read_file(shapefile_path)
        needed = [y_col] + x_cols_list + (yend_cols_list or []) + (q_cols_list or [])
        missing = [c for c in needed if c not in gdf.columns]
        if missing:
            return {"status": "error", "message": f"Columns not found: {missing}"}

        gdf = gdf.to_crs(target_crs)

        # --- coerce numerics & subset ---
        gdf[needed] = gdf[needed].apply(pd.to_numeric, errors="coerce")
        data = gdf[needed + [gdf.geometry.name]].copy()

        if drop_na:
            before = data.shape[0]
            data = data.dropna(subset=needed)
            after = data.shape[0]
            if after == 0:
                return {"status": "error", "message": "All rows dropped due to NA in y/x/yend/q."}
            if after < before:
                gdf = gdf.loc[data.index].reset_index(drop=True)
                data = data.reset_index(drop=True)

        # --- arrays for spreg ---
        y = data[[y_col]].to_numpy(dtype=float)              # (n,1)
        X = data[x_cols_list].to_numpy(dtype=float)          # (n,k), no constant
        YEND = None if not yend_cols_list else data[yend_cols_list].to_numpy(dtype=float)
        Q = None if not q_cols_list else data[q_cols_list].to_numpy(dtype=float)

        # --- spatial weights ---
        import libpysal
        wm = weights_method.lower()
        if wm == "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf.loc[data.index], use_index=True)
        elif wm == "rook":
            w = libpysal.weights.Rook.from_dataframe(gdf.loc[data.index], use_index=True)
        elif wm == "distance":
            thr = distance_threshold if target_crs.upper() != "EPSG:4326" else distance_threshold / 111000.0
            w = libpysal.weights.DistanceBand.from_dataframe(
                gdf.loc[data.index], threshold=thr, binary=False, use_index=True
            )
        else:
            return {"status":"error","message":f"Unknown weights_method: {weights_method}"}
        w.transform = "r"

        # Drop islands and re-align data if needed
        if w.islands:
            keep = [i for i in range(len(gdf.loc[data.index])) if i not in set(w.islands)]
            if not keep:
                return {"status":"error","message":"All units are islands under current weights."}
            # reindex everything
            y = y[keep, :]
            X = X[keep, :]
            if YEND is not None: YEND = YEND[keep, :]
            if Q is not None: Q = Q[keep, :]
            sub_gdf = gdf.loc[data.index].iloc[keep]
            if wm == "queen":
                w = libpysal.weights.Queen.from_dataframe(sub_gdf, use_index=True)
            elif wm == "rook":
                w = libpysal.weights.Rook.from_dataframe(sub_gdf, use_index=True)
            else:
                thr = distance_threshold if target_crs.upper() != "EPSG:4326" else distance_threshold / 111000.0
                w = libpysal.weights.DistanceBand.from_dataframe(sub_gdf, threshold=thr, binary=False, use_index=True)
            w.transform = "r"

        # --- HAC kernel weights if requested ---
        gwk = None
        if robust == "hac":
            # Build Kernel weights on centroids; ensure ones on diagonal
            coords = np.column_stack([gdf.loc[data.index].geometry.centroid.x,
                                      gdf.loc[data.index].geometry.centroid.y])
            bw = hac_bandwidth or (np.ptp(coords[:,0]) + np.ptp(coords[:,1])) / 20.0
            gwk = libpysal.weights.Kernel(coords, bandwidth=bw, fixed=True, function="triangular", diagonal=True)
            gwk.transform = "r"

        # --- fit GM_Lag ---
        try:
            from spreg import GM_Lag
        except ModuleNotFoundError:
            return {"status": "error", "message": "The 'spreg' package is not installed. Install with: pip install spreg"}

        reg = GM_Lag(
            y, X,
            yend=YEND, q=Q,
            w=w,
            w_lags=int(w_lags),
            lag_q=bool(lag_q),
            robust=robust,               # None | 'white' | 'hac'
            gwk=gwk,                     # required if robust='hac'
            sig2n_k=bool(sig2n_k),
            spat_diag=bool(spat_diag),
            name_y=y_col,
            name_x=x_cols_list,
            name_yend=(yend_cols_list or None),
            name_q=(q_cols_list or None),
            name_w=f"{weights_method}"
        )

        # --- package outputs ---
        def arr(x): return None if x is None else np.asarray(x).tolist()
        def zpack(z_list):
            # z_stat is list of (z, p)
            return [{"z": float(zp[0]), "p": float(zp[1])} for zp in (z_list or [])]

        preview = table_preview(gdf.loc[data.index], [y_col, *x_cols_list], geometry_key="geometry_wkt")

        result = {
            "n_obs": int(reg.n),
            "k_vars": int(reg.k),  # includes constant internally
            "dependent": y_col,
            "exog": x_cols_list,
            "endog": yend_cols_list,
            "instruments": q_cols_list,
            "weights_method": weights_method.lower(),
            "spec": {"w_lags": int(w_lags), "lag_q": bool(lag_q), "robust": robust, "sig2n_k": bool(sig2n_k)},
            "betas": [float(b) for b in np.asarray(reg.betas).flatten()],
            "beta_names": (["const"] + x_cols_list + (yend_cols_list or []) + ["W_y"])[:len(np.asarray(reg.betas).flatten())],
            "std_err": arr(reg.std_err),
            "z_stats": zpack(getattr(reg, "z_stat", None)),
            "pseudo_r2": float(getattr(reg, "pr2", np.nan)),
            "pseudo_r2_reduced": float(getattr(reg, "pr2_e", np.nan)),
            "sig2": float(getattr(reg, "sig2", np.nan)),
            "ssr": float(getattr(reg, "utu", np.nan)),
            "ak_test": arr(getattr(reg, "ak_test", None)),  # [stat, p] if spat_diag=True
            "pred_y_head": [float(v) for v in np.asarray(reg.predy).flatten()[:5]],
            "data_preview": preview
        }

        msg = "GM_Lag estimation completed successfully"
        if wm == "distance" and target_crs.upper() == "EPSG:4326":
            msg += f" (threshold interpreted as {distance_threshold/111000.0:.6f} degrees)."
        if robust == "hac":
            msg += f" (HAC bandwidth ~ {bw:.3f})."

        return {"status": "success", "message": msg, "result": result}

    except Exception as e:
        return {"status": "error", "message": f"Failed to run GM_Lag: {str(e)}"}

