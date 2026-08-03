"""
LangChain + GIS MCP: park buffer proximity agent.

Connects to a running GIS MCP server over streamable HTTP, loads a focused
subset of geospatial tools, and runs either an interactive chat or a one-shot
demo query that performs real GIS analysis (CRS → project → buffer → intersect
→ geodetic distance).

Docs:
  - https://docs.langchain.com/oss/python/langchain/mcp
  - https://gis-mcp.com/gis-ai-agent/langchain/basic-geospatial-agent/
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any, List, Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

load_dotenv()

# Avoid corporate HTTP proxies intercepting local MCP traffic (common on Windows).
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")

# --- configuration (override via env) ---
OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
MCP_SERVER_URL: str = os.getenv("GIS_MCP_URL", "http://127.0.0.1:9010/mcp")
# Official LangChain MCP docs use transport "http" for streamable HTTP.
MCP_TRANSPORT: str = os.getenv("GIS_MCP_CLIENT_TRANSPORT", "streamable_http")

# Prefer OpenRouter when configured; otherwise OpenAI-compatible defaults.
USE_OPENROUTER: bool = bool(OPENROUTER_API_KEY)
MODEL_NAME: str = os.getenv(
    "GIS_AGENT_MODEL",
    "deepseek/deepseek-chat-v3.1" if USE_OPENROUTER else "gpt-4o-mini",
)
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
DEFAULT_TEMPERATURE: float = float(os.getenv("GIS_AGENT_TEMPERATURE", "0.2"))

# Keep the tool surface small so the agent stays reliable and cheap.
ALLOWED_TOOL_NAMES = frozenset(
    {
        "calculate_geodetic_distance",
        "get_utm_crs",
        "get_crs_info",
        "project_geometry",
        "buffer",
        "intersection",
        "get_area",
        "get_centroid",
        "is_valid",
    }
)

SYSTEM_PROMPT = """You are a GIS analyst agent. You MUST use GIS MCP tools for all
spatial calculations. Do not invent coordinates, distances, areas, or CRS codes.

Preferred workflow for meter-based buffers around lon/lat data:
1. confirm CRS context (WGS 84 / EPSG:4326 for lon/lat)
2. get_utm_crs for a representative [lon, lat] point
3. project_geometry from EPSG:4326 into that UTM CRS (geometry is WKT)
4. buffer in meters on the projected geometry
5. project other geometries into the same UTM CRS
6. intersection / get_area / get_centroid as needed
7. use calculate_geodetic_distance for lon/lat great-circle distance in meters

Geometry inputs to Shapely tools must be WKT strings (for example POINT(-73.97 40.78)).
For calculate_geodetic_distance and get_utm_crs, points are [longitude, latitude].
Use get_centroid (not a generic "centroid" name) when you need a center point.

Explain results clearly: CRS used, distances in meters, whether geometries intersect,
and cite tool outputs. If a tool errors, report the error and stop inventing numbers.
"""

# Fixed scenario used by --demo (no shapefiles required).
DEMO_QUERY = """A city planner is reviewing a proposed building near a small park.

Park footprint (WGS 84 lon/lat, WKT):
POLYGON((-73.9730 40.7720, -73.9710 40.7720, -73.9710 40.7735, -73.9730 40.7735, -73.9730 40.7720))

Proposed building footprint (WGS 84 lon/lat, WKT):
POLYGON((-73.9705 40.7724, -73.9698 40.7724, -73.9698 40.7729, -73.9705 40.7729, -73.9705 40.7724))

Please:
1. Find a suitable UTM CRS for this area using get_utm_crs on a park coordinate.
2. Project both polygons from EPSG:4326 into that UTM CRS.
3. Buffer the projected park by 100 meters.
4. Intersect the park buffer with the projected building.
5. Report whether they intersect (building within 100 m of the park) and the
   geodetic distance in meters between the park centroid and building centroid
   (use get_centroid on the WGS 84 polygons, then calculate_geodetic_distance
   with [lon, lat] from those centroid points).
6. Summarize with clear yes/no proximity conclusion and numeric results from tools.
"""


def resolve_api_key() -> Optional[str]:
    if OPENROUTER_API_KEY:
        return OPENROUTER_API_KEY
    if OPENAI_API_KEY:
        return OPENAI_API_KEY
    return None


def validate_environment() -> bool:
    if resolve_api_key():
        return True
    print("Error: No LLM API key found.")
    print("Set OPENROUTER_API_KEY or OPENAI_API_KEY in the environment or .env file.")
    print("See .env.example in this directory.")
    return False


def initialize_language_model() -> ChatOpenAI:
    api_key = resolve_api_key()
    if USE_OPENROUTER:
        return ChatOpenAI(
            model=MODEL_NAME,
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            temperature=DEFAULT_TEMPERATURE,
        )
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=api_key,
        temperature=DEFAULT_TEMPERATURE,
    )


def initialize_mcp_client() -> MultiServerMCPClient:
    print(f"MCP URL: {MCP_SERVER_URL}")
    print(f"MCP transport: {MCP_TRANSPORT}")
    return MultiServerMCPClient(
        {
            "gis": {
                "transport": MCP_TRANSPORT,
                "url": MCP_SERVER_URL,
            }
        }
    )


async def load_gis_tools(client: MultiServerMCPClient) -> Optional[List[Any]]:
    print(f"Fetching tools from {MCP_SERVER_URL} ...")
    try:
        tools = await client.get_tools()
    except Exception as exc:  # noqa: BLE001 - show actionable diagnostics
        print("\nFailed to connect to GIS MCP server.")
        print(f"  URL: {MCP_SERVER_URL}")
        print(f"  Error: {type(exc).__name__}: {exc}")
        print(
            "\nStart the server in another terminal:\n"
            "  Windows PowerShell:\n"
            "    $env:GIS_MCP_TRANSPORT='http'\n"
            "    $env:GIS_MCP_HOST='127.0.0.1'\n"
            "    $env:GIS_MCP_PORT='9010'\n"
            "    gis-mcp\n"
            "  macOS/Linux:\n"
            "    export GIS_MCP_TRANSPORT=http GIS_MCP_HOST=127.0.0.1 GIS_MCP_PORT=9010\n"
            "    gis-mcp\n"
            "  If get_tools fails with HTTP 503, set NO_PROXY=127.0.0.1,localhost "
            "and use http://127.0.0.1:9010/mcp (not localhost).\n"
        )
        return None

    if not tools:
        print("No tools returned. Is GIS MCP running with the expected install?")
        return None

    filtered = [t for t in tools if getattr(t, "name", None) in ALLOWED_TOOL_NAMES]
    print(f"Loaded {len(tools)} tools from server; using {len(filtered)} for this agent.")
    if len(filtered) < 5:
        print("Warning: expected core Shapely/PyProj tools missing. Check gis-mcp install.")
    return filtered


def extract_agent_response(result: dict) -> str:
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    else:
                        parts.append(str(block))
                return "\n".join(parts).strip() or str(content)
            return str(content)
    if messages:
        return str(messages[-1])
    return "No response generated"


def tool_call_summary(result: dict) -> List[str]:
    """Collect tool names invoked during the run (for demo logging)."""
    names: List[str] = []
    for msg in result.get("messages", []):
        tool_calls = getattr(msg, "tool_calls", None) or []
        for call in tool_calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                names.append(name)
    return names


async def run_query(agent: Any, query: str) -> str:
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    used = tool_call_summary(result)
    if used:
        print("Tools called: " + ", ".join(used))
    return extract_agent_response(result)


async def run_interactive_session(agent: Any) -> None:
    print("GIS Agent ready. Type 'exit', 'quit', or 'q' to stop.\n")
    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break
        if query.lower() in {"exit", "quit", "q"}:
            print("Session ended.")
            break
        if not query:
            continue
        try:
            response = await run_query(agent, query)
            print(f"Agent: {response}\n")
        except Exception as exc:  # noqa: BLE001
            print(f"Error during agent execution: {exc}\n")


async def async_main(demo: bool) -> int:
    if not validate_environment():
        return 1

    llm = initialize_language_model()
    client = initialize_mcp_client()
    tools = await load_gis_tools(client)
    if tools is None:
        return 1

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    if demo:
        print("\n--- Running demo query (park 100 m buffer proximity) ---\n")
        response = await run_query(agent, DEMO_QUERY)
        print(f"\nAgent:\n{response}\n")
        return 0

    await run_interactive_session(agent)
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangChain GIS MCP agent")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the fixed park-buffer proximity demo and exit",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(asyncio.run(async_main(demo=args.demo)))
