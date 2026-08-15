# LangGraph

Stateful and multi-agent GIS workflows on top of GIS MCP Server.

## Status

**Available** — stateful pipeline, three-agent setback workflow, and a file-based site-suitability pattern.


## Tutorials

| Tutorial | Status | Description |
| -------- | ------ | ----------- |
| [Stateful geospatial agent](stateful-geospatial-agent.md) | Available | interpret → plan → execute → validate → respond |
| [Multi-agent geospatial workflow](multi-agent-geospatial-workflow.md) | Available | Planner + Analysis + Validation (setback compliance) |
| [File-based site suitability](file-based-site-suitability.md) | Available | Clip / overlay / CRS-safe buffer / join / map (GeoJSON layers) |

## Sample code

[`agents/LangGraph/`](https://github.com/mahdin75/gis-mcp/tree/main/agents/LangGraph) — full reference implementations  

[`templates/langgraph-gis-workflow/`](https://github.com/mahdin75/gis-mcp/tree/main/templates/langgraph-gis-workflow) · [`templates/langgraph-multi-agent-gis/`](https://github.com/mahdin75/gis-mcp/tree/main/templates/langgraph-multi-agent-gis) — minimal starters

```bash
cd agents/LangGraph
pip install -r requirements.txt
python verify_graph.py
python verify_multi_agent.py
python gis_workflow_graph.py --demo
python multi_agent_workflow.py --demo
```

## When to use LangGraph

- Explicit multi-step GIS control flow (CRS → project → buffer → check)
- Validation / error branches as graph nodes
- Separated Planner / Analysis / Validation when auditability matters

Prefer a simpler [LangChain agent](../langchain/basic-geospatial-agent.md) for short exploratory Q&A.

For **GeoJSON layers** (clip, overlay, park buffer, map), see [file-based site suitability](file-based-site-suitability.md). That pattern is written up as a Medium continuation of the [LangChain intro](https://medium.com/@mahdinazari75/build-your-first-gis-ai-agent-by-gis-mcp-server-langchain-c0c1bfa36f6d).


## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Agent architecture](../architecture.md)
- [LangChain](../langchain/README.md)
