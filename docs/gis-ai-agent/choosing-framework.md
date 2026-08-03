# Choosing an agent framework

GIS MCP Server is framework-agnostic: any runtime that can act as an **MCP client** can call its tools. This page helps you pick a tutorial path and avoid frameworks that are a poor fit for first-wave documentation.

## Decision checklist

Ask these questions before you commit:

1. **Language** — Python, Node.js/TypeScript, or another runtime?
2. **Orchestration** — Single tool-calling agent, stateful graph, or multi-agent roles?
3. **MCP client maturity** — Does the framework support MCP over **HTTP** (preferred for GIS MCP agent samples) or only stdio?
4. **Ops surface** — Will you maintain pins and retest when the framework’s agent APIs change?
5. **GIS workload** — Simple geometry/CRS calls, multi-step analysis, RAG over spatial docs, or role-separated download → analyze → map?

## Recommended paths

| If you need… | Prefer | Docs status |
| ------------ | ------ | ----------- |
| Fastest Python start with GIS MCP | **LangChain** | [Available](langchain/README.md) |
| Node.js / TypeScript agent | **OpenAI Agents SDK** | [Available](openai-nodejs/README.md) |
| Explicit state, branching, checkpoints | **LangGraph** | [Available](langgraph/README.md) |
| Role-based multi-agent teams | **CrewAI** | [Planned](crewai/README.md) |
| Retrieval over documents **plus** GIS tools | **LlamaIndex** | [Planned](llamaindex/README.md) |
| Google Cloud–centric agent stack | **Google ADK** | [Planned / evaluate](google-adk/README.md) |

## Available now

### LangChain (Python)

- **Strengths:** Broad ecosystem; official MCP adapters used by the published GIS MCP sample; good default for single-agent geospatial assistants.
- **Transport used in sample:** HTTP streamable MCP to `/mcp`.
- **Start:** [LangChain tutorials](langchain/README.md) → [Park buffer proximity agent](langchain/basic-geospatial-agent.md).

### OpenAI Agents SDK (Node.js)

- **Strengths:** Native MCP server helpers; natural fit for JS/TS apps.
- **Transport used in sample:** HTTP streamable MCP to `/mcp`.
- **Start:** [OpenAI Node.js tutorials](openai-nodejs/README.md) → [Basic geospatial agent](openai-nodejs/basic-geospatial-agent.md).

### LangGraph (Python)

- **Strengths:** Explicit `StateGraph`, stored plan, validation gate, error branch—better for repeatable GIS pipelines than a free-form agent.
- **Transport used in sample:** `streamable_http` to `/mcp`.
- **Start:** [LangGraph tutorials](langgraph/README.md) → [Stateful site-coverage workflow](langgraph/stateful-geospatial-agent.md).

## Planned (not implemented yet)

Tutorials are planned in this order of documentation priority. Stub pages exist so navigation and contributions stay consistent.

| Framework | Why it is on the roadmap | Caveats |
| --------- | ------------------------ | ------- |
| **CrewAI** | Clear multi-agent “crew” story for analyst / cartographer roles | API churn; pin versions when the tutorial lands |
| **LlamaIndex** | Distinct RAG + tools narrative | Keep GIS claims limited to MCP tools + your indexed content |
| **Google ADK** | Relevant if you already standardize on Google’s agent kit; optional synergy with GCS storage | Evaluate demand before investing heavily |
| **LangGraph multi-agent** | Specialist nodes on top of the stateful tutorial | Single-pipeline tutorial already shipped |

## Not prioritized for first-wave tutorials

These may still work with GIS MCP if they provide an MCP client, but this project does **not** plan dedicated tutorials in the near term:

| Framework / product | Reason |
| ------------------- | ------ |
| AutoGPT (platform) | Product/platform integration, not a small embeddable SDK tutorial |
| BabyAGI | Historical pattern; no maintained tutorial target for MCP agents |
| SuperAGI | Low priority for maintenance and adoption relative to the shortlist |
| MetaGPT | Weak fit for MCP tool-server tutorials |
| AutoGen / classic Semantic Kernel | Succession toward Microsoft Agent Framework increases deprecated-API risk; revisit as **Microsoft Agent Framework** stabilizes if enterprise demand appears |

If you need one of these, use the [architecture](architecture.md) and [best practices](best-practices.md) guides, connect via MCP HTTP, and open a discussion or PR rather than expecting first-party docs immediately.

## Compatibility with GIS MCP

Regardless of framework, your agent must:

1. Run **GIS MCP Server** (pip, Docker, or editable install).
2. Use a transport GIS MCP actually supports: **stdio**, **HTTP**, or **SSE**.
3. Discover tools from the live server (tool lists depend on installed extras).
4. Pass arguments that match each tool’s schema (paths, CRS identifiers, geometries, and so on).

GIS MCP does not bundle LangChain, CrewAI, LlamaIndex, or other agent SDKs. Those are dependencies of **your** agent project (see the `agents/` samples in the repository).

## Practical recommendation

1. **New to GIS MCP agents?** Follow the [LangChain park buffer tutorial](langchain/basic-geospatial-agent.md) or [OpenAI Node.js](openai-nodejs/basic-geospatial-agent.md) tutorial.
2. **Need multi-step control with validation?** Use the [LangGraph stateful workflow](langgraph/stateful-geospatial-agent.md).
3. **Need multiple specialist roles?** Prefer CrewAI when published; until then, do not fake multi-agent behavior inside GIS MCP—it has no built-in crew runtime.
4. **Read [Best practices](best-practices.md)** before scaling to large toolsets or production workflows.

## Related pages

- [Agent Tutorials overview](README.md)
- [GIS MCP agent architecture](architecture.md)
- [Best practices for GIS agents](best-practices.md)
