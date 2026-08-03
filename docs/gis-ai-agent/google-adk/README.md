# Google ADK

Google Agent Development Kit (ADK) with GIS MCP Server as an MCP tool backend.

## Status

**Planned / evaluate on demand** — no tutorial yet.

Google ADK is a **Tier 2** documentation candidate: useful for teams already on Google’s agent stack, with possible operational overlap if you use GIS MCP’s **GCS** storage backend. It is not in the first implementation wave (LangGraph, CrewAI, LlamaIndex).

## Planned tutorials

| Tutorial | Status | Intended focus |
| -------- | ------ | -------------- |
| [ADK + GIS MCP](adk-geospatial-agent.md) | Coming soon | MCP client connection and a small geospatial workflow |

## When to consider ADK

- Your organization standardizes on Google ADK.
- You already deploy related services on GCP and may use GIS MCP GCS storage.

Otherwise prefer [LangChain](../langchain/README.md) or [OpenAI Node.js](../openai-nodejs/README.md) today.

## Prerequisites (expected)

- GIS MCP Server (HTTP or the transport ADK’s MCP client supports)
- Google ADK and auth/model setup per Google’s docs
- Optional: GCS storage configuration for GIS MCP

## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Storage Configuration](../../storage-configuration.md)
- [Agent architecture](../architecture.md)
