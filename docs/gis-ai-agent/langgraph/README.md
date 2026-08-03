# LangGraph

Stateful, graph-based GIS agents on top of GIS MCP Server.

## Status

**Planned** — tutorial not published yet.

LangGraph is a **Tier 1** documentation target: it shares the LangChain MCP adapter ecosystem already used by the [LangChain](../langchain/README.md) sample, and it fills the gap for multi-step and branching geospatial workflows.

## Planned tutorials

| Tutorial | Status | Intended focus |
| -------- | ------ | -------------- |
| [Stateful geospatial agent](stateful-geospatial-agent.md) | Coming soon | Checkpointed multi-step GIS pipeline (inspect → CRS → analyze → save) |
| [Multi-agent geospatial workflow](multi-agent-geospatial-workflow.md) | Coming soon | Graph with specialized nodes sharing GIS MCP tools |

## When to use LangGraph

- You need explicit control flow, branching, or human-in-the-loop steps.
- Your GIS workflow is longer than a single tool-calling turn.
- You already use LangChain with GIS MCP and need more structure.

Until this tutorial ships, start with the [LangChain basic agent](../langchain/basic-geospatial-agent.md) and apply [best practices](../best-practices.md) for planning and CRS handling.

## Prerequisites (expected)

- GIS MCP Server with HTTP transport
- LangGraph + LangChain MCP adapters (versions to be pinned in the future tutorial)
- Same LLM provider setup pattern as other Python agent samples

## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Agent architecture](../architecture.md)
- [LangChain](../langchain/README.md)
