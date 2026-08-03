"""
Validate the multi-agent LangGraph GIS workflow without an LLM API key.
Requires GIS MCP HTTP (default http://127.0.0.1:9010/mcp).
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("SKIP_LLM_PLANNER", "1")
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")

from multi_agent_workflow import DEMO_REQUEST, run_multi_agent  # noqa: E402


async def main() -> int:
    print("Running multi-agent GIS workflow verify (no LLM)...")
    result = await run_multi_agent(DEMO_REQUEST)
    print("stage:", result.get("stage"))
    print("agent_log:", result.get("agent_log"))
    print("validation_ok:", result.get("validation_ok"))
    print("findings:", result.get("validation_findings"))
    print("errors:", result.get("errors"))
    print("\nfinal_answer:\n", result.get("final_answer"))

    if result.get("stage") != "done" or not result.get("validation_ok"):
        print("FAIL")
        return 1

    agents = [e.get("agent") for e in (result.get("agent_log") or [])]
    for required in ("planner", "analysis", "validation"):
        if required not in agents:
            print(f"FAIL missing agent in log: {required}")
            return 1

    # Planner and Validation must not appear as having executed tools.
    for entry in result.get("agent_log") or []:
        if entry.get("agent") == "planner" and entry.get("action") == "tools_executed":
            print("FAIL planner must not execute tools")
            return 1

    results = result.get("tool_results") or {}
    if not results.get("get_utm_crs") or not results.get("buffer"):
        print("FAIL missing analysis tool results")
        return 1

    distance = (results.get("geodetic_distance") or {}).get("distance")
    if distance is None or not (0 < float(distance) < 5000):
        print(f"FAIL unexpected distance: {distance}")
        return 1

    print("PASS multi-agent LangGraph GIS MCP workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
