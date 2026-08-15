# CrewAI

Role-based multi-agent GIS workflows using GIS MCP Server as the shared geospatial tool backend.

## Status

**Planned** — tutorial not published yet.

CrewAI is a **Tier 1** documentation target for multi-agent orchestration (for example analyst + cartographer roles). GIS MCP does not provide crew orchestration itself; CrewAI (or similar) runs in your agent application and calls GIS MCP over MCP.

## Planned tutorials

| Tutorial | Status | Intended focus |
| -------- | ------ | -------------- |
| [Multi-agent geospatial crew](multi-agent-geospatial-crew.md) | Coming soon | Roles that download/analyze/visualize via GIS MCP tools |

## When to use CrewAI

- You want named roles with separate goals and tool subsets.
- Your workflow splits naturally across fetch → analyze → map/report.
- You accept pinning CrewAI versions and retesting MCP integration periodically.

Until this tutorial ships, use a [single LangChain agent](../langchain/basic-geospatial-agent.md) or the [LangGraph](../langgraph/README.md) tutorials for structured multi-step flows.

## Prerequisites (expected)

- GIS MCP Server (HTTP)
- Optional extras required by the demo (for example data gathering and/or `[visualize]`)
- CrewAI and its MCP client integration (pinned in the future tutorial)

## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Best practices](../best-practices.md) — especially multi-agent coordination
- [Agent architecture](../architecture.md)
