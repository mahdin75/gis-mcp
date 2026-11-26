"""Apply catalog slimming after tools have been registered."""

from __future__ import annotations

import json
from typing import Optional

from .descriptions import apply_descriptions
from .tool_groups import apply_tags


def finalize_catalog(mcp) -> None:
    """Drop unused schema fields and apply short descriptions and group tags.

    ``Dict[str, Any]`` return hints make FastMCP advertise an output schema of
    ``{"type": "object", "additionalProperties": true}`` on every tool. That
    schema does not constrain anything, so it is removed from tools/list.
    """
    for tool in mcp._tool_manager._tools.values():
        tool.output_schema = None
    apply_descriptions(mcp)
    apply_tags(mcp)


def measure_catalog(mcp, *, include_fastmcp_meta: bool = False) -> dict:
    """Measure the tools/list payload the server would send."""
    tools = []
    for tool in mcp._tool_manager._tools.values():
        dumped = tool.to_mcp_tool(include_fastmcp_meta=include_fastmcp_meta).model_dump(
            mode="json", exclude_none=True
        )
        tools.append(dumped)
    payload = json.dumps(tools, separators=(",", ":"))
    return {
        "tool_count": len(tools),
        "payload_chars": len(payload),
        "description_chars": sum(len(tool.get("description") or "") for tool in tools),
        "input_schema_chars": sum(
            len(json.dumps(tool.get("inputSchema") or {}, separators=(",", ":")))
            for tool in tools
        ),
        "output_schema_chars": sum(
            len(json.dumps(tool["outputSchema"], separators=(",", ":")))
            for tool in tools
            if tool.get("outputSchema")
        ),
        "meta_chars": sum(
            len(json.dumps(tool["meta"], separators=(",", ":")))
            for tool in tools
            if tool.get("meta")
        ),
        "descriptions": {tool["name"]: tool.get("description") or "" for tool in tools},
    }


def estimate_tokens(text: str) -> dict:
    """Count tokens with cl100k when tiktoken is installed, and always report chars/4.

    cl100k_base is a representative BPE tokenizer (used by several OpenAI models).
    It is not the Claude or Cursor tokenizer. chars/4 is a separate rough estimate.
    """
    chars = len(text)
    rough = (chars + 3) // 4
    cl100k: Optional[int] = None
    try:
        import tiktoken

        cl100k = len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        cl100k = None
    return {"chars": chars, "chars_div_4": rough, "cl100k": cl100k}
