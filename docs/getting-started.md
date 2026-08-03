# Getting Started

This guide helps you install and run the GIS MCP Server quickly using pip (with uv) and shows how to connect it to your IDE/client.

For how GIS MCP fits beside the LLM and other tools, and how the server is structured, see **[Architecture](architecture.md)**.

### Prerequisites

- Python 3.10+
- Internet access to install packages

### Install via pip (with uv)

1. Create a virtual environment:

```bash
pip install uv
uv venv --python=3.10
```

2. Install the package:

```bash
uv pip install gis-mcp
```

3. Run the server:

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

When running in HTTP or SSE transport mode, the server provides the following endpoints:

- **MCP endpoint**: `http://localhost:8080/mcp` (HTTP) or `http://localhost:8080/sse` (SSE)
- **Storage endpoints**:
  - `POST /storage/upload` - Upload files to server storage
  - `GET /storage/download?path=<file>` - Download files from server storage
  - `GET /storage/list?path=<dir>` - List files in server storage

For more details on transport modes and complete endpoint documentation, see:

- [HTTP Transport Configuration](http-transport.md)
- [Server Endpoints](endpoints.md)

### Storage Configuration

The GIS MCP Server uses a configurable storage directory for file operations (reading, writing, and downloading data). By default, files are stored in `~/.gis_mcp/data/`.

#### Specifying a Custom Storage Folder

You can specify a custom storage folder using either:

1. **Command-line argument:**

   ```bash
   gis-mcp --storage-path /path/to/your/storage
   ```

2. **Environment variable:**
   ```bash
   export GIS_MCP_STORAGE_PATH=/path/to/your/storage
   gis-mcp
   ```

#### Default Storage Location

If no storage path is specified, the server uses the default location:

- **Default path:** `~/.gis_mcp/data/` (e.g., `/home/username/.gis_mcp/data/` on Linux, `C:\Users\username\.gis_mcp\data\` on Windows)

The storage directory is automatically created if it doesn't exist.

#### How Storage Works

- **File writes:** When you save files using tools like `write_file_gpd`, `write_raster`, or `save_results`, relative paths are resolved relative to the storage directory. Absolute paths are used as-is.
- **Data downloads:** Downloaded data (satellite imagery, climate data, movement networks, etc.) is saved to subdirectories within the storage folder:
  - `movement_data/` - Street networks
  - `land_products/` - Land cover data
  - `satellite_imagery/` - Satellite imagery
  - `ecology_data/` - Species occurrence data
  - `climate_data/` - Climate datasets
  - `administrative_boundaries/` - Administrative boundaries
  - `outputs/` - General output files

#### Example Configuration

For Claude Desktop or Cursor IDE, you can specify the storage path in your configuration:

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/home/YourUsername/.venv/bin/gis-mcp",
      "args": ["--storage-path", "/custom/path/to/storage"]
    }
  }
}
```

Or use an environment variable in your shell configuration (`.bashrc`, `.zshrc`, etc.):

```bash
export GIS_MCP_STORAGE_PATH=/custom/path/to/storage
```

### Connect to an MCP client

Claude Desktop (Windows):

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

Claude Desktop (Linux/Mac):

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

Cursor IDE (Windows) – `.cursor/mcp.json`:

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

Cursor IDE (Linux/Mac) – `.cursor/mcp.json`:

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

This video teaches you the installation of GIS MCP Server on your windows and Claude Desktop:

<iframe width="560" height="315" src="https://www.youtube.com/embed/1u_ra1Wp4es" frameborder="0" allowfullscreen></iframe>

Notes

- Replace `YourUsername` with your actual username
- Restart your IDE after adding configuration

### Optional Features & Extras

GIS MCP Server supports several optional features for specialized workflows. You can install these extras using pip with square brackets, e.g.:

```bash
uv pip install "gis-mcp[climate]"
```

Available extras:

- **climate**: For climate data access and processing (installs `cdsapi`)
- **ecology**: For ecological and biodiversity data (installs `pygbif`)
- **administrative-boundaries**: For working with global administrative boundaries (installs `pygadm`)
- **movement**: For movement and network analysis (installs `osmnx`)
- **satellite-imagery**: For searching and processing satellite imagery (installs `pystac-client`, `planetary-computer`, `xarray`, `stackstac`, `requests`)
- **land-cover**: For land cover data workflows (same as satellite-imagery)
- **all**: Installs all optional dependencies for full functionality

Example to install with multiple extras:

```bash
uv pip install "gis-mcp[climate,ecology,movement]"
```

See the `pyproject.toml` or documentation for the full list of extras and their included packages.

For more information on fetching external datasets (climate, ecology, movement, satellite imagery, and more), see the [Data Gathering guide](data-gathering/README.md).

### Build Your First GIS AI Agent

Ready to create your own AI agent that can perform geospatial operations?

👉 **[Agent Tutorials →](/gis-ai-agent)**

Start with the overview, then follow an available framework guide (LangChain or OpenAI Node.js). Foundation pages cover [agent architecture](gis-ai-agent/architecture.md), [choosing a framework](gis-ai-agent/choosing-framework.md), and [best practices](gis-ai-agent/best-practices.md).

Learn how to:

- Set up the GIS MCP server in HTTP mode
- Build a LangChain agent from scratch (or use the OpenAI Agents SDK in Node.js)
- Connect your agent to GIS tools over MCP
- Apply GIS-specific best practices (CRS, tool selection, validation)

Perfect for developers, data scientists, and anyone interested in building AI-powered geospatial applications.

### Next steps

- Explore the API Reference in the sidebar (Shapely, PyProj, GeoPandas, Rasterio, PySAL)
- Check Installations → Developers for editable installs
