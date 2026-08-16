# Tutorial materials

Shareable companion files for GIS MCP articles, videos, and talks.

This tree is **not** the docs website (`docs/`) and **not** unpublished drafts (`medium-drafts/`). Docs-backed samples stay in [`agents/`](../agents/); unpublished copy-paste drafts stay gitignored.

## Layout

One folder per material. Keep the slug stable (kebab-case, no dates):

```
tutorials/<slug>/
  README.md           # how to run this material
  requirements.txt    # Python deps (if any)
  .env.example        # env template, no secrets
  .gitignore          # generated data / outputs for this material
  …source files…
```

Do not commit secrets, generated GeoJSON, maps, or `outputs/`.

## Materials

| Folder | Material |
| ------ | -------- |
| [`langgraph-multi-step-gis-agent/`](langgraph-multi-step-gis-agent/) | [Build a Multi-Step GIS AI Agent with GIS MCP Server + LangGraph](https://medium.com/@mahdinazari75/build-a-multi-step-gis-ai-agent-with-gis-mcp-server-langgraph-abc2eb289138) |
