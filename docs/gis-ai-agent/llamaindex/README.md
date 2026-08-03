# LlamaIndex

Combine retrieval workflows with GIS MCP tools for document-aware geospatial agents.

## Status

**Planned** — tutorial not published yet.

LlamaIndex is prioritized because it offers a **distinct** story from LangChain/LangGraph: RAG (or workflows) over your content, plus MCP tools for real GIS operations. Claims in future tutorials will be limited to what GIS MCP tools and your indexed data actually provide.

## Planned tutorials

| Tutorial | Status | Intended focus |
| -------- | ------ | -------------- |
| [RAG + GIS MCP agent](rag-geospatial-agent.md) | Coming soon | Retrieve layer/docs context, then call GIS MCP for analysis |

## When to use LlamaIndex

- Your app is document- or metadata-heavy and also needs spatial tools.
- You want retrieval and tool calling in one agent/workflow stack.

For a GIS-only assistant without RAG, prefer the available [LangChain](../langchain/README.md) tutorial today.

## Prerequisites (expected)

- GIS MCP Server (HTTP)
- LlamaIndex with MCP client support (versions pinned later)
- Content you are allowed to index (local docs, metadata—not assumed to ship inside GIS MCP)

## Related

- [Choosing an agent framework](../choosing-framework.md)
- [Agent architecture](../architecture.md)
- [Best practices](../best-practices.md)
