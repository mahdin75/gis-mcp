# LangGraph + GIS MCP sample

Stateful **transit-stop coverage** workflow: interpret → plan → execute GIS MCP tools → validate → respond.

Full tutorial: https://gis-mcp.com/gis-ai-agent/langgraph/stateful-geospatial-agent/

This is **not** a free-form LangChain ReAct agent. The graph stores an explicit plan and validation flags in state.

## Quick start

```bash
pip install -r requirements.txt

# Terminal 1 — GIS MCP
#   $env:GIS_MCP_TRANSPORT='http'; $env:GIS_MCP_HOST='127.0.0.1'; $env:GIS_MCP_PORT='9010'; gis-mcp

# Terminal 2
python verify_graph.py
python gis_workflow_graph.py --demo
```

| File | Purpose |
| ---- | ------- |
| `gis_workflow_graph.py` | StateGraph workflow |
| `verify_graph.py` | No-LLM end-to-end check |
| `requirements.txt` | Dependencies |
| `.env.example` | Optional LLM keys |
