"""Shapely-related MCP tool functions and resource listings."""
import os
import logging
from typing import Any, Dict, List, Optional
from .mcp import gis_mcp

# Configure logging
logger = logging.getLogger(__name__)

# Resource handlers for Shapely operations
@gis_mcp.resource("gis://operations/basic")
def get_basic_operations() -> Dict[str, List[str]]:
    """List available basic geometric operations."""
    return {
        "operations": [
            "buffer",
            "intersection",
            "union",
            "difference",
            "symmetric_difference"
        ]
    }

@gis_mcp.resource("gis://operations/geometric")
def get_geometric_properties() -> Dict[str, List[str]]:
    """List available geometric property operations."""
    return {
        "operations": [
            "convex_hull",
            "envelope",
            "minimum_rotated_rectangle",
            "get_centroid",
            "get_bounds",
            "get_coordinates",
            "get_geometry_type"
        ]
    }

@gis_mcp.resource("gis://operations/transformations")
def get_transformations() -> Dict[str, List[str]]:
    """List available geometric transformations."""
    return {
        "operations": [
            "rotate_geometry",
            "scale_geometry",
            "translate_geometry"
        ]
    }

@gis_mcp.resource("gis://operations/advanced")
def get_advanced_operations() -> Dict[str, List[str]]:
    """List available advanced operations."""
    return {
        "operations": [
            "triangulate_geometry",
            "voronoi",
            "unary_union_geometries"
        ]
    }

@gis_mcp.resource("gis://operations/measurements")
def get_measurements() -> Dict[str, List[str]]:
    """List available measurement operations."""
    return {
        "operations": [
            "get_length",
            "get_area"
        ]
    }

@gis_mcp.resource("gis://operations/validation")
def get_validation_operations() -> Dict[str, List[str]]:
    """List available validation operations."""
    return {
        "operations": [
            "is_valid",
            "make_valid",
            "simplify"
        ]
    }

@gis_mcp.resource("gis://operations/shapely_util")
def get_shapely_util_operations() -> Dict[str, List[str]]:
    """List available Shapely utility/advanced operations."""
    return {
        "operations": [
            "snap_geometry",
            "nearest_point_on_geometry",
            "normalize_geometry",
            "geometry_to_geojson",
            "geojson_to_geometry"
        ]
    }

# Basic geometric operations
@gis_mcp.tool()
def buffer(geometry: str, distance: float, resolution: int = 16, 
        join_style: int = 1, mitre_limit: float = 5.0, 
        single_sided: bool = False) -> Dict[str, Any]:
    """Create a buffer around a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        buffered = geom.buffer(
            distance=distance,
            resolution=resolution,
            join_style=join_style,
            mitre_limit=mitre_limit,
            single_sided=single_sided
        )
        return {
            "status": "success",
            "geometry": buffered.wkt,
            "message": "Buffer created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating buffer: {str(e)}")
        raise ValueError(f"Failed to create buffer: {str(e)}")

@gis_mcp.tool()
def intersection(geometry1: str, geometry2: str) -> Dict[str, Any]:
    """Find intersection of two geometries."""
    try:
        from shapely import wkt
        geom1 = wkt.loads(geometry1)
        geom2 = wkt.loads(geometry2)
        result = geom1.intersection(geom2)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Intersection created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating intersection: {str(e)}")
        raise ValueError(f"Failed to create intersection: {str(e)}")

@gis_mcp.tool()
def union(geometry1: str, geometry2: str) -> Dict[str, Any]:
    """Combine two geometries."""
    try:
        from shapely import wkt
        geom1 = wkt.loads(geometry1)
        geom2 = wkt.loads(geometry2)
        result = geom1.union(geom2)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Union created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating union: {str(e)}")
        raise ValueError(f"Failed to create union: {str(e)}")

@gis_mcp.tool()
def difference(geometry1: str, geometry2: str) -> Dict[str, Any]:
    """Find difference between geometries."""
    try:
        from shapely import wkt
        geom1 = wkt.loads(geometry1)
        geom2 = wkt.loads(geometry2)
        result = geom1.difference(geom2)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Difference created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating difference: {str(e)}")
        raise ValueError(f"Failed to create difference: {str(e)}")

@gis_mcp.tool()
def symmetric_difference(geometry1: str, geometry2: str) -> Dict[str, Any]:
    """Find symmetric difference between geometries."""
    try:
        from shapely import wkt
        geom1 = wkt.loads(geometry1)
        geom2 = wkt.loads(geometry2)
        result = geom1.symmetric_difference(geom2)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Symmetric difference created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating symmetric difference: {str(e)}")
        raise ValueError(f"Failed to create symmetric difference: {str(e)}")

# Geometric properties
@gis_mcp.tool()
def convex_hull(geometry: str) -> Dict[str, Any]:
    """Calculate convex hull of a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        result = geom.convex_hull
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Convex hull created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating convex hull: {str(e)}")
        raise ValueError(f"Failed to create convex hull: {str(e)}")

@gis_mcp.tool()
def envelope(geometry: str) -> Dict[str, Any]:
    """Get bounding box of a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        result = geom.envelope
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Envelope created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating envelope: {str(e)}")
        raise ValueError(f"Failed to create envelope: {str(e)}")

@gis_mcp.tool()
def minimum_rotated_rectangle(geometry: str) -> Dict[str, Any]:
    """Get minimum rotated rectangle of a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        result = geom.minimum_rotated_rectangle
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Minimum rotated rectangle created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating minimum rotated rectangle: {str(e)}")
        raise ValueError(f"Failed to create minimum rotated rectangle: {str(e)}")

@gis_mcp.tool()
def get_centroid(geometry: str) -> Dict[str, Any]:
    """Get the centroid of a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        result = geom.centroid
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Centroid calculated successfully"
        }
    except Exception as e:
        logger.error(f"Error calculating centroid: {str(e)}")
        raise ValueError(f"Failed to calculate centroid: {str(e)}")

@gis_mcp.tool()
def get_bounds(geometry: str) -> Dict[str, Any]:
    """Get the bounds of a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        return {
            "status": "success",
            "bounds": list(geom.bounds),
            "message": "Bounds calculated successfully"
        }
    except Exception as e:
        logger.error(f"Error calculating bounds: {str(e)}")
        raise ValueError(f"Failed to calculate bounds: {str(e)}")

@gis_mcp.tool()
def get_coordinates(
    geometry: str,
    precision: Optional[int] = None,
    max_coords: Optional[int] = None,
    offset: int = 0,
) -> Dict[str, Any]:
    """List coordinates of a point or line. precision rounds values. max_coords and offset page long lines."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        coordinates = [list(coord) for coord in geom.coords]
        if precision is not None:
            digits = int(precision)
            coordinates = [[round(float(value), digits) for value in coord] for coord in coordinates]
        total = len(coordinates)
        offset = max(0, int(offset))
        if max_coords is not None:
            coordinates = coordinates[offset : offset + max(0, int(max_coords))]
        elif offset:
            coordinates = coordinates[offset:]
        return {
            "status": "success",
            "coordinate_count": total,
            "offset": offset,
            "truncated": offset + len(coordinates) < total,
            "coordinates": coordinates,
            "message": "Coordinates retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error getting coordinates: {str(e)}")
        raise ValueError(f"Failed to get coordinates: {str(e)}")

@gis_mcp.tool()
def get_geometry_type(geometry: str) -> Dict[str, Any]:
    """Get the type of a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        return {
            "status": "success",
            "type": geom.geom_type,
            "message": "Geometry type retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting geometry type: {str(e)}")
        raise ValueError(f"Failed to get geometry type: {str(e)}")

# Transformations
@gis_mcp.tool()
def rotate_geometry(geometry: str, angle: float, origin: str = "center", 
                use_radians: bool = False) -> Dict[str, Any]:
    """Rotate a geometry."""
    try:
        from shapely import wkt
        from shapely.affinity import rotate
        geom = wkt.loads(geometry)
        result = rotate(geom, angle=angle, origin=origin, use_radians=use_radians)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Geometry rotated successfully"
        }
    except Exception as e:
        logger.error(f"Error rotating geometry: {str(e)}")
        raise ValueError(f"Failed to rotate geometry: {str(e)}")

@gis_mcp.tool()
def scale_geometry(geometry: str, xfact: float, yfact: float, 
                origin: str = "center") -> Dict[str, Any]:
    """Scale a geometry."""
    try:
        from shapely import wkt
        from shapely.affinity import scale
        geom = wkt.loads(geometry)
        result = scale(geom, xfact=xfact, yfact=yfact, origin=origin)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Geometry scaled successfully"
        }
    except Exception as e:
        logger.error(f"Error scaling geometry: {str(e)}")
        raise ValueError(f"Failed to scale geometry: {str(e)}")

@gis_mcp.tool()
def translate_geometry(geometry: str, xoff: float, yoff: float, 
                    zoff: float = 0.0) -> Dict[str, Any]:
    """Translate a geometry."""
    try:
        from shapely import wkt
        from shapely.affinity import translate
        geom = wkt.loads(geometry)
        result = translate(geom, xoff=xoff, yoff=yoff, zoff=zoff)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Geometry translated successfully"
        }
    except Exception as e:
        logger.error(f"Error translating geometry: {str(e)}")
        raise ValueError(f"Failed to translate geometry: {str(e)}")

# Advanced operations
@gis_mcp.tool()
def triangulate_geometry(geometry: str) -> Dict[str, Any]:
    """Create a triangulation of a geometry."""
    try:
        from shapely import wkt
        from shapely.ops import triangulate
        geom = wkt.loads(geometry)
        triangles = triangulate(geom)
        return {
            "status": "success",
            "geometries": [tri.wkt for tri in triangles],
            "message": "Triangulation created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating triangulation: {str(e)}")
        raise ValueError(f"Failed to create triangulation: {str(e)}")

@gis_mcp.tool()
def voronoi(geometry: str) -> Dict[str, Any]:
    """Create a Voronoi diagram from points."""
    try:
        from shapely import wkt
        from shapely.ops import voronoi_diagram
        geom = wkt.loads(geometry)
        result = voronoi_diagram(geom)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Voronoi diagram created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating Voronoi diagram: {str(e)}")
        raise ValueError(f"Failed to create Voronoi diagram: {str(e)}")

@gis_mcp.tool()
def unary_union_geometries(geometries: List[str]) -> Dict[str, Any]:
    """Create a union of multiple geometries."""
    try:
        from shapely import wkt
        from shapely.ops import unary_union
        geoms = [wkt.loads(g) for g in geometries]
        result = unary_union(geoms)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Union created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating union: {str(e)}")
        raise ValueError(f"Failed to create union: {str(e)}")

# Measurements
@gis_mcp.tool()
def get_length(geometry: str) -> Dict[str, Any]:
    """Get the length of a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        return {
            "status": "success",
            "length": float(geom.length),
            "message": "Length calculated successfully"
        }
    except Exception as e:
        logger.error(f"Error calculating length: {str(e)}")
        raise ValueError(f"Failed to calculate length: {str(e)}")

@gis_mcp.tool()
def get_area(geometry: str) -> Dict[str, Any]:
    """Get the area of a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        return {
            "status": "success",
            "area": float(geom.area),
            "message": "Area calculated successfully"
        }
    except Exception as e:
        logger.error(f"Error calculating area: {str(e)}")
        raise ValueError(f"Failed to calculate area: {str(e)}")

# Validation operations
@gis_mcp.tool()
def is_valid(geometry: str) -> Dict[str, Any]:
    """Check if a geometry is valid."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        return {
            "status": "success",
            "is_valid": bool(geom.is_valid),
            "message": "Geometry validation completed successfully"
        }
    except Exception as e:
        logger.error(f"Error validating geometry: {str(e)}")
        raise ValueError(f"Failed to validate geometry: {str(e)}")

@gis_mcp.tool()
def make_valid(geometry: str) -> Dict[str, Any]:
    """Make a geometry valid."""
    try:
        from shapely import wkt, make_valid
        geom = wkt.loads(geometry)
        result = make_valid(geom)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Geometry made valid successfully"
        }
    except Exception as e:
        logger.error(f"Error making geometry valid: {str(e)}")
        raise ValueError(f"Failed to make geometry valid: {str(e)}")

@gis_mcp.tool()
def simplify(geometry: str, tolerance: float, 
            preserve_topology: bool = True) -> Dict[str, Any]:
    """Simplify a geometry."""
    try:
        from shapely import wkt
        geom = wkt.loads(geometry)
        result = geom.simplify(tolerance=tolerance, preserve_topology=preserve_topology)
        return {
            "status": "success",
            "geometry": result.wkt,
            "message": "Geometry simplified successfully"
        }
    except Exception as e:
        logger.error(f"Error simplifying geometry: {str(e)}")
        raise ValueError(f"Failed to simplify geometry: {str(e)}")

# Utility operations (already existed)
@gis_mcp.tool()
def snap_geometry(geometry1: str, geometry2: str, tolerance: float) -> Dict[str, Any]:
    """
    Snap one geometry to another using shapely.ops.snap.
    Args:
        geometry1: WKT string of the geometry to be snapped.
        geometry2: WKT string of the reference geometry.
        tolerance: Distance tolerance for snapping.
    Returns:
        Dictionary with status, message, and snapped geometry as WKT.
    """
    try:
        from shapely import wkt
        from shapely.ops import snap
        geom1 = wkt.loads(geometry1)
        geom2 = wkt.loads(geometry2)
        snapped = snap(geom1, geom2, tolerance)
        return {
            "status": "success",
            "geometry": snapped.wkt,
            "message": "Geometry snapped successfully"
        }
    except Exception as e:
        logger.error(f"Error in snap_geometry: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def nearest_point_on_geometry(geometry1: str, geometry2: str) -> Dict[str, Any]:
    """
    Find the nearest point on geometry2 to geometry1 using shapely.ops.nearest_points.
    Args:
        geometry1: WKT string of the first geometry (e.g., a point).
        geometry2: WKT string of the second geometry.
    Returns:
        Dictionary with status, message, and the nearest point as WKT.
    """
    try:
        from shapely import wkt
        from shapely.ops import nearest_points
        geom1 = wkt.loads(geometry1)
        geom2 = wkt.loads(geometry2)
        p1, p2 = nearest_points(geom1, geom2)
        return {
            "status": "success",
            "nearest_point": p2.wkt,
            "message": "Nearest point found successfully"
        }
    except Exception as e:
        logger.error(f"Error in nearest_point_on_geometry: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def normalize_geometry(geometry: str) -> Dict[str, Any]:
    """
    Normalize the orientation/order of a geometry using shapely.normalize.
    Args:
        geometry: WKT string of the geometry.
    Returns:
        Dictionary with status, message, and normalized geometry as WKT.
    """
    try:
        from shapely import wkt, normalize
        geom = wkt.loads(geometry)
        normalized = normalize(geom)
        return {
            "status": "success",
            "geometry": normalized.wkt,
            "message": "Geometry normalized successfully"
        }
    except Exception as e:
        logger.error(f"Error in normalize_geometry: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def geometry_to_geojson(geometry: str) -> Dict[str, Any]:
    """
    Convert a Shapely geometry (WKT) to GeoJSON using shapely.geometry.mapping.
    Args:
        geometry: WKT string of the geometry.
    Returns:
        Dictionary with status, message, and GeoJSON representation.
    """
    try:
        from shapely import wkt
        from shapely.geometry import mapping
        geom = wkt.loads(geometry)
        geojson = mapping(geom)
        return {
            "status": "success",
            "geojson": geojson,
            "message": "Geometry converted to GeoJSON successfully"
        }
    except Exception as e:
        logger.error(f"Error in geometry_to_geojson: {str(e)}")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def geojson_to_geometry(geojson: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert GeoJSON to a Shapely geometry using shapely.geometry.shape.
    Args:
        geojson: GeoJSON dictionary.
    Returns:
        Dictionary with status, message, and geometry as WKT.
    """
    try:
        from shapely.geometry import shape
        geom = shape(geojson)
        return {
            "status": "success",
            "geometry": geom.wkt,
            "message": "GeoJSON converted to geometry successfully"
        }
    except Exception as e:
        logger.error(f"Error in geojson_to_geometry: {str(e)}")
        return {"status": "error", "message": str(e)}
