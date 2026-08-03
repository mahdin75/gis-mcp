# Template: multi-agent GIS workflow (LangGraph)

Minimal **Planner → Analysis → Validation** graph. Only Analysis calls GIS MCP.

**Full tutorial:** https://gis-mcp.com/gis-ai-agent/langgraph/multi-agent-geospatial-workflow/

## Setup

```bash
# Start GIS MCP on 127.0.0.1:9010 (HTTP), then:
cd templates/langgraph-multi-agent-gis
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

python smoke_check.py
python main.py --demo
```

## What to customize

| Area | Customize |
| ---- | --------- |
| `PLACEHOLDER_HAZARD` / `PLACEHOLDER_SUBJECT` | Your WKT inputs |
| `SETBACK_METERS` | Buffer / setback distance |
| `ANALYSIS_TOOLS` | Tools only Analysis may call |
| `planner_agent` | How requests become a plan (heuristic or LLM) |
| `validation_agent` | QA rules (CRS, consistency) — do **not** re-call MCP by default |

## Files

- `main.py` — three-agent StateGraph  
- `smoke_check.py` — no-LLM end-to-end check  
- `requirements.txt`, `.env.example`  
