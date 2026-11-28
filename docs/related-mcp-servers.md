# Related MCP Servers

This page lists other MCP servers that complement GIS MCP Server and can be used together to build comprehensive geospatial AI workflows.

## GeoServer MCP

**Repository:** [mahdin75/geoserver-mcp](https://github.com/mahdin75/geoserver-mcp/)

**Description:** A Model Context Protocol (MCP) server implementation that connects LLMs to the GeoServer REST API.

**Use Cases:**

- Managing GeoServer workspaces and layers
- Querying and updating feature data
- Generating styled map images
- Creating and applying SLD styles

**Key Features:**

- Workspace and layer management
- CQL query support for vector data
- Feature update and deletion operations
- Map generation with custom styles
- SLD style creation and application

**Installation:**

```bash
pip install geoserver-mcp
```

**Documentation:** [GitHub Repository](https://github.com/mahdin75/geoserver-mcp/)

---

## DC Hub

**Repository:** [azmartone67/dchub-mcp-server](https://github.com/azmartone67/dchub-mcp-server)

**Description:** DC Hub is the live data layer for data-center site selection. Its Data Center Power Index (DCPI) is a daily score of where data centers can get grid power, across 300+ markets. It complements GIS MCP Server: DC Hub supplies the power, grid, gas and fiber context for a candidate site, and GIS MCP Server does the geometry work around it (buffers, distances, overlays).

**Use Cases:**

- Screening candidate parcels or metros for grid power before running spatial analysis
- Pulling nearby substations, transmission, gas and fiber assets for a site, then measuring distances with GIS MCP Server
- Comparing markets on power availability, energy prices and interconnection queues

**Key Features:**

- Daily DCPI market scores across 300+ markets
- Live grid feeds from the seven US ISOs (PJM, ERCOT, CAISO, MISO, SPP, NYISO, ISO-NE)
- Mapped power, grid, gas and fiber assets
- Answers carry an as-of date and a citation line

**Installation:**

No install. It is a hosted remote server over streamable HTTP at `https://dchub.cloud/mcp`. In Claude Desktop, add it under Settings, Connectors, Add custom connector. In Cursor, add it as a `url` entry in `mcp.json`. Previews need no key; a free key adds a daily allowance of full answers.

**Documentation:** [GitHub Repository](https://github.com/azmartone67/dchub-mcp-server)

---

## Using Multiple MCP Servers Together

You can configure multiple MCP servers in your client (Claude Desktop or Cursor IDE) to leverage different capabilities:

**Example Configuration (Claude Desktop):**

```json
{
  "mcpServers": {
    "gis-mcp": {
      "command": "/path/to/.venv/bin/gis-mcp",
      "args": []
    },
    "geoserver-mcp": {
      "command": "/path/to/.venv/bin/geoserver-mcp",
      "args": [
        "--url",
        "http://localhost:8080/geoserver",
        "--user",
        "admin",
        "--password",
        "geoserver"
      ]
    }
  }
}
```

This allows your AI assistant to:

- Perform geospatial analysis using GIS MCP Server (Shapely, PyProj, GeoPandas, Rasterio, PySAL)
- Manage and query GeoServer instances using GeoServer MCP
- Combine both capabilities for comprehensive geospatial workflows

---

## Contributing

Know of another MCP server that complements GIS MCP Server? We'd love to add it to this list! Please open an issue or submit a pull request with the details.
