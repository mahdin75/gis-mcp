# LangChain

Build GIS-enabled agents in **Python** with LangChain and GIS MCP Server.

## Status

**Available** — end-to-end tutorial, runnable sample, and MCP workflow verifier.

## Tutorials

| Tutorial | Status | Description |
| -------- | ------ | ----------- |
| [Park buffer proximity agent](basic-geospatial-agent.md) | Available | LangChain + MCP HTTP: project → buffer 100 m → intersect → geodetic distance |

## Sample code

Repository: [`agents/Langchain/`](https://github.com/mahdin75/gis-mcp/tree/main/agents/Langchain)

Minimal starter: [`templates/langchain-gis-agent/`](https://github.com/mahdin75/gis-mcp/tree/main/templates/langchain-gis-agent)

| File | Purpose |
| ---- | ------- |
| `my_gis_agent.py` | Interactive agent and `--demo` proximity workflow |
| `verify_tools.py` | No-LLM check that GIS MCP tools perform the workflow |
| `requirements.txt` | LangChain / MCP adapter dependencies |
| `.env.example` | API key and optional URL/model overrides |

## When to use LangChain

- Fastest documented Python path to a GIS MCP agent
- Single-agent tool calling with official MCP adapters
- Path toward [LangGraph](../langgraph/README.md) for stateful graphs later

## Prerequisites

- GIS MCP Server (HTTP recommended)
- Python 3.10+
- `OPENROUTER_API_KEY` or `OPENAI_API_KEY` for the agent (not required for `verify_tools.py`)

See: [HTTP Transport](../../http-transport.md), [Best practices](../best-practices.md).

## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Agent architecture](../architecture.md)
- [Agent Tutorials overview](../README.md)
