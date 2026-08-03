# Best practices for GIS agents

Guidance for building reliable agents on top of **GIS MCP Server**. Practices below assume the current product model: GIS MCP exposes MCP tools; your agent framework owns planning, memory, and orchestration.

Nothing here claims features GIS MCP does not provide (for example built-in long-term memory or a native multi-agent runtime).

## Tool selection

GIS MCP can register a **large** tool set (core analysis plus optional data and visualization extras). Dumping every tool into every agent increases cost, latency, and wrong-tool calls.

**Do:**

- Install only the extras your workflow needs so unused tools are never registered.
- Prefer framework features that bind a **subset** of tools when available.
- Match tools to the task (CRS tools for projections, GeoPandas for layer IO/joins, Rasterio for rasters, PySAL for spatial stats).

**Don’t:**

- Assume a tool exists because a similar GIS desktop command exists.
- Expose data-gathering or visualize tools if those extras are not installed—the agent will invent calls that fail at runtime.

## Tool descriptions

MCP tool schemas and descriptions are what the LLM sees.

**Do:**

- Keep system prompts aligned with real tool names and purposes from the live server.
- Tell the agent to prefer GIS MCP tools for spatial computation instead of estimating geometries in prose.
- Point developers at the [API reference](../data-gathering/README.md) and analysis docs when designing prompts.

**Don’t:**

- Override tool behavior in the prompt (“pretend `buffer` also reprojects”)—the server will not.
- Rely on outdated tool lists copied from blog posts; discover tools from the running server.

## Input validation

Validate arguments in the agent layer when you can (before or after tool calls):

- Required path strings exist and are reachable given your storage configuration.
- Numeric parameters (buffers, thresholds, indices) are finite and in documented ranges where the tool docs specify them.
- Enumerated modes (overlay types, stats, download options) match the tool schema.

GIS MCP tools will still error on invalid inputs; treat failures as signals to repair arguments, not to invent results.

## Geospatial data validation

Before multi-step analysis:

- Confirm layers open (GeoPandas/Rasterio tools or your own checks).
- Check geometry validity when workflows depend on clean polygons (Shapely validation / make-valid tools exist for this class of problem).
- Verify non-empty results after filters, clips, and overlays before chaining more tools.

Empty or invalid inputs produce misleading “success” narratives if the agent only paraphrases partial tool output.

## Coordinate reference systems

CRS mistakes are the most common silent GIS agent failure.

**Do:**

- Establish the CRS of each layer before measuring area, distance, or buffering in linear units.
- Use PyProj / project tools when data must move between CRS.
- State units expected by the user (meters vs degrees) in the agent prompt or UI.

**Don’t:**

- Buffer or measure “100 meters” on data still in EPSG:4326 without an intentional geographic workflow.
- Mix layers in different CRS in overlays/joins without reprojecting first.

## Error handling

**Do:**

- Surface tool errors to the user (message + which tool failed).
- Retry only when the failure is transient (connectivity) or clearly fixable (bad path, missing CRS).
- On HTTP samples, fail fast if the MCP server is unreachable—same class of issue as the LangChain sample’s connection diagnostics.

**Don’t:**

- Catch errors and answer with fabricated coordinates or statistics.
- Infinite-loop tool retries on schema validation failures.

## Reproducibility

**Do:**

- Pin GIS MCP and agent SDK versions in your project.
- Record inputs: layer paths, CRS, tool names, and key parameters in logs or saved transcripts.
- Prefer writing outputs through documented save/storage mechanisms so paths are stable for later runs.
- Note which optional extras were installed.

**Don’t:**

- Depend on ephemeral chat memory alone as the record of a spatial analysis.

## Memory design

Memory is an **agent-framework** concern. GIS MCP does not provide a vector store or session memory API.

**Do:**

- Store durable artifacts (GeoJSON, GeoPackage, maps, tables) via tools/storage, then remember **paths and CRS** in agent state.
- Keep only compact summaries in conversational memory (extent, CRS, output path)—not entire geometries—unless your framework can handle large payloads safely.

**Don’t:**

- Assume the MCP server recalls prior chat turns between separate client sessions.
- Stuff large geometries into every LLM turn when a file path is enough for the next tool call.

## Task planning

**Do:**

- Decompose spatial work into ordered steps: inspect → CRS → transform → analyze → save/visualize.
- Reuse proven sequences from [workflow examples](../examples/README.md) as test prompts.
- Prefer fewer, larger correct steps over many speculative tool calls.

**Don’t:**

- Skip CRS inspection before measurements.
- Call visualization or download tools “just in case” when the user only asked for a number.

## Multi-agent coordination

Multi-agent patterns live in frameworks such as CrewAI or LangGraph—not inside GIS MCP.

**Do:**

- Give each role a clear tool subset and responsibility (for example data fetch vs analysis vs cartography).
- Share **file paths and CRS metadata** between agents instead of re-downloading blindly.
- Run one GIS MCP server (HTTP) as a shared tool backend when the framework supports concurrent clients.

**Don’t:**

- Duplicate contradictory CRS assumptions across agents.
- Expect GIS MCP to arbitrate agent roles or shared blackboard state.

## Avoiding unnecessary tool calls

**Do:**

- Answer from prior tool results when the data is already in context.
- Use metadata/CRS/bounds tools before heavy raster or network downloads.
- Cap max tool iterations in the agent framework when available.

**Don’t:**

- Re-read the same file on every turn without need.
- Download climate, satellite, or movement datasets for questions solvable with local geometry tools.

## Avoiding unsupported or hallucinated GIS operations

Agents often invent desktop-GIS workflows GIS MCP does not expose.

**Do:**

- Constrain the system prompt: only use discovered MCP tools; if no tool fits, say so.
- Keep a short allowlist of supported categories in the prompt (analysis libraries and installed extras).
- Fail closed: “I don’t have a tool for X” is better than a plausible wrong polygon.

**Don’t:**

- Claim support for arbitrary geoprocessing, network analyst solvers, or proprietary enterprise GP services unless a tool exists.
- Paste example GeoJSON that was never returned by a tool as if it were measured.

## Transport and deployment habits

- Prefer **HTTP** for custom agent apps so the server lifecycle is explicit ([HTTP Transport](../http-transport.md)).
- Use **stdio** for desktop assistants configured via MCP JSON ([install docs](../install/README.md)).
- Align host/port with your client URL (samples often use port `9010`).
- Enable only the storage backend you need ([Storage Configuration](../storage-configuration.md)).

## Related pages

- [Agent Tutorials overview](README.md)
- [GIS MCP agent architecture](architecture.md)
- [Choosing an agent framework](choosing-framework.md)
- [Project architecture](../architecture.md)
