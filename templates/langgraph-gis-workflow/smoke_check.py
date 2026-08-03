"""Smoke-check stateful workflow (no LLM)."""

from __future__ import annotations

import asyncio
import os
import sys

os.environ.setdefault("SKIP_LLM", "1")
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")

from main import run  # noqa: E402


async def main() -> int:
    result = await run("smoke")
    print(result.get("final_answer"))
    if not result.get("validation_ok"):
        print("FAIL", result.get("errors"))
        return 1
    print("PASS smoke_check")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
