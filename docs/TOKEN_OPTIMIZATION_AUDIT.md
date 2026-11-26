# MCP token optimization audit

This audit describes the GIS-MCP server as it behaved before the token-reduction changes in this branch. Measurements were taken from the registered FastMCP catalog (87 core tools) on 26 November 2026. Optional integrations (satellite, climate, ecology, movement, land cover, visualization, administrative boundaries) are imported only when their packages are installed and are not in the 87-tool count.

Token figures below use **characters / 4** unless a later benchmark file reports a `cl100k_base` count. characters/4 is an estimate. It is not a Claude, Cursor, or ChatGPT bill.

The catalog snapshot is `docs/benchmarks/baseline_summary.json`.

| Catalog piece | Characters | Estimated tokens (chars/4) |
| --- | ---: | ---: |
| Full `tools/list` payload | 46,237 | 11,559 |
| Descriptions | 14,643 | 3,661 |
| Input schemas | 18,110 | 4,528 |
| Output schemas | 3,915 | 979 |
| FastMCP `_meta` | 2,088 | 522 |
| Tools | 87 |  |

Average description: 168 characters. Average input schema: 208 characters.

Clients such as Claude Desktop, Cursor, and ChatGPT place `tools/list` in the model context. That cost is paid on every conversation, not once per tool call. Tool results are paid again on every call. Both are in scope.

## 1. Registered tools

Registration is decorator-based. `src/gis_mcp/mcp.py` creates one `FastMCP("GIS MCP")`. Importing a module runs `@gis_mcp.tool()` and stores the function.

| Group | Module | Tools |
| --- | --- | ---: |
| Geometry | `shapely_functions.py` | 28 |
| Vector | `geopandas_functions.py` | 11 |
| Raster | `rasterio_functions.py` | 18 |
| CRS | `pyproj_functions.py` | 11 |
| Spatial statistics | `pysal_functions.py` | 18 |
| Save | `save_tool.py` (`save_results`) | 1 |

Optional tools, registered from `main.py` only when the extra is installed:

| Group | Module | Tools |
| --- | --- | --- |
| Visualize | `visualize/map_tool.py`, `visualize/web_map_tool.py` | `create_map`, `create_web_map` |
| Boundaries | `data/administrative_boundaries.py` | `download_boundaries` |
| Climate | `data/climate.py` | `download_climate_data` |
| Ecology | `data/ecology.py` | `get_species_info`, `download_species_occurrences` |
| Movement | `data/movement.py` | `download_street_network`, `calculate_shortest_path` |
| Satellite | `data/satellite_imagery.py` | `download_satellite_imagery` |
| Land cover | `data/land_cover.py` | `download_worldcover`, `compute_s2_ndvi` |

There is no GeoServer, PostGIS, or cloud-storage tool in the MCP catalog. Storage is server configuration (`storage_config.py`), not a tool the model must load.

Fourteen MCP resources (`gis://...`) repeat the tool names as lists. They are not part of `tools/list`. A client that reads them spends a second, smaller catalog. They were left in place because some prompts already point at those URIs.

## 2. Descriptions repeat the schema

FastMCP copies the whole docstring into `description`. It also builds `inputSchema` from the type hints. Docstrings written as `Args:` / `Parameters:` / `Returns:` therefore send the same facts twice, and the `Returns:` lines describe the JSON envelope rather than the operation.

Largest descriptions in the baseline:

| Tool | Description characters | Function |
| --- | ---: | --- |
| `merge_gpd` | 678 | `geopandas_functions.merge_gpd` |
| `build_transform_and_save_weights` | 613 | `pysal_functions.build_transform_and_save_weights` |
| `ols_with_spatial_diagnostics_safe` | 601 | `pysal_functions.ols_with_spatial_diagnostics_safe` |
| `raster_algebra` | 508 | `rasterio_functions.raster_algebra` |
| `build_and_transform_weights` | 453 | `pysal_functions.build_and_transform_weights` |
| `sjoin_gpd` | 408 | `geopandas_functions.sjoin_gpd` |
| `metadata_raster` | 373 | `rasterio_functions.metadata_raster` |

`merge_gpd` is also inaccurate: the docstring documents `how`, `on`, `left_on`, and `right_on`, but the function always does an inner join on shared columns. That text costs tokens and can make the model pass arguments the tool does not accept.

Shapely and most PyProj tools were already one sentence (`buffer`: "Create a buffer around a geometry."). Those were left alone. Shortening them further would remove the verb the model uses to pick the tool.

**Proposed change.** Replace long docstrings in the published description with one sentence that names the operation and any enum (`how`, `predicate`, `method`). Leave names and types in the schema. Do not add `Field(description=...)` on every parameter: that copies the sentence into the schema and spends the tokens again.

**Compatibility.** Tool names and parameter names stay the same. Clients that matched on docstring prose rather than the tool name can see a shorter sentence. The enum values that used to live only in the docstring are kept in the one-line description.

**Benefit.** The long tail above is several thousand characters. Measured after the change in `docs/TOKEN_OPTIMIZATION_BENCHMARK.md`.

## 3. Empty output schemas

Every tool is annotated `-> Dict[str, Any]`. FastMCP 2.13 turns that into:

```json
{"additionalProperties": true, "type": "object"}
```

That schema does not constrain the result. It was 3,915 characters (about 979 tokens) of identical JSON, about 45 characters on each of the 87 tools.

**Proposed change.** Set `output_schema` to `None` after registration.

**Compatibility.** `outputSchema` is optional in MCP. Clients that only read `content` are unaffected. Clients that required an output schema for these tools will no longer see one. There was nothing useful to validate.

## 4. Empty FastMCP metadata

`include_fastmcp_meta` defaults to true in FastMCP 2.13. With no tags set, every tool still carried:

```json
{"_fastmcp": {"tags": []}}
```

That was 2,088 characters (about 522 tokens).

**Proposed change.** Construct the server with `include_fastmcp_meta=False`. Use tags only inside the server for filtering, so they never appear in `tools/list`.

**Compatibility.** Clients do not need `_fastmcp.tags` to call tools. Cursor, Claude Desktop, and ChatGPT select tools from `name`, `description`, and `inputSchema`.

## 5. No server-side tool subset

`main.py` always imports the core modules. Optional modules are already skipped when their import fails. There was no way to hide PySAL from a client that only buffers geometries. MCP `tools/list` has a cursor, but current clients still concatenate every page into the prompt. Hiding a tool without omitting it from `tools/list` does not save tokens.

FastMCP supports `include_tags` and `exclude_tags` before list. That is the mechanism that actually changes the payload.

**Proposed change.** Tag each tool with one group (`geometry`, `vector`, `raster`, `crs`, `statistics`, `io`, `visualize`, `boundaries`, `climate`, `ecology`, `movement`, `satellite`, `landcover`). Default remains every registered tool. `GIS_MCP_MODULES`, `GIS_MCP_EXCLUDE`, `--modules`, and `--exclude-modules` set the FastMCP filters.

**Compatibility.** The default catalog is unchanged in membership. A client configured with a subset will not see the other tools and cannot call them until the server is restarted with a wider set. Reconnect after changing the filter. Tags are not a client-side discovery API.

**Not assumed.** No client in this audit can search tools without first receiving their schemas. Pagination does not, by itself, reduce prompt tokens.

## 6. Large tool results

These are per-call costs. A single oversized result can exceed the entire catalog.

### Vector previews include full WKT

`read_file_gpd`, `overlay_gpd`, `dissolve_gpd`, `explode_gpd`, `clip_vector`, `sjoin_gpd`, `sjoin_nearest_gpd`, and `point_in_polygon` return `head(5)` with geometry converted to WKT. Five municipal polygons can be tens of kilobytes. PySAL `data_preview` fields do the same for five features, and several local statistics also return one number per feature with no cap (`moran_local`, `getis_ord_g_local`, `join_counts_local`, `adbscan`).

**Proposed change.** Default previews to attributes only. Add `include_geometry`, `max_features`, `offset`, `columns`, and `precision`. Cap local-statistic arrays at `max_records` (default 100) and, above that, return count, min, max, mean, and a head. The saved file is still the full result.

**Compatibility.** `preview` remains a list. Geometry is absent unless requested. Callers that read WKT from the preview must pass `include_geometry=true`. `num_rows` / `num_features` still describe the full dataset. Arrays of 100 or fewer values stay plain lists.

### `get_available_crs` builds 100 CRS records

`pyproj_functions.get_available_crs` walks the first 100 EPSG codes and returns a name and type for each. That is roughly 8,000–12,000 characters per call, and it constructs 100 CRS objects even when the user asked "what CRS should I use?".

**Proposed change.** Return a fixed list of 20 common CRS codes unless `query` is set. Hard-cap `limit` at 50. Search the common list before touching the EPSG database, and stop the database scan at 400 codes.

**Compatibility.** The tool still returns `crs_list`. The list is no longer "the first 100 EPSG codes". Tests only required a non-empty list.

### Raster histogram defaults to 256 bins

`raster_histogram` returns `histogram` and `bin_edges` for every band. A 10-band raster at 256 bins is thousands of numbers. The model usually needs the shape of the distribution, not 256 edges.

**Proposed change.** `compact=true` (the default) computes at most 32 bins and reports the pixel count. `compact=false` keeps the requested bin count.

**Compatibility.** The `histograms` object remains. Bin length changes when `compact` is left at the default. Pass `compact=false` for the previous 256-bin array.

### Zonal statistics grow with the polygon count

`zonal_statistics` returns one record per polygon and embeds no geometry, but a national dataset is still a long array.

**Proposed change.** `max_features` defaults to 200, with `total`, `offset`, and `truncated`. The statistics that are returned are unchanged.

### CRS WKT

`get_raster_crs` returns a full WKT string. Tests and clients read the `wkt` key. It stays. The description was shortened; the value was not.

### STAC and GBIF payloads

`download_satellite_imagery`, `download_worldcover`, and `compute_s2_ndvi` return `item.properties`, which is often several kilobytes of STAC metadata the file path already identifies. `get_species_info` returns the full GBIF backbone record.

**Proposed change.** Return a short summary (`datetime`, platform, cloud cover, taxonomy keys). `include_properties=true` or `full=true` restores the previous object.

### Routing

`calculate_shortest_path` returns every node id. A city-scale path can be thousands of integers.

**Proposed change.** Return `node_count`, `length_m`, and at most `max_nodes` (default 200) ids, with `truncated`.

### Duplicated weight payloads

`weights_from_shapefile`, `distance_band_weights`, `knn_weights`, and `build_and_transform_weights` return the same dictionary as both `result` and `weights_info`. JSON encodes it twice.

**Proposed change.** Keep `weights_info`, which the tests read, and drop the duplicate `result` key.

### Success prose

Many tools add `message` text that restates `status: success`. That is a few dozen tokens per call. The messages were kept where tests or clients may look for them. New code does not add a second copy of the same sentence.

## 7. Response format doubles every dict

FastMCP 2.13 `Tool.run` (`fastmcp/tools/tool.py`) turns a dict into text `content` and also sets `structuredContent` to the same dict, even when `output_schema` is `None`. MCP requires `content`. `structuredContent` is optional. Clients that put both into the transcript spend about twice the result tokens.

**Proposed change.** Middleware clears `structured_content` unless `GIS_MCP_STRUCTURED_CONTENT=1`.

**Compatibility.** The JSON text in `content` is unchanged, so Claude Desktop, Cursor, and ChatGPT still receive the result. A client that reads only `structuredContent` and ignores `content` must set the environment variable. That client would be outside the usual MCP rule that `content` is the required channel. The in-repo test helper reads the text when structured content is absent.

## 8. Repeated file reads

Vector tools call `geopandas.read_file` again for every step of a workflow (read, overlay, join, write). That does not by itself add tokens, but it adds latency and can push the model to call `read_file_gpd` extra times if a later call is slow.

**Proposed change.** Cache the GeoDataFrame keyed by absolute path, mtime, and size (16 entries). Return a copy so callers can reproject without poisoning the cache.

**Compatibility.** A file replaced in place with the same mtime and size could be stale. That is the usual mtime-cache limitation. The cache is process-local and is not a cross-call token protocol.

## 9. Tool consolidation was rejected

`point_in_polygon` is a spatial join with `predicate="within"`. `envelope` returns a geometry and `get_bounds` returns four numbers. Several PySAL global statistics share a loader. Merging them into `geometry_op(operation, ...)` or `spatial_stat(kind, ...)` would shrink `tools/list` and make selection worse: the model would have to guess an enum, and every existing client prompt and test would break. A wrong tool call costs more tokens than a one-line description.

No tools were removed. No universal GIS tool was added.

## 10. Deterministic execution

The server does not call a language model. Geometry uses Shapely, CRS uses PyProj, vectors use GeoPandas, rasters use Rasterio, spatial statistics use PySAL, and the optional tools use OSMnx, Planetary Computer, CDS, GBIF, or GADM. Filtering and statistics run in Python or in those libraries. Backtick stripping on a few path arguments only cleans client-wrapped strings. It is not an LLM call.

Nothing in this audit adds an agent framework, a model router, or a second model hop.

## 11. What was not changed

- Tool names and required parameters.
- The geometry returned by geometry operations such as `buffer` and `intersection`. That WKT is the answer, not a preview.
- Full raster arrays are not embedded in results today; tools write files and return paths. `write_raster` still accepts an array because that is its input. Prefer file paths for large grids.
- Resource URIs that list operation names.
- The default set of tools. Subsets are opt-in.

## Priority used for the implementation

1. Drop empty output schemas and FastMCP metadata. Shorten descriptions that duplicate the schema. Stop duplicating dict results into `structuredContent`.
2. Cap CRS lists, histograms, zonal pages, vector previews, local-statistic arrays, STAC properties, and shortest-path node lists.
3. Group tags and `--modules` / `GIS_MCP_MODULES` for clients that should not load the full catalog.
4. Cache repeated vector reads.
5. Do not merge unrelated tools.
