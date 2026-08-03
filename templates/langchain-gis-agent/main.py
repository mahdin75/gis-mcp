"""
Minimal LangChain + GIS MCP single-agent template.

Customize: ALLOWED_TOOL_NAMES, SYSTEM_PROMPT, and your user query.
Tutorial: docs/gis-ai-agent/langchain/basic-geospatial-agent.md
"""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any, List, Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

load_dotenv()
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")

# --- customize ---
MCP_SERVER_URL = os.getenv("GIS_MCP_URL", "http://127.0.0.1:9010/mcp")
MCP_TRANSPORT = os.getenv("GIS_MCP_CLIENT_TRANSPORT", "streamable_http")
ALLOWED_TOOL_NAMES = frozenset(
    {
        # PLACEHOLDER: add/remove GIS MCP tool names for your use case
        "get_utm_crs",
        "project_geometry",
        "buffer",
        "intersection",
        "get_centroid",
        "calculate_geodetic_distance",
        "is_valid",
        "get_area",
    }
)
SYSTEM_PROMPT = """You are a GIS assistant. Use GIS MCP tools for all spatial math.
Never invent coordinates, CRS codes, distances, or areas.
For meter buffers on lon/lat data: get_utm_crs → project_geometry → buffer.
Shapely tools expect WKT; get_utm_crs / calculate_geodetic_distance use [lon, lat].
# PLACEHOLDER: add domain rules (units, deliverables, forbidden ops)
"""
# --- end customize ---

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENROUTER = bool(OPENROUTER_API_KEY)
MODEL_NAME = os.getenv(
    "GIS_AGENT_MODEL",
    "deepseek/deepseek-chat-v3.1" if USE_OPENROUTER else "gpt-4o-mini",
)


def _api_key() -> Optional[str]:
    return OPENROUTER_API_KEY or OPENAI_API_KEY


def build_llm() -> ChatOpenAI:
    key = _api_key()
    if not key:
        raise SystemExit("Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env")
    if USE_OPENROUTER:
        return ChatOpenAI(
            model=MODEL_NAME,
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.2,
        )
    return ChatOpenAI(model=MODEL_NAME, api_key=key, temperature=0.2)


async def load_tools() -> List[Any]:
    client = MultiServerMCPClient(
        {"gis": {"transport": MCP_TRANSPORT, "url": MCP_SERVER_URL}}
    )
    tools = await client.get_tools()
    return [t for t in tools if getattr(t, "name", None) in ALLOWED_TOOL_NAMES]


def _answer(result: dict) -> str:
    for msg in reversed(result.get("messages", [])):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return str(result.get("messages", [])[-1] if result.get("messages") else "")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        default="",
        help="User question (include WKT / lon-lat as needed)",
    )
    args = parser.parse_args()
    query = args.query.strip() or input("You: ").strip()
    if not query:
        return

    tools = await load_tools()
    if not tools:
        raise SystemExit(f"No allowed tools from {MCP_SERVER_URL}. Is gis-mcp running?")

    agent = create_agent(model=build_llm(), tools=tools, system_prompt=SYSTEM_PROMPT)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    print(_answer(result))


if __name__ == "__main__":
    asyncio.run(main())
