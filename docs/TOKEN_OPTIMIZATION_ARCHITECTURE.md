# MCP token optimization architecture

GIS-MCP is still one FastMCP server that calls Shapely, PyProj, GeoPandas, Rasterio, and PySAL. The token work changes what is advertised in `tools/list` and what a tool returns. It does not add a model, a router, or an agent loop.

## Catalog path

```text
import tool module
  -> @gis_mcp.tool() registers the function
finalize_catalog()
  -> output_schema = None
  -> short description from descriptions.py
  -> group tag from tool_groups.py
tools/list
  -> FastMCP include_tags / exclude_tags
  -> include_fastmcp_meta is false, so tags are not serialized
```

`src/gis_mcp/__init__.py` finalizes the core tools when the package is imported. `main()` finalizes again after optional extras (visualization, climate, ecology, movement, satellite, land cover, boundaries) have been imported, then applies the module filter.

Server instructions are one short paragraph on the MCP initialize result: geometry strings are WKT, defaults match the full result, and the limit parameters exist. That text is not repeated in every tool.

## Descriptions

`src/gis_mcp/descriptions.py` replaces the published description for tools whose docstrings listed `Args`, `Parameters`, or `Returns`. The replacement is one sentence. Enums the model must choose (`overlay` `how`, spatial-join `predicate`, weights `method`) stay in that sentence because they are how the model picks the operation. They are not copied into JSON Schema `description` fields.

Tools that were already one line, including `buffer` and `intersection`, keep their docstrings.

`merge_gpd`'s old docstring documented parameters the function does not accept. The published sentence matches the implementation: an inner attribute join that keeps the first file's geometry.

## Schemas

Input schemas still come from the Python signature. Required arguments stay required. New arguments are optional and have defaults:

| Argument | Default | Tools |
| --- | --- | --- |
| `max_features`, `offset`, `columns`, `include_geometry`, `precision` | `5`, `0`, none, `false`, `6` | Vector tools that return a preview |
| `bbox`, `simplify` | none | `read_file_gpd` |
| `query`, `limit` | none, `20` (max 50) | `get_available_crs` |
| `precision`, `max_coords`, `offset` | none, none, `0` | `get_coordinates` |
| `max_features`, `offset` | `200`, `0` | `zonal_statistics` |
| `compact` | `true` | `raster_histogram` |
| `max_records` | `100` | Local PySAL tools and ADBSCAN |
| `include_properties` | `false` | Satellite and land-cover downloads |
| `full` | `false` | `get_species_info` |
| `max_nodes` | `200` | `calculate_shortest_path` |

`Dict[str, Any]` no longer produces an output schema. The schema was `{"type":"object","additionalProperties":true}` on every tool.

## Groups and selective exposure

Groups live in `src/gis_mcp/tool_groups.py`. They are server-side tags.

| Group | Contents |
| --- | --- |
| `geometry` | Shapely tools |
| `vector` | GeoPandas tools |
| `raster` | Rasterio tools |
| `crs` | PyProj tools |
| `statistics` | PySAL tools |
| `io` | `save_results` |
| `visualize` | Static and HTML maps |
| `boundaries`, `climate`, `ecology`, `movement`, `satellite`, `landcover` | Optional data tools |

Default: no include filter and no exclude filter, so every tool that registered is listed.

```bash
gis-mcp --modules geometry,vector,crs
gis-mcp --exclude-modules statistics
```

```text
GIS_MCP_MODULES=geometry,vector
GIS_MCP_EXCLUDE=statistics
```

The CLI overrides the environment variable when the flag is passed. Unknown group names are ignored and logged.

This is not dynamic discovery. A client that connected before the filter changed still has the old list until it reconnects. MCP does not give the server a way to avoid sending schemas to a client that asks for every tool. The filter works because the server omits tools from `tools/list` before the client builds its prompt.

Optional integrations are still imported only when their packages import successfully. Core geometry, vector, raster, CRS, and statistics tools do not import those packages.

## Results

`CompactResultMiddleware` in `mcp.py` keeps `structuredContent` by default, so existing clients that read it still get the dict. Set `GIS_MCP_STRUCTURED_CONTENT=0` to send the JSON text only.

`src/gis_mcp/compact.py` builds previews and caps sequences. The defaults match the previous full result:

- Vector pages include WKT and do not round numbers. Pass `include_geometry=false` or `precision` to shrink a preview. `bbox` and `simplify` apply only to the preview of `read_file_gpd`, not to a file the tool writes.
- `cap_sequence` returns the full list when `limit` is omitted. A set limit that the series exceeds becomes `{count, truncated, min, max, mean, head}`.
- STAC responses include `properties` and a `summary`. Pass `include_properties=false` to keep the summary only.
- GBIF species lookup returns the backbone record. Pass `full=false` for the short taxonomy fields.

Weight builders still return the same object under both `result` and `weights_info`.

Geometry operations such as `buffer` still return the full WKT. That is the product of the operation.

## Cache

`src/gis_mcp/gdf_cache.py` stores up to 16 GeoDataFrames keyed by absolute path, mtime, and size. Each read returns a copy. The cache is inside one server process. It does not change tokens by itself. It avoids re-reading the same file during overlay, join, and export.

## What was deliberately not built

- A single `geometry_op` or `spatial_stat` tool. The extra enum and the loss of a specific tool name would cost more in wrong calls than the catalog would save.
- An LLM call inside the server.
- Client-specific tool lists beyond the group filter. The server cannot see which product is connected in a way that is reliable across stdio and HTTP, and guessing would hide tools from clients that need them.

## Compatibility summary

| Change | Effect if you do nothing |
| --- | --- |
| Shorter descriptions | Same tool names and parameters |
| No output schema | No validation change; the old schema accepted any object |
| No `_fastmcp` meta | Clients that do not read FastMCP tags are unchanged |
| Preview includes WKT | Pass `include_geometry=false` to omit it |
| CRS list is the first 100 EPSG records | Pass a smaller `limit` or `query` to search |
| Histogram uses the requested bin count | Pass `compact=true` for at most 32 bins |
| `structuredContent` is still sent | Set `GIS_MCP_STRUCTURED_CONTENT=0` to send the JSON text only |
| Module filter unset | All registered tools are listed |
