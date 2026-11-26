# MCP token optimization benchmark

Measured on the core catalog of 87 tools. Optional data and visualization tools are not in this count. The before snapshot is `docs/benchmarks/baseline_summary.json`, taken from the registered FastMCP tools before the optimization. The after numbers are produced by:

```bash
python scripts/benchmark_mcp_tokens.py
```

The script writes `docs/benchmarks/after_summary.json`.

## How tokens are counted

| Method | What it is |
| --- | --- |
| `chars/4` | Character length divided by 4. A rough estimate only. |
| `cl100k_base` | `tiktoken` encoding used by several OpenAI models. A representative BPE count. |

Neither number is a Claude, Cursor, or ChatGPT invoice. Coordinate-heavy JSON tokenizes worse than `chars/4` predicts: the geometry preview below is 981 tokens by `chars/4` and 2,153 tokens by `cl100k`.

Tool-call counts for a workflow are unchanged. Tools were not merged, so a buffer-then-overlay workflow still makes the same calls. The saving is the catalog on every conversation plus the size of each result.

## Catalog

87 tools before and after. Nothing was removed.

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| `tools/list` payload, characters | 46,237 | 32,554 | −29.6% |
| Same payload, chars/4 | 11,560 | 8,139 | −29.6% |
| Same payload, cl100k | not stored | 7,440 | |
| Description characters | 14,643 | 6,137 | −58.1% |
| Description text, cl100k | 3,440 | 1,349 | −60.8% |
| Average description, characters | 168 | 71 | |
| Input schema characters | 18,110 | 21,286 | +17.5% |
| Average input schema, characters | 208 | 245 | |
| Output schema characters | 3,915 | 0 | −100% |
| FastMCP `_meta` characters | 2,088 | 0 | −100% |

Input schemas grew because preview, paging, and limit arguments were added. That cost is smaller than the description, output-schema, and metadata cuts, so the catalog is still about 14,000 characters smaller (about 3,400 tokens at chars/4, and the cl100k catalog is 7,440 tokens). The smaller result options stay off unless a caller asks for them, so an existing client still receives the full default payload.

Description cl100k counts are the tool descriptions joined with newlines, tokenized with `cl100k_base`. The before figure uses the descriptions saved in the baseline file. The full before payload was not re-tokenized with cl100k because the snapshot stored character totals and description text, not the original schema JSON.

Empty output schemas (`{"type":"object","additionalProperties":true}` on every tool) and empty `_fastmcp.tags` objects are gone.

## Representative results

### Vector preview

200 polygons, 30 vertices each. The tool returns 5 features.

| Preview | Characters | chars/4 | cl100k |
| --- | ---: | ---: | ---: |
| With WKT geometry (default) | 3,921 | 981 | 2,153 |
| Attributes only (`include_geometry=false`) | 121 | 31 | 47 |

cl100k drops from 2,153 to 47, about 98%, when the caller asks to omit geometry. The default preview still includes WKT so an existing client sees the same kind of geometry it did before. The file written by overlay, clip, and join tools is still the full dataset. `num_features` still reports the full count.

Real cadastral polygons have more vertices than this fixture, so the old preview was often larger than this example.

### Other default result caps

| Call | Default (same as the previous install) | Opt-in smaller result |
| --- | --- | --- |
| `get_available_crs` | First 100 EPSG records | A smaller `limit`, or `query` to search |
| `raster_histogram` | The requested bin count | `compact=true` (at most 32 bins) |
| `zonal_statistics` | One row per polygon, plus `total` and `truncated` | `max_features` to page |
| Local Moran's I and similar | One number per feature, plus a WKT preview | `max_records` to summarize a long series |
| Weight tools | Same object under `result` and `weights_info` | Unchanged |
| Satellite / WorldCover / NDVI | Full STAC `properties`, plus a `summary` | `include_properties=false` |
| `calculate_shortest_path` | Every node id, plus `node_count` and `length_m` | `max_nodes` to cap the id list |

### Duplicate structured content

FastMCP 2.13 puts a dict result in `content` and copies it to `structuredContent`. Both copies are still sent, so a client that reads `structuredContent` keeps working. Set `GIS_MCP_STRUCTURED_CONTENT=0` to send the JSON text only.

## Discovery and workflows

Selecting `--modules geometry` lists the 28 Shapely tools instead of all 87. That only helps a client that connects with the filter set. A client that requests the full list still receives 87 tools. There is no extra tool call for discovery. Existing resources (`gis://...`) are unchanged.

A typical buffer, reproject, and overlay workflow uses the same number of tool calls as before. Execution of those calls is still Shapely, PyProj, and GeoPandas. Repeated vector reads in one process reuse a 16-entry file cache. Latency was not compared on a fixed dataset in this run. Correctness is covered by `tests/test_token_optimization.py` and the existing tool tests.

## Correctness

- Tool count stays 87.
- Required parameters are unchanged.
- Preview geometry is included unless the caller passes `include_geometry=false`. The spatial operation still writes or returns the full geometry when that geometry is the result (`buffer`, `intersection`, and the output file of an overlay).
- Local-statistic arrays stay full lists unless `max_records` is set, so existing responses keep their shape.
- `GIS_MCP_MODULES` defaults to every registered tool.
