"""Smoke-check multi-agent workflow (no LLM)."""

from __future__ import annotations

import asyncio
import os

os.environ.setdefault("SKIP_LLM_PLANNER", "1")
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")

from main import run  # noqa: E402


async def main() -> int:
    result = await run("smoke")
    print(result.get("final_answer"))
    log = result.get("agent_log") or []
    for need in ("planner:", "analysis:", "validation:"):
        if not any(need in str(x) for x in log):
            print(f"FAIL missing log marker {need}")
            return 1
    if not result.get("validation_ok"):
        print("FAIL", result.get("errors"))
        return 1
    print("PASS smoke_check")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
