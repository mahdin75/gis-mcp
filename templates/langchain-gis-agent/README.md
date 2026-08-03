# Template: basic single-agent GIS assistant (LangChain)

Minimal LangChain agent that loads GIS MCP tools and answers geospatial questions.

**Full tutorial (do not replace with this stub):**  
https://gis-mcp.com/gis-ai-agent/langchain/basic-geospatial-agent/

## Setup

```bash
# 1) Start GIS MCP (separate terminal)
#    $env:GIS_MCP_TRANSPORT='http'; $env:GIS_MCP_HOST='127.0.0.1'; $env:GIS_MCP_PORT='9010'; gis-mcp

# 2) Install this template
cd templates/langchain-gis-agent
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # set OPENROUTER_API_KEY or OPENAI_API_KEY

# 3) Smoke-check MCP (no LLM)
python smoke_check.py

# 4) Run agent
python main.py
python main.py --query "YOUR QUESTION WITH WKT HERE"
```

## What to customize

| Placeholder / area | Change to |
| ------------------ | --------- |
| `ALLOWED_TOOL_NAMES` | Tools your task needs (keep small) |
| `SYSTEM_PROMPT` | Domain rules, units, CRS policy |
| `GIS_MCP_URL` | Remote MCP URL if not local |
| `GIS_AGENT_MODEL` | Your LLM model id |
| Query / demo text | Your geometries and question |

## Files

- `main.py` — agent entrypoint  
- `smoke_check.py` — verify MCP tool discovery  
- `requirements.txt` — LangChain + MCP adapters  
- `.env.example` — API keys / URL overrides  
