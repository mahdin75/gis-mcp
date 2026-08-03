# Template: stateful GIS workflow (LangGraph)

Minimal LangGraph pipeline: **interpret → plan → execute (GIS MCP) → validate → respond**.

**Full tutorial:** https://gis-mcp.com/gis-ai-agent/langgraph/stateful-geospatial-agent/

## Setup

```bash
# Start GIS MCP on 127.0.0.1:9010 (HTTP), then:
cd templates/langgraph-gis-workflow
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # or source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # optional LLM keys

python smoke_check.py    # no LLM — runs deterministic pipeline
python main.py --demo    # same path with printed answer
```

## What to customize

| Area | Customize |
| ---- | --------- |
| `PLACEHOLDER_SITE_A` / `PLACEHOLDER_SITE_B` | Your WKT geometries |
| `BUFFER_METERS` | Buffer distance (meters, after UTM) |
| `ALLOWED_TOOL_NAMES` | GIS MCP tools Analysis may use |
| `interpret` / `validate` nodes | Domain parsing and QA rules |
| Optional LLM | Set keys and clear `SKIP_LLM=1` to use structured interpret |

## Files

- `main.py` — StateGraph  
- `smoke_check.py` — deterministic end-to-end check  
- `requirements.txt`, `.env.example`  
