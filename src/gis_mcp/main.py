""" GIS MCP Server - Main entry point

This module implements an MCP server that connects LLMs to GIS operations using
Shapely and PyProj libraries, enabling AI assistants to perform geospatial operations
and transformations.
"""

import logging
import argparse
import sys
import os
import json
from .mcp import gis_mcp
from .storage_config import initialize_storage, parse_storage_config_arg, get_storage_adapter
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
)

# Import storage endpoints to register HTTP routes (for HTTP/SSE transport)
try:
    from . import storage_endpoints
except ImportError as e:
    import logging
    logging.warning(f"Storage endpoints could not be imported: {e}")

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
    parser.add_argument("--storage-path", type=str, default=None,
                       help="Path to storage folder for file operations (default: ~/.gis_mcp/data/)")
    parser.add_argument(
        "--storage-config",
        type=str,
        default=None,
        help=(
            'JSON object or path to JSON file configuring storage backend, e.g. '
            '\'{"provider":"gcp","bucket":"my-bucket","prefix":"gis-data/"}\''
        ),
    )
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Initialize storage configuration.
    # Priority:
    #   1. --storage-config
    #   2. GIS_MCP_STORAGE_CONFIG / GIS_MCP_STORAGE_PROVIDER env
    #   3. GIS_MCP_STORAGE_PATH env (overrides --storage-path)
    #   4. --storage-path
    #   5. default ~/.gis_mcp/data/
    try:
        cli_storage_config = parse_storage_config_arg(args.storage_config)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error(f"Invalid --storage-config: {e}")
        sys.exit(1)

    if cli_storage_config is not None:
        storage_config = cli_storage_config
    elif os.getenv("GIS_MCP_STORAGE_CONFIG") or os.getenv("GIS_MCP_STORAGE_PROVIDER"):
        storage_config = None  # initialize_storage reads structured env config
    else:
        storage_config = os.getenv("GIS_MCP_STORAGE_PATH", args.storage_path)

    try:
        storage_path = initialize_storage(storage_config)
    except (ValueError, ImportError, FileNotFoundError) as e:
        logger.error(f"Failed to initialize storage: {e}")
        sys.exit(1)

    adapter = get_storage_adapter()
    logger.info(f"Storage initialized ({adapter.describe()})")
    logger.info(f"Local storage path: {storage_path}")
    
    # Get transport configuration from environment variables
    transport = os.getenv('GIS_MCP_TRANSPORT', 'stdio').lower()
    
    try:
        if transport == 'stdio':
            # Default stdio transport
            print("Starting GIS MCP server with STDIO transport...")
            logger.info("STDIO transport enabled (default)")
            gis_mcp.run()
        else:
            # HTTP transport configuration
            host = os.getenv('GIS_MCP_HOST', '0.0.0.0')
            port = int(os.getenv('GIS_MCP_PORT', '8080'))
            
            print(f"Starting GIS MCP server with {transport} transport on {host}:{port}")
            print(f"\nAvailable endpoints:")
            if transport == 'sse':
                print(f"  - MCP (SSE): http://{host}:{port}/sse")
            else:
                print(f"  - MCP (HTTP): http://{host}:{port}/mcp")
            print(f"  - Storage upload: http://{host}:{port}/storage/upload")
            print(f"  - Storage download: http://{host}:{port}/storage/download")
            print(f"  - Storage list: http://{host}:{port}/storage/list")
            print(f"\nFor detailed endpoint documentation, visit: https://gis-mcp.com/endpoints/")
            logger.info(f"{transport} transport enabled - {host}:{port}")
            
            gis_mcp.run(transport=transport, host=host, port=port)
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
