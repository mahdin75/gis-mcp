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

## CARTO for Agents

**Website:** [carto.com](https://carto.com/)

**Description:** The official remote MCP server for CARTO, a cloud-native GIS platform. Every tool call runs inside your own cloud data warehouse or lakehouse, so it covers the governed, enterprise-scale end of a workflow that GIS MCP Server handles at the library level.

**Use Cases:**

- Browsing governed warehouse data: connections, tables, columns, and column statistics
- Running spatial SQL and geospatial analysis at warehouse scale
- Rendering interactive maps inline in the conversation, or loading saved CARTO Builder maps
- Running an organization's published CARTO Workflows as agent tools

**Key Features:**

- Warehouse-native execution on BigQuery, Snowflake, Databricks, Redshift, or PostgreSQL, with no data copied out
- OAuth 2.0 user-to-machine auth, so the agent inherits the user's permissions and every action is auditable
- Remote server over streamable HTTP, so there is nothing to install locally
- Creating and editing maps and workflows, not only reading them

**Installation:**

Remote server, no install required. Add the organization's endpoint to any MCP client:

```json
{
  "mcpServers": {
    "carto": {
      "url": "https://<region>.api.carto.com/mcp/<account_id>"
    }
  }
}
```

**Documentation:** [CARTO for Agents](https://docs.carto.com/carto-for-agents?utm_source=gis-mcp&utm_medium=listing&utm_campaign=mcp-marketplace-listings)

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
- Query governed warehouse data and render maps using CARTO for Agents
- Combine both capabilities for comprehensive geospatial workflows

---

## Contributing

Know of another MCP server that complements GIS MCP Server? We'd love to add it to this list! Please open an issue or submit a pull request with the details.
