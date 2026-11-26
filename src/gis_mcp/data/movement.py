import logging
from pathlib import Path
from typing import Optional, Dict, Any
import osmnx as ox
import networkx as nx

from ..mcp import gis_mcp
from ..storage_config import get_storage_path, resolve_path

logger = logging.getLogger(__name__)

@gis_mcp.resource("gis://operations/movement")
def get_movement_operations() -> dict:
    """List available movement operations."""
    return {"operations": ["download_street_network", "calculate_shortest_path"]}

@gis_mcp.tool()
def download_street_network(place: str, network_type: str = "drive", file_path: str = None, custom_filter: str = None) -> Dict[str, Any]:
    """
    Download a street network for a given place using OSMnx.
    Args:
        place: Name of the place (e.g., "Los Angeles, California, USA")
        network_type: Type of network ("drive", "walk", "bike", etc.). Ignored if custom_filter is provided.
        file_path: Optional. Full path where the GraphML file will be saved. If not set, saves to default location.
        custom_filter: Optional. OSMnx custom filter string to specify which roads to download (e.g., '["highway"~"motorway|trunk|primary"]').
    Returns:
        NetworkX graph as GraphML file path or error message.
    """
    try:
        if custom_filter is not None:
            G = ox.graph_from_place(place, custom_filter=custom_filter)
        else:
            G = ox.graph_from_place(place, network_type=network_type)
        if file_path is not None:
            file_path = resolve_path(file_path, relative_to_storage=True)
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Use storage path with movement_data subdirectory
            storage = get_storage_path()
            out_dir = storage / "movement_data"
            out_dir.mkdir(parents=True, exist_ok=True)
            file_path = out_dir / f"{place.replace(',', '').replace(' ', '_')}_{network_type if custom_filter is None else 'custom'}.graphml"
        ox.save_graphml(G, file_path)
        logger.info(f"Saved street network for {place} to {file_path}")
        return {"status": "success", "file_path": str(file_path)}
    except Exception as e:
        logger.exception("Failed to download street network")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def calculate_shortest_path(graphml_path: str, origin: tuple, destination: tuple, max_nodes: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate the shortest path between two points using a saved street network.
    Args:
        graphml_path: Path to the saved GraphML file
        origin: (lat, lon) tuple for the origin
        destination: (lat, lon) tuple for the destination
    Returns:
        List of node IDs representing the shortest path or error message.
    """
    try:
        G = ox.load_graphml(graphml_path)
        orig_node = ox.nearest_nodes(G, origin[1], origin[0])
        dest_node = ox.nearest_nodes(G, destination[1], destination[0])
        path = nx.shortest_path(G, orig_node, dest_node, weight="length")
        logger.info(f"Calculated shortest path from {origin} to {destination}")
        try:
            length_m = float(nx.path_weight(G, path, weight="length"))
        except Exception:
            length_m = None
        if max_nodes is None:
            returned = path
            truncated = False
        else:
            max_nodes = max(0, int(max_nodes))
            truncated = len(path) > max_nodes
            returned = path[:max_nodes] if truncated else path
        return {
            "status": "success",
            "node_count": len(path),
            "length_m": length_m,
            "truncated": truncated,
            "path": returned,
        }
    except Exception as e:
        logger.exception("Failed to calculate shortest path")
        return {"status": "error", "message": str(e)}
