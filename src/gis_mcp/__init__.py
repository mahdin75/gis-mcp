"""GIS MCP Server - A Model Context Protocol server for GIS operations."""

__version__ = "0.16.0"

from .geopandas_functions import *
from .shapely_functions import *
from .rasterio_functions import *
from .pyproj_functions import *
from .pysal_functions import *
from .save_tool import *
from .catalog import finalize_catalog
from .mcp import gis_mcp

finalize_catalog(gis_mcp)