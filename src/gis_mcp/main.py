""" GIS MCP Server - Main entry point

This module implements an MCP server that connects LLMs to GIS operations using
Shapely and PyProj libraries, enabling AI assistants to perform geospatial operations
and transformations.
"""

import logging
import argparse
import sys
from .mcp import gis_mcp
try:
    from .data import administrative_boundaries
except ImportError as e:
    administrative_boundaries = None
    import logging
    logging.warning(f"administrative_boundaries module could not be imported: {e}. Install with 'pip install gis-mcp[administrative-boundaries]' if you need this feature.")
try:
    from .data import climate
except ImportError as e:
    climate = None
    import logging
    logging.warning(f"climate module could not be imported: {e}. Install with 'pip install gis-mcp[climate]' if you need this feature.")
try:
    from .data import ecology
except ImportError as e:
    ecology = None
    import logging
    logging.warning(f"ecology module could not be imported: {e}. Install with 'pip install gis-mcp[ecology]' if you need this feature.")
try:
    from .data import movement
except ImportError as e:
    movement = None
    import logging
    logging.warning(f"movement module could not be imported: {e}. Install with 'pip install gis-mcp[movement]' if you need this feature.")

try:
    from .data import satellite_imagery
except ImportError as e:
    satellite_imagery = None
    import logging
    logging.warning(f"satellite_imagery module could not be imported: {e}. Install with 'pip install gis-mcp[satellite_imagery]' if you need this feature.")

try:
    from .data import land_cover
except ImportError as e:
    land_cover = None
    import logging
    logging.warning(f"land_cover module could not be imported: {e}. Install with 'pip install gis-mcp[land_cover]' if you need this feature.")

try:
    from .visualize import map_tool, web_map_tool
except ImportError as e:
    map_tool = None
    web_map_tool = None
    import logging
    logging.warning(f"Visualization modules could not be imported: {e}. Install with 'pip install gis-mcp[visualize]' if you need this feature.")


import warnings
warnings.filterwarnings('ignore')  # Suppress warnings for cleaner output

# Import tool modules to register MCP tools via decorators
from . import (
    geopandas_functions,
    shapely_functions,
    rasterio_functions,
    pyproj_functions,
    pysal_functions,
    nx_osmnx_functions,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("gis-mcp")

# Create FastMCP instance

def main():
    """Main entry point for the GIS MCP server."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="GIS MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Start the MCP server
        print("Starting GIS MCP server...")
        gis_mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 

