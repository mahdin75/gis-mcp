# GIS-MCP agent templates

Minimal starter projects extracted from the full tutorials. Prefer these when scaffolding a new app; use the tutorials for deep walkthroughs.

| Template | Pattern | Full tutorial |
| -------- | ------- | ------------- |
| [`langchain-gis-agent/`](langchain-gis-agent/) | Single-agent GIS assistant | [Park buffer agent](../docs/gis-ai-agent/langchain/basic-geospatial-agent.md) |
| [`langgraph-gis-workflow/`](langgraph-gis-workflow/) | Stateful plan → execute → validate | [Stateful workflow](../docs/gis-ai-agent/langgraph/stateful-geospatial-agent.md) |
| [`langgraph-multi-agent-gis/`](langgraph-multi-agent-gis/) | Planner / Analysis / Validation | [Multi-agent setback](../docs/gis-ai-agent/langgraph/multi-agent-geospatial-workflow.md) |

## Shared conventions

- GIS MCP runs separately over HTTP (`streamable_http` client → `/mcp`)
- Prefer `http://127.0.0.1:9010/mcp` and set `NO_PROXY=127.0.0.1,localhost`
- Keep a small **tool allow-list** (do not dump every MCP tool into the agent)
- Buffer in **meters only after** projecting lon/lat to UTM
- Never invent coordinates or distances in prompts

## Prerequisites

```bash
pip install gis-mcp
# PowerShell example:
$env:GIS_MCP_TRANSPORT='http'; $env:GIS_MCP_HOST='127.0.0.1'; $env:GIS_MCP_PORT='9010'; gis-mcp
```

Then `cd` into a template, `pip install -r requirements.txt`, and follow that folder’s README.
