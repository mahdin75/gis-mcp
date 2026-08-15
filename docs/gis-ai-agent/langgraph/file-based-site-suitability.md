# File-based site suitability (LangGraph)

A **layer-based** LangGraph pattern on GIS MCP: clip → overlay → CRS-safe buffer → spatial join → map.

This is **not** a replacement for the WKT tutorials. Use those first if you are new to LangGraph + GIS MCP:

- [Stateful site-coverage](stateful-geospatial-agent.md) (inline WKT, 400 m transit buffer)
- [Multi-agent setback](multi-agent-geospatial-workflow.md) (Planner / Analysis / Validation)

Use **this** pattern when the question needs **GeoJSON/shapefile layers**, intermediate files, and a map — for example playground / park-access site suitability.

## What it demonstrates

```
User request
  → interpret / plan (LangGraph state)
  → read_file_gpd
  → clip_vector (lots ∩ downtown)
  → overlay_gpd how=difference (erase flood)
  → dissolve_gpd → get_utm_crs → project_geometry → buffer
  → project_geometry back to EPSG:4326 → save_results
  → sjoin_gpd (lots ⋈ park-access zone)
  → write_file_gpd · create_map · create_web_map
  → rank + validate + natural-language briefing
```

GIS MCP has **no GeoPandas buffer** and **no layer `to_crs` tool**. Meter buffers must use Shapely `buffer` on WKT **after** `project_geometry` into a UTM CRS, then save the result back to a file. See [best practices](../best-practices.md).

## Tools used (registered names)

GeoPandas: [`read_file_gpd`](../../api/geopandas/read_file_gpd.md), [`clip_vector`](../../api/geopandas/clip_vector.md), [`overlay_gpd`](../../api/geopandas/overlay_gpd.md), [`dissolve_gpd`](../../api/geopandas/dissolve_gpd.md), [`sjoin_gpd`](../../api/geopandas/sjoin_gpd.md), [`write_file_gpd`](../../api/geopandas/write_file_gpd.md)

PyProj / Shapely: [`get_utm_crs`](../../api/pyproj/get_utm_crs.md), [`project_geometry`](../../api/pyproj/project_geometry.md), [`buffer`](../../api/shapely/buffer.md), [`is_valid`](../../api/shapely/is_valid.md)

Output: `save_results`, [`create_map`](../../api/visualize/create_map.md), [`create_web_map`](../../api/visualize/create_web_map.md) (requires `pip install "gis-mcp[visualize]"`)

Do not call `to_file_gpd` (not registered). Do not use [`sjoin_nearest_gpd`](../../api/geopandas/sjoin_nearest_gpd.md) as a 300 m filter: `max_distance` is in **CRS units**, and the tool does not expose `distance_col`.

## Walkthrough

Long-form, copy-paste tutorial (continuation of the LangChain Medium intro):

- [Build Your First GIS AI Agent (LangChain)](https://medium.com/@mahdinazari75/build-your-first-gis-ai-agent-by-gis-mcp-server-langchain-c0c1bfa36f6d)
- Medium: *Build a Multi-Step GIS AI Agent with LangGraph + GIS MCP* — add the published URL here after posting

Website: [gis-mcp.com](https://gis-mcp.com/) · [LangGraph overview](README.md)

Install extras and HTTP transport: [pip](../../install/pip.md) · [HTTP](../../http-transport.md) · [storage](../../storage-configuration.md)
