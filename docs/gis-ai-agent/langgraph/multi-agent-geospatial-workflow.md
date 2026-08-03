# Multi-agent geospatial workflow (LangGraph)

**Status: Coming soon**

This page is reserved for a LangGraph tutorial that coordinates **multiple specialist nodes** (for example fetch, analyze, summarize) that share GIS MCP tools.

## Intended scope (not implemented yet)

- Graph nodes with different prompts / tool subsets
- Shared state carrying file paths and CRS metadata
- One GIS MCP HTTP server as the shared geospatial tool layer

GIS MCP does not provide multi-agent orchestration; that remains in LangGraph.

Until this guide ships, use:

- [LangChain basic geospatial agent](../langchain/basic-geospatial-agent.md)
- [Best practices — multi-agent coordination](../best-practices.md#multi-agent-coordination)
- [LangGraph section overview](README.md)
