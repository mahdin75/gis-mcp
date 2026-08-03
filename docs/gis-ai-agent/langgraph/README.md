# LangGraph

Stateful, graph-based GIS agents on top of GIS MCP Server.

## Status

**Available** — stateful site-coverage tutorial and runnable sample.

## Tutorials

| Tutorial | Status | Description |
| -------- | ------ | ----------- |
| [Stateful geospatial agent](stateful-geospatial-agent.md) | Available | interpret → plan → GIS MCP execute → validate → respond |
| [Multi-agent geospatial workflow](multi-agent-geospatial-workflow.md) | Coming soon | Multiple specialist nodes sharing GIS MCP |

## Sample code

[`agents/LangGraph/`](https://github.com/mahdin75/gis-mcp/tree/main/agents/LangGraph)

```bash
cd agents/LangGraph
pip install -r requirements.txt
python verify_graph.py
python gis_workflow_graph.py --demo
```

## When to use LangGraph

- You need **explicit** multi-step GIS control flow (CRS → project → buffer → check)
- You want validation / error branches as graph nodes
- A free-form [LangChain agent](../langchain/basic-geospatial-agent.md) is not structured enough

## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Agent architecture](../architecture.md)
- [LangChain](../langchain/README.md)
