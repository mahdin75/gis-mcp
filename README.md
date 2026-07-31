# GIS MCP Server

[![MCP Toplist](https://mcptoplist.com/badge/mcp.so%2Fgis-mcp-server%2Fmahdin75.svg)](https://mcptoplist.com/server/mcp.so%2Fgis-mcp-server%2Fmahdin75)

<div align="center">

| Category                     | Badges                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Package**                  | [![PyPI version](https://img.shields.io/pypi/v/gis-mcp.svg)](https://pypi.org/project/gis-mcp/) [![PyPI downloads](https://static.pepy.tech/personalized-badge/gis-mcp?period=total&units=international_system&left_color=grey&right_color=blue&left_text=PyPI%20downloads)](https://pepy.tech/project/gis-mcp) [![Tests](https://github.com/mahdin75/gis-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/mahdin75/gis-mcp/actions/workflows/test.yml)                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **Installation & Transport** | [![Docker Installation](https://img.shields.io/badge/Docker-Installation-2496ED?logo=docker&logoColor=white)](https://gis-mcp.com/install/docker/) [![Transport](https://img.shields.io/badge/Transport-HTTP%20%7C%20stdio-blue)](https://github.com/mahdin75/gis-mcp)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **Storage**                  | [![Local Filesystem](https://img.shields.io/badge/Local-Filesystem-4CAF50?logo=files&logoColor=white)](https://gis-mcp.com/storage-configuration/) [![GCP Cloud Storage](https://img.shields.io/badge/GCP-Cloud%20Storage-4285F4?logo=googlecloud&logoColor=white)](https://gis-mcp.com/storage-configuration/)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **Data Sources**             | [![Climate](https://img.shields.io/badge/Climate-Data-B91C1C?logo=weather&logoColor=white)](https://gis-mcp.com/data-gathering/climate/) [![Biodiversity](https://img.shields.io/badge/Biodiversity-Data-4CAF50?logo=leaf&logoColor=white)](https://gis-mcp.com/data-gathering/ecology/) [![LandCover](https://img.shields.io/badge/LandCover-Data-5D4037?logo=map&logoColor=white)](https://gis-mcp.com/data-gathering/land_cover/) [![Movement](https://img.shields.io/badge/Movement-Data-FF6B35?logo=person-walking&logoColor=white)](https://gis-mcp.com/data-gathering/movement/) [![Satellite](https://img.shields.io/badge/Satellite-Imagery-6C5CE7?logo=satellite&logoColor=white)](https://gis-mcp.com/data-gathering/satellite_imagery/) [![Administrative](https://img.shields.io/badge/Administrative-Boundaries-7289DA?logo=map&logoColor=white)](https://gis-mcp.com/data-gathering/administrative_boundaries/) |
| **Agentic AI**               | [![LangChain Agent Example](<https://img.shields.io/badge/LangChain-Agent%20Example%20(Python)-3776AB?logo=langchain&logoColor=white>)](https://gis-mcp.com/gis-ai-agent/langchain) [![OpenAI Agent Example](<https://img.shields.io/badge/OpenAI-Agent%20Example%20(Node.js)-111827?logo=openai&logoColor=white>)](https://gis-mcp.com/gis-ai-agent/openai-nodejs)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **Community**                | [![Discord](https://img.shields.io/badge/Discord-Community-7289DA?logo=discord&logoColor=white)](https://discord.gg/SeVmVhVbk) [![YouTube](https://img.shields.io/badge/YouTube-Tutorials-B91C1C?logo=youtube&logoColor=white)](https://www.youtube.com/@gis-mcp) [![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/mahdin75/gis-mcp)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

</div>

<div align="center">
  <h3>✨ Want to perform accurate geospatial analysis in your chatbot? ✨</h3>
  <p><strong>Install GIS-MCP and transform your AI's spatial capabilities!</strong></p>
  <br/>
  <img src="docs/Logo.png" alt="GIS MCP Server Logo" width="300"/>

  <br/>
</div>

A Model Context Protocol (MCP) server implementation that connects Large Language Models (LLMs) to GIS operations using GIS libraries, enabling AI assistants to perform geospatial operations and transformations.

How it fits next to the LLM and other tools, plus internal components: **[Architecture](https://gis-mcp.com/architecture/)**.

🌐 **Website:** [gis-mcp.com](https://gis-mcp.com)

> Current version is 0.15.0 (Beta):
>
> We welcome contributions and developers to join us in building this project.

## 🎥 Demo

<div align="center">
  <img src="docs/demo.gif" alt="GIS MCP Server Demo" width="800"/>
</div>

## 📋 Table of Contents

- [Features](#-features)
- [Storage](#-storage)
- [Prerequisites](#-prerequisites)
- [Vibe Coding](#vibe-coding)
- [Installation](#-installation)
  - [Docker Installation](#-docker-installation)
  - [pip Installation](#-pip-installation)
  - [Development Installation](#-development-installation)
- [Build Your First GIS AI Agent](#-build-your-first-gis-ai-agent)
- [Available Functions](#-available-functions)
  - [Shapely Functions](#-shapely-functions-29-total)
  - [PyProj Functions](#-pyproj-functions-13-total)
  - [GeoPandas Functions](#-geopandas-functions-13-total)
  - [Rasterio Functions](#-rasterio-functions-20-total)
  - [PySAL Functions](#-pysal-functions-18-total)
  - [Visualization Functions](#-visualization-functions-2-total)
    - [Static Map Functions](#-static-map-functions-1-total)
    - [Interactive Web Map Functions](#-interactive-web-map-functions-1-total)
  - [Administrative Boundaries Functions](#-administrative-boundaries-functions-1-total)
  - [Climate Data Functions](#-climate-data-functions-1-total)
  - [Ecology Data Functions](#-ecology-data-functions-2-total)
  - [Movement Data Functions](#-movement-data-functions-2-total)
  - [Land Cover Data Functions](#-land-cover-data-functions-2-total)
  - [Satellite Imagery Functions](#-satellite-imagery-functions-1-total)
- [Client Development](#-client-development)
- [Planned Features](#-planned-features)
- [Contributing](#-contributing)
- [License](#-license)
- [Related Projects](#-related-projects)
- [Support](#-support)
- [Badges](#-badges)

## 🚀 Features

GIS MCP Server empowers AI assistants with advanced geospatial intelligence. Key features include:

- 🔹 **Comprehensive Geometry Operations** – Perform intersection, union, buffer, difference, and other geometric transformations with ease.
- 🔹 **Advanced Coordinate Transformations** – Effortlessly reproject and transform geometries between coordinate reference systems.
- 🔹 **Accurate Measurements** – Compute distances, areas, lengths, and centroids precisely.
- 🔹 **Spatial Analysis & Validation** – Validate geometries, run proximity checks, and perform spatial overlays or joins.
- 🔹 **Raster & Vector Support** – Process raster layers, compute indices like NDVI, clip, resample, and merge with vector data.
- 🔹 **Spatial Statistics & Modeling** – Leverage PySAL for spatial autocorrelation, clustering, and neighborhood analysis.
- 🔹 **Easy Integration** – Connect seamlessly with MCP-compatible clients like Claude Desktop or Cursor IDE.
- 🔹 **HTTP/SSE Transport** – Run as HTTP service with RESTful storage endpoints for file upload/download operations.
- 🔹 **Flexible Storage** – Local filesystem by default, or Google Cloud Storage when you want files in a GCS bucket.
- 🔹 **Flexible & Extensible** – Supports Python-based GIS libraries and is ready for custom tools or workflow extensions.

> 🌟 **Tip:** With GIS MCP Server, your AI can now “think spatially,” unlocking new capabilities for environmental analysis, mapping, and location intelligence.

---

## 💾 Storage

GIS MCP Server supports two storage backends for file upload, download, and tool outputs:

| Backend | When to use | Configure with |
| ------- | ----------- | -------------- |
| **Local filesystem** | Default; files on disk (including Docker volumes) | `--storage-path` or `GIS_MCP_STORAGE_PATH` |
| **Google Cloud Storage (GCP)** | When you want files in a GCS bucket | `--storage-config` / `GIS_MCP_STORAGE_CONFIG` or `GIS_MCP_STORAGE_PROVIDER=gcp` |

Install GCP support with:

```bash
pip install gis-mcp[gcp]
```

Full setup (paths, IAM, Docker, credentials): [Storage Configuration](https://gis-mcp.com/storage-configuration/).

---

## 📋 Prerequisites

- Python 3.10 or higher
- MCP-compatible client (like Claude Desktop or Cursor)
- Internet connection for package installation

## Vibe Coding

If you’re building agents via vibe coding, use these context files in your editor so the LLM understands the GIS MCP server:

- `llms.txt`: summarized context for smaller windows.
- `llms-full.txt`: full context when your model has a larger window.

## 🛠 Installation

Choose the installation method that best suits your needs:

### 🐳 Docker Installation

GIS MCP Server can be run using Docker, which provides an isolated environment with all dependencies pre-installed.

**Important:** Both `Dockerfile` and `Dockerfile.local` have **HTTP transport mode enabled by default**. The server runs on port `9010` and is accessible at `http://localhost:9010/mcp`.

#### Using Dockerfile

The main `Dockerfile` installs the package from PyPI:

1. Build the Docker image:

```bash
docker build -t gis-mcp .
```

2. Run the container (HTTP mode is enabled by default):

```bash
docker run -p 9010:9010 gis-mcp
```

#### Using Dockerfile.local

The `Dockerfile.local` installs the package from local source files (useful for development or custom builds):

1. Build the Docker image:

```bash
docker build -f Dockerfile.local -t gis-mcp:local .
```

2. Run the container (HTTP mode is enabled by default):

```bash
docker run -p 9010:9010 gis-mcp:local
```

The server will be available at `http://localhost:9010/mcp` in HTTP transport mode.

For more details on Docker configuration and environment variables, see the [Docker installation guide](docs/install/docker.md).

### 📦 pip Installation

The pip installation is recommended for most users:

1. Install uv package manager:

```bash
pip install uv
```

2. Create the Virtual Environment (Python 3.10+):

```bash
uv venv --python=3.10
```

3. Activate the Virtual Environment:

On Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

On Linux:

```bash
source .venv/bin/activate
```

4. Install the package:

```bash
uv pip install gis-mcp
```

#### Install with Visualization Features

To install with visualization capabilities (Folium and PyDeck for interactive maps):

```bash
uv pip install gis-mcp[visualize]
```

This will install additional dependencies:

- `folium>=0.15.0` - For creating interactive web maps
- `pydeck>=0.9.0` - For advanced 3D visualizations

5. Start the server:

```bash
gis-mcp
```

By default, the server runs in **STDIO transport mode**, which is ideal for local development and integration with Claude Desktop or Cursor IDE.

You can also run the server in **HTTP transport mode** for network deployments:

```bash
export GIS_MCP_TRANSPORT=http
export GIS_MCP_PORT=8080
gis-mcp
```

When running in HTTP or SSE transport mode, the following endpoints are available:

- **MCP endpoint**: `http://host:port/mcp` (HTTP) or `http://host:port/sse` (SSE)
- **Storage endpoints**:
  - `POST /storage/upload` - Upload files to server storage
  - `GET /storage/download?path=<file>` - Download files from server storage
  - `GET /storage/list?path=<dir>` - List files in server storage

For more details on transport modes and complete endpoint documentation, see:

- [HTTP Transport Configuration](docs/http-transport.md)
- [Server Endpoints](docs/endpoints.md)

#### pip Configuration

To use the pip installation with Claude or Cursor, add the following configuration:

**Claude Desktop:**

**Windows:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "C:\\Users\\YourUsername\\.venv\\Scripts\\gis-mcp",
      "args": []
    }
  }
}
```

**Linux/Mac:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/home/YourUsername/.venv/bin/gis-mcp",
      "args": []
    }
  }
}
```

**Cursor IDE** (create `.cursor/mcp.json`):

**Windows:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "C:\\Users\\YourUsername\\.venv\\Scripts\\gis-mcp",
      "args": []
    }
  }
}
```

**Linux/Mac:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/home/YourUsername/.venv/bin/gis-mcp",
      "args": []
    }
  }
}
```

After configuration:

1. Make sure to replace `YourUsername` with your actual username
2. For development installation, replace `/path/to/gis-mcp` with the actual path to your project
3. Restart your IDE to apply the changes
4. You can now use all GIS operations through Claude or Cursor!

### 🛠 Development Installation

For contributors and developers:

1. Install uv package manager:

```bash
pip install uv
```

2. Create the Virtual Environment:

```bash
uv venv --python=3.10
```

3. Install the package in development mode:

```bash
uv pip install -e .
```

4. Start the server:

```bash
python -m gis_mcp
```

#### Development Configuration

To use the development installation with Claude or Cursor, add the following configuration:

**Claude Desktop:**

**Windows:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "C:\\path\\to\\gis-mcp\\.venv\\Scripts\\python",
      "args": ["-m", "gis_mcp"]
    }
  }
}
```

**Linux/Mac:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/path/to/gis-mcp/.venv/bin/python",
      "args": ["-m", "gis_mcp"]
    }
  }
}
```

**Cursor IDE** (create `.cursor/mcp.json`):

**Windows:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "C:\\path\\to\\gis-mcp\\.venv\\Scripts\\python",
      "args": ["-m", "gis_mcp"]
    }
  }
}
```

**Linux/Mac:**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/path/to/gis-mcp/.venv/bin/python",
      "args": ["-m", "gis_mcp"]
    }
  }
}
```

After configuration:

1. Make sure to replace `YourUsername` with your actual username
2. For development installation, replace `/path/to/gis-mcp` with the actual path to your project
3. Restart your IDE to apply the changes
4. You can now use all GIS operations through Claude or Cursor!

## 🤖 Build Your First GIS AI Agent

Ready to create your own AI agent that can perform geospatial operations? Our comprehensive tutorial will guide you from zero to hero!

### What You'll Learn

- ✅ How to set up the GIS MCP server in HTTP mode
- ✅ How to build a LangChain agent from scratch
- ✅ How to connect your agent to GIS tools
- ✅ How to use OpenRouter to access multiple AI models (DeepSeek, Gemini, GPT-4, Claude, etc.)
- ✅ How to customize and extend your agent

### Get Started

👉 **[Follow the complete tutorial →](https://gis-mcp.com/gis-ai-agent/)**

📝 **[Read the Medium article →](https://medium.com/@mahdinazari75/build-your-first-gis-ai-agent-by-gis-mcp-server-langchain-c0c1bfa36f6d)**

🎥 **[Watch tutorials on YouTube →](https://www.youtube.com/@gis-mcp)**

The tutorial is beginner-friendly and requires no prior AI or GIS experience. You'll build a working agent that can:

- Calculate distances between points
- Transform coordinates between different systems
- Create buffers around locations
- Perform spatial analysis
- And much more!

**Perfect for**: Developers, data scientists, GIS professionals, and anyone interested in building AI-powered geospatial applications.

## 📚 Available Functions

This section provides a comprehensive list of all available functions organized by library.

### 🔷 Shapely Functions (29 total)

**Basic Geometric Operations:**

- `buffer` - Create buffer around geometry
- `intersection` - Find intersection of two geometries
- `union` - Combine two geometries
- `difference` - Find difference between geometries
- `symmetric_difference` - Find symmetric difference

**Geometric Properties:**

- `convex_hull` - Calculate convex hull
- `envelope` - Get bounding box
- `minimum_rotated_rectangle` - Get minimum rotated rectangle
- `get_centroid` - Get centroid point
- `get_bounds` - Get geometry bounds
- `get_coordinates` - Extract coordinate array
- `get_geometry_type` - Get geometry type name

**Transformations:**

- `rotate_geometry` - Rotate geometry by angle
- `scale_geometry` - Scale geometry by factors
- `translate_geometry` - Move geometry by offset

**Advanced Operations:**

- `triangulate_geometry` - Create triangulation
- `voronoi` - Create Voronoi diagram
- `unary_union_geometries` - Union multiple geometries

**Measurements:**

- `get_length` - Calculate geometry length
- `get_area` - Calculate geometry area

**Validation & Utilities:**

- `is_valid` - Check geometry validity
- `make_valid` - Fix invalid geometry
- `simplify` - Simplify geometry
- `snap_geometry` - Snap to reference geometry
- `nearest_point_on_geometry` - Find nearest point
- `normalize_geometry` - Normalize orientation
- `geometry_to_geojson` - Convert to GeoJSON
- `geojson_to_geometry` - Convert from GeoJSON

### 🔷 PyProj Functions (13 total)

**Coordinate Transformations:**

- `transform_coordinates` - Transform point coordinates
- `project_geometry` - Project geometry between CRS

**CRS Information:**

- `get_crs_info` - Get detailed CRS information
- `get_available_crs` - List available CRS systems
- `get_utm_zone` - Get UTM zone for coordinates
- `get_utm_crs` - Get UTM CRS for coordinates
- `get_geocentric_crs` - Get geocentric CRS

**Geodetic Calculations:**

- `get_geod_info` - Get ellipsoid information
- `calculate_geodetic_distance` - Calculate distance on ellipsoid
- `calculate_geodetic_point` - Calculate point at distance/azimuth
- `calculate_geodetic_area` - Calculate area on ellipsoid

### 🔷 GeoPandas Functions (13 total)

**I/O Operations:**

- `read_file_gpd` - Read geospatial file with preview
- `write_file_gpd` - Export GeoDataFrame to file

**Join & Merge Operations:**

- `append_gpd` - Concatenate GeoDataFrames vertically
- `merge_gpd` - Database-style attribute joins
- `overlay_gpd` - Spatial overlay operations
- `dissolve_gpd` - Dissolve by attribute
- `explode_gpd` - Split multi-part geometries

**Spatial Operations:**

- `clip_vector` - Clip geometries
- `sjoin_gpd` - Spatial joins
- `sjoin_nearest_gpd` - Nearest neighbor spatial joins
- `point_in_polygon` - Point-in-polygon tests

### 🔷 Rasterio Functions (20 total)

**Basic Raster Operations:**

- `metadata_raster` - Get raster metadata
- `get_raster_crs` - Get raster CRS
- `extract_band` - Extract single band
- `raster_band_statistics` - Calculate band statistics
- `raster_histogram` - Compute pixel histograms

**Raster Processing:**

- `clip_raster_with_shapefile` - Clip raster with polygons
- `resample_raster` - Resample by scale factor
- `reproject_raster` - Reproject to new CRS
- `tile_raster` - Split into tiles

**Raster Analysis:**

- `compute_ndvi` - Calculate vegetation index
- `raster_algebra` - Mathematical operations on bands
- `concat_bands` - Combine single-band rasters
- `weighted_band_sum` - Weighted band combination

**Advanced Analysis:**

- `zonal_statistics` - Statistics within polygons
- `reclassify_raster` - Reclassify pixel values
- `focal_statistics` - Moving window statistics
- `hillshade` - Generate hillshade from DEM
- `write_raster` - Write array to raster file

### 🔷 PySAL Functions (18 total)

**Spatial Autocorrelation:**

- `morans_i` - Global Moran's I statistic
- `gearys_c` - Global Geary's C statistic
- `gamma_statistic` - Gamma index
- `getis_ord_g` - Global Getis-Ord G statistic

**Local Statistics:**

- `moran_local` - Local Moran's I
- `getis_ord_g_local` - Local Getis-Ord G\*
- `join_counts_local` - Local join counts

**Global Statistics:**

- `join_counts` - Binary join counts test
- `adbscan` - Adaptive density-based clustering

**Spatial Weights:**

- `weights_from_shapefile` - Create weights from shapefile
- `distance_band_weights` - Distance-based weights
- `knn_weights` - K-nearest neighbors weights
- `build_transform_and_save_weights` - Build, transform, and save weights
- `ols_with_spatial_diagnostics_safe` - OLS regression with spatial diagnostics
- `build_and_transform_weights` - Build and transform weights

**Spatial-Temporal Analysis:**

- `spatial_markov` - Spatial Markov analysis for panel data
- `dynamic_lisa` - Dynamic LISA (directional LISA) analysis

**Spatial Regression:**

- `gm_lag` - GM_Lag spatial 2SLS/GMM-IV spatial lag model

### 🔷 Visualization Functions (2 total)

**Static Map Visualization (Matplotlib/GeoPandas):**

- `create_map` – Generate high-quality static maps (PNG, PDF, JPG) from multiple geospatial data sources including shapefiles, rasters, WKT geometries, and coordinate arrays. Supports multiple layers with individual styling options, legends, titles, and grid overlays.

**Interactive Web Map Visualization (Folium):**

- `create_web_map` – Generate interactive HTML maps using Folium with layer controls, legends, scale bars, dynamic titles, tooltips, and minimap. Supports multiple basemap options and responsive design for web browsers.

### 🔷 Administrative Boundaries Functions (1 total)

**Boundary Download:**

- `download_boundaries` - Download GADM administrative boundaries and save as GeoJSON

### 🔷 Climate Data Functions (1 total)

**Climate Data Download:**

- `download_climate_data` - Download climate data (ERA5 or other CDS datasets)

### 🔷 Ecology Data Functions (2 total)

**Ecology Data Download and Info:**

- `get_species_info` – Retrieve taxonomic information for a given species name
- `download_species_occurrences` – Download occurrence records for a given species and save as JSON

### 🔷 Movement Data Functions (2 total)

**Movement Data Download and Routing (via [OSMnx](https://osmnx.readthedocs.io/en/stable/)):**

- `download_street_network` – Download a street network for a given place and save as GraphML
- `calculate_shortest_path` – Calculate the shortest path between two points using a saved street network

### 🔷 Land Cover Data Functions (2 total)

**Land Cover from Planetary Computer:**

- `download_worldcover` – Download ESA WorldCover for AOI/year; optional crop and reprojection
- `compute_s2_ndvi` – Compute NDVI from Sentinel-2 L2A; crop and reprojection supported

### 🔷 Satellite Imagery Functions (1 total)

**STAC-based Satellite Download:**

- `download_satellite_imagery` – Download and stack bands from STAC items (e.g., Sentinel-2, Landsat), with optional crop and reprojection

**Total Functions Available: 92**

## 🛠 Client Development

Example usage of the tools:

### Buffer Operation

```python
Tool: buffer
Parameters: {
    "geometry": "POINT(0 0)",
    "distance": 10,
    "resolution": 16,
    "join_style": 1,
    "mitre_limit": 5.0,
    "single_sided": false
}
```

### Coordinate Transformation

```python
Tool: transform_coordinates
Parameters: {
    "coordinates": [0, 0],
    "source_crs": "EPSG:4326",
    "target_crs": "EPSG:3857"
}
```

### Geodetic Distance

```python
Tool: calculate_geodetic_distance
Parameters: {
    "point1": [0, 0],
    "point2": [10, 10],
    "ellps": "WGS84"
}
```

### Static Map Creation

```python
Tool: create_map
Parameters: {
    "layers": [
        {
            "data": "buildings.shp",
            "style": {"label": "Buildings", "color": "red", "alpha": 0.7}
        },
        {
            "data": "roads.shp",
            "style": {"label": "Roads", "color": "black", "linewidth": 1}
        }
    ],
    "filename": "city_analysis",
    "filetype": "png",
    "title": "City Infrastructure Analysis",
    "show_grid": true,
    "add_legend": true
}
```

### Interactive Web Map Creation

```python
Tool: create_web_map
Parameters: {
    "layers": [
        {
            "data": "buildings.shp",
            "style": {"label": "Buildings", "color": "red"}
        },
        {
            "data": "parks.geojson",
            "style": {"label": "Parks", "color": "green"}
        }
    ],
    "filename": "city_interactive.html",
    "title": "City Infrastructure Map",
    "basemap": "CartoDB positron",
    "show_grid": true,
    "add_legend": true,
    "add_minimap": true
}
```

## 🔮 Planned Features

- Implement advanced spatial indexing
- Implement network analysis capabilities
- Add support for 3D geometries
- Implement performance optimizations
- Add support for more GIS libraries

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure your PR description clearly describes the problem and solution. Include the relevant issue number if applicable.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Projects

| Project Name                                                                                        | Category                   | Description                                                                                                   |
| --------------------------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------- |
| [Model Context Protocol](https://github.com/modelcontextprotocol/modelcontextprotocol)              | MCP Related                | The core MCP Specification                                                                                    |
| [FastMCP](https://github.com/jlowin/fastmcp)                                                        | MCP Related                | The fast, Pythonic way to build MCP servers and clients                                                       |
| [Shapely](https://github.com/shapely/shapely)                                                       | Geospatial Analysis        | Python package for manipulation and analysis of geometric objects                                             |
| [PyProj](https://github.com/pyproj4/pyproj)                                                         | Geospatial Analysis        | Python interface to PROJ library                                                                              |
| [GeoPandas](https://github.com/geopandas/geopandas)                                                 | Geospatial Analysis        | Python package for working with geospatial data                                                               |
| [Rasterio](https://github.com/rasterio/rasterio)                                                    | Geospatial Analysis        | Python package for reading and writing geospatial raster data                                                 |
| [Fiona](https://github.com/Toblerity/Fiona)                                                         | Geospatial Analysis        | Python interface to OGR library for reading and writing vector geospatial data formats                        |
| [PySAL](https://github.com/pysal/pysal)                                                             | Geospatial Analysis        | Python spatial analysis library for geospatial data science                                                   |
| [Folium](https://github.com/python-visualization/folium)                                            | Visualization              | Python library for creating interactive web maps using Leaflet.js                                             |
| [PyDeck](https://github.com/visgl/deck.gl)                                                          | Visualization              | Python library for creating advanced 3D visualizations and interactive maps                                   |
| [Matplotlib](https://github.com/matplotlib/matplotlib)                                              | Visualization              | Python plotting library for creating static maps and visualizations                                           |
| [cdsapi](https://github.com/ecmwf/cdsapi)                                                           | Geospatial Data Collecting | Python API to access the Copernicus Climate Data Store (CDS)                                                  |
| [pygadm](https://github.com/12rambau/pygadm)                                                        | Geospatial Data Collecting | Easy access to administrative boundary defined by GADM from Python scripts                                    |
| [pygbif](https://github.com/gbif/pygbif)                                                            | Geospatial Data Collecting | Python client for the GBIF API (ecology and biodiversity data)                                                |
| [OSMnx](https://osmnx.readthedocs.io/en/stable/)                                                    | Geospatial Data Collecting | Python package for downloading, modeling, and analyzing street networks and urban features from OpenStreetMap |
| [pystac-client](https://github.com/stac-utils/pystac-client)                                        | Geospatial Data Collecting | Python client for STAC catalogs; search and access spatiotemporal assets                                      |
| [Planetary Computer SDK for Python](https://github.com/microsoft/planetary-computer-sdk-for-python) | Geospatial Data Collecting | Python SDK for Microsoft Planetary Computer; auth and helpers for STAC/COGs                                   |

## 🔗 Related MCP Servers

| Server Name                                                 | Description                                                                                       |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [GeoServer MCP](https://github.com/mahdin75/geoserver-mcp/) | A Model Context Protocol (MCP) server implementation that connects LLMs to the GeoServer REST API |

## 📞 Support

For support, please open an issue in the GitHub repository.

## 💬 Community

Join our Discord community for discussions, updates, and support:

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20our%20community-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/SeVmVhVbk)

## 👥 Contributors

<a href="https://github.com/mahdin75/gis-mcp/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=mahdin75/gis-mcp" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

<br/>

## 🏆 Badges

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/gis-mcp.svg)](https://pypi.org/project/gis-mcp/)
[![PyPI downloads](https://img.shields.io/pypi/dm/gis-mcp.svg)](https://pypi.org/project/gis-mcp/)
<br/></br>

[![MCP Toplist](https://mcptoplist.com/badge/mcp.so%2Fgis-mcp-server%2Fmahdin75.svg)](https://mcptoplist.com/server/mcp.so%2Fgis-mcp-server%2Fmahdin75)
<br/></br>

[![Trust Score](https://archestra.ai/mcp-catalog/api/badge/quality/mahdin75/gis-mcp)](https://archestra.ai/mcp-catalog/mahdin75__gis-mcp)
<br/></br>

  <a href="https://glama.ai/mcp/servers/@mahdin75/gis-mcp">
    <img width="380" height="200" src="https://glama.ai/mcp/servers/@mahdin75/gis-mcp/badge" alt="GIS Server MCP server" />
  </a>
  <br/><br/><br/>
  
  <a href="https://mcp.so/server/gis-mcp-server/mahdin75">
    <img src="https://mcp.so/logo.png" alt="MCP.so Badge" width="150"/>
  </a>


</div>
