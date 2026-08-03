"""
Validate the LangGraph GIS workflow without requiring an LLM API key.

Requires GIS MCP HTTP server (default http://127.0.0.1:9010/mcp).
"""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure local package import when run from repo root or this folder
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("SKIP_LLM_INTERPRET", "1")
os.environ.setdefault("SKIP_LLM_RESPOND", "1")
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")

from gis_workflow_graph import DEMO_REQUEST, run_workflow  # noqa: E402


async def main() -> int:
    print("Running LangGraph GIS workflow verify (no LLM)...")
    result = await run_workflow(DEMO_REQUEST)
    print("stage:", result.get("stage"))
    print("plan:", result.get("plan_steps"))
    print("validation_ok:", result.get("validation_ok"))
    print("notes:", result.get("validation_notes"))
    print("errors:", result.get("errors"))
    print("\nfinal_answer:\n", result.get("final_answer"))

    if result.get("stage") != "done" or not result.get("validation_ok"):
        print("FAIL")
        return 1

    results = result.get("tool_results") or {}
    distance = (results.get("geodetic_distance") or {}).get("distance")
    if distance is None or not (50 < float(distance) < 800):
        print(f"FAIL unexpected distance: {distance}")
        return 1

    print("PASS LangGraph stateful GIS MCP workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
