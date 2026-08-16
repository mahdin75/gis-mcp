# LangGraph multi-step GIS agent

Companion files for the Medium tutorial:

[Build a Multi-Step GIS AI Agent with GIS MCP Server + LangGraph](https://medium.com/@mahdinazari75/build-a-multi-step-gis-ai-agent-with-gis-mcp-server-langgraph-abc2eb289138)

Playground site suitability: clip → overlay → CRS-safe buffer → spatial join → map.

| File | Purpose |
| ---- | ------- |
| `prepare_data.py` | Writes synthetic GeoJSON layers under `data/` |
| `gis_suitability_agent.py` | LangGraph workflow that calls GIS MCP tools |
| `requirements.txt` | Agent-side Python deps |
| `.env.example` | Env template (no secrets) |

## Setup

Start GIS MCP over HTTP in another terminal (`gis-mcp[visualize]` for maps):

```powershell
$env:GIS_MCP_TRANSPORT='http'; $env:GIS_MCP_HOST='127.0.0.1'; $env:GIS_MCP_PORT='9010'; gis-mcp
```

Then:

```bash
cd tutorials/langgraph-multi-step-gis-agent
pip install -r requirements.txt
cp .env.example .env   # set OPENROUTER_API_KEY if you want LLM polish
python prepare_data.py
python gis_suitability_agent.py --demo
```

`--demo` runs without a key (template answer). Interactive mode: `python gis_suitability_agent.py`.
