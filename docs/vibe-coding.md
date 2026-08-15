# Vibe Coding

GIS MCP is an open-source Model Context Protocol server for GIS/geospatial analysis and AI agents. If you develop agents via vibe coding, give the model these machine-readable maps of the project:

- [`llms.txt`](https://gis-mcp.com/llms.txt): curated summary for smaller context windows.
- [`llms-full.txt`](https://gis-mcp.com/llms-full.txt): full documentation map for larger windows.

They are generated from this documentation during the MkDocs build. Copies also live in the repository root:

- [`llms.txt` (summary)](https://github.com/mahdin75/gis-mcp/blob/main/llms.txt)
- [`llms-full.txt` (full)](https://github.com/mahdin75/gis-mcp/blob/main/llms-full.txt)

How to use:

- Fetch the live URLs above, or pin the repo copies in an MCP-aware editor (Cursor, Claude Desktop, etc.).
- Prefer `llms.txt` first; switch to `llms-full.txt` when the model can handle more detail.
