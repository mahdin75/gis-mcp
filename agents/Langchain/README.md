# LangChain + GIS MCP sample

Park **100 m buffer proximity** agent using LangChain and GIS MCP over HTTP.

Full tutorial: https://gis-mcp.com/gis-ai-agent/langchain/basic-geospatial-agent/

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # set OPENROUTER_API_KEY or OPENAI_API_KEY

# Terminal 1 — GIS MCP (HTTP)
#   $env:GIS_MCP_TRANSPORT='http'; $env:GIS_MCP_HOST='127.0.0.1'; $env:GIS_MCP_PORT='9010'; gis-mcp

# Terminal 2 — verify tools (no LLM), then agent demo
# Prefer 127.0.0.1 if localhost hits a corporate proxy (HTTP 503)
python verify_tools.py
python my_gis_agent.py --demo
python my_gis_agent.py
```

| File | Purpose |
| ---- | ------- |
| `my_gis_agent.py` | Interactive agent / `--demo` |
| `verify_tools.py` | MCP workflow check without an LLM |
| `requirements.txt` | LangChain dependencies |
| `.env.example` | Env template (no secrets) |
