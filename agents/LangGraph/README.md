# LangGraph + GIS MCP samples

1. **Stateful site coverage** — single pipeline (`gis_workflow_graph.py`)
2. **Multi-agent setback compliance** — Planner / Analysis / Validation (`multi_agent_workflow.py`)

Tutorials:

- https://gis-mcp.com/gis-ai-agent/langgraph/stateful-geospatial-agent/
- https://gis-mcp.com/gis-ai-agent/langgraph/multi-agent-geospatial-workflow/

## Quick start

```bash
pip install -r requirements.txt

# Terminal 1 — GIS MCP
#   $env:GIS_MCP_TRANSPORT='http'; $env:GIS_MCP_HOST='127.0.0.1'; $env:GIS_MCP_PORT='9010'; gis-mcp

# Terminal 2
python verify_graph.py
python verify_multi_agent.py
python gis_workflow_graph.py --demo
python multi_agent_workflow.py --demo
```

| File | Purpose |
| ---- | ------- |
| `gis_workflow_graph.py` | Single stateful pipeline |
| `verify_graph.py` | No-LLM check (single) |
| `multi_agent_workflow.py` | Three-agent setback workflow |
| `verify_multi_agent.py` | No-LLM check (multi-agent) |
| `requirements.txt` | Dependencies |
| `.env.example` | Optional LLM keys |
