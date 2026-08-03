# LangGraph

Stateful and multi-agent GIS workflows on top of GIS MCP Server.

## Status

**Available** — single stateful pipeline + practical three-agent setback workflow.

## Tutorials

| Tutorial | Status | Description |
| -------- | ------ | ----------- |
| [Stateful geospatial agent](stateful-geospatial-agent.md) | Available | interpret → plan → execute → validate → respond |
| [Multi-agent geospatial workflow](multi-agent-geospatial-workflow.md) | Available | Planner + Analysis + Validation (setback compliance) |

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

## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Agent architecture](../architecture.md)
- [LangChain](../langchain/README.md)
