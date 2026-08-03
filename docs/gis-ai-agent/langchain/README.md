# LangChain

Build GIS-enabled agents in **Python** with LangChain and GIS MCP Server.

## Status

**Available** — end-to-end tutorial and sample project.

## Tutorials

| Tutorial | Status | Description |
| -------- | ------ | ----------- |
| [Basic geospatial agent](basic-geospatial-agent.md) | Available | Connect LangChain to GIS MCP over HTTP, load MCP tools, run an interactive GIS assistant |

Additional LangChain guides can be added beside this file as the section grows.

## Sample code

Repository: [`agents/Langchain/`](https://github.com/mahdin75/gis-mcp/tree/main/agents/Langchain)

## When to use LangChain

- You want the fastest documented Python path to a GIS MCP agent.
- You need a single-agent loop with MCP tool calling.
- You plan to grow into [LangGraph](../langgraph/README.md) later for stateful workflows.

## Prerequisites

- GIS MCP Server running (HTTP recommended for this tutorial)
- Python 3.10+
- LLM API access as described in the tutorial (OpenRouter in the published sample)

See also: [HTTP Transport](../../http-transport.md), [Best practices](../best-practices.md).

## Planned under this section

- Optional follow-ups: tool subsetting patterns, extras-aware agents (`[visualize]`, data gathering)

## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Agent architecture](../architecture.md)
- [Agent Tutorials overview](../README.md)
