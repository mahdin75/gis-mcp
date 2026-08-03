"""Smoke-check: discover GIS MCP tools (no LLM)."""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")

URL = os.getenv("GIS_MCP_URL", "http://127.0.0.1:9010/mcp")
TRANSPORT = os.getenv("GIS_MCP_CLIENT_TRANSPORT", "streamable_http")
EXPECTED = {"get_utm_crs", "project_geometry", "buffer", "intersection"}


async def main() -> int:
    print(f"Connecting {URL} ({TRANSPORT})")
    client = MultiServerMCPClient({"gis": {"transport": TRANSPORT, "url": URL}})
    try:
        tools = await client.get_tools()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return 1
    names = {t.name for t in tools}
    print(f"Discovered {len(names)} tools")
    missing = EXPECTED - names
    if missing:
        print(f"FAIL missing: {sorted(missing)}")
        return 1
    print("PASS smoke_check")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
