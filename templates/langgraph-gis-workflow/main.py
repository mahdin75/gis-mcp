"""
Minimal LangGraph stateful GIS MCP workflow template.

Flow: interpret → plan → execute_tools → validate → respond (| handle_error)

Customize placeholders below. Full tutorial:
docs/gis-ai-agent/langgraph/stateful-geospatial-agent.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any, Dict, List, Literal, Optional, TypedDict

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END, START, StateGraph

load_dotenv()
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ.setdefault("SKIP_LLM", os.getenv("SKIP_LLM", "1"))

# --- customize ---
MCP_URL = os.getenv("GIS_MCP_URL", "http://127.0.0.1:9010/mcp")
MCP_TRANSPORT = os.getenv("GIS_MCP_CLIENT_TRANSPORT", "streamable_http")

# PLACEHOLDER: replace with your study geometries (WGS 84 WKT)
PLACEHOLDER_SITE_A = "POINT(-73.9855 40.7580)"  # feature to buffer
PLACEHOLDER_SITE_B = "POINT(-73.9820 40.7595)"  # feature to test
BUFFER_METERS = 400.0
REPRESENTATIVE_LONLAT = [-73.9855, 40.7580]

ALLOWED_TOOL_NAMES = frozenset(
    {
        "get_utm_crs",
        "project_geometry",
        "buffer",
        "intersection",
        "calculate_geodetic_distance",
        "is_valid",
    }
)
# --- end customize ---


class State(TypedDict, total=False):
    user_request: str
    site_a_wkt: str
    site_b_wkt: str
    buffer_meters: float
    lonlat: List[float]
    plan_steps: List[str]
    tool_results: Dict[str, Any]
    validation_ok: bool
    errors: List[str]
    final_answer: str


def _payload(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
    return {"raw": raw}


def _empty(wkt: Optional[str]) -> bool:
    return (not wkt) or ("EMPTY" in wkt.upper())


def _lonlat_from_point(wkt: str) -> List[float]:
    inner = wkt.upper().replace("POINT", "").replace("(", "").replace(")", "").strip()
    x, y = inner.split()[:2]
    return [float(x), float(y)]


async def _tools() -> Dict[str, Any]:
    client = MultiServerMCPClient(
        {"gis": {"transport": MCP_TRANSPORT, "url": MCP_URL}}
    )
    tools = await client.get_tools()
    out = {t.name: t for t in tools if t.name in ALLOWED_TOOL_NAMES}
    missing = ALLOWED_TOOL_NAMES - set(out)
    if missing:
        raise RuntimeError(f"Missing tools: {sorted(missing)}")
    return out


async def _call(tools: Dict[str, Any], name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return _payload(await tools[name].ainvoke(args))


def interpret(state: State) -> Dict[str, Any]:
    # PLACEHOLDER: parse user_request with LLM/heuristics; demo uses constants
    return {
        "site_a_wkt": PLACEHOLDER_SITE_A,
        "site_b_wkt": PLACEHOLDER_SITE_B,
        "buffer_meters": BUFFER_METERS,
        "lonlat": list(REPRESENTATIVE_LONLAT),
        "errors": [],
    }


def plan(state: State) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    return {
        "plan_steps": [
            "is_valid",
            "get_utm_crs",
            "project_geometry",
            "buffer",
            "intersection",
            "calculate_geodetic_distance",
        ],
        "tool_results": {},
    }


async def execute_tools(state: State) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    try:
        tools = await _tools()
        a, b = state["site_a_wkt"], state["site_b_wkt"]
        results: Dict[str, Any] = {}
        results["valid_a"] = await _call(tools, "is_valid", {"geometry": a})
        results["valid_b"] = await _call(tools, "is_valid", {"geometry": b})
        utm = await _call(tools, "get_utm_crs", {"coordinates": state["lonlat"]})
        crs = utm["crs"]
        results["utm"] = utm
        pa = await _call(
            tools,
            "project_geometry",
            {"geometry": a, "source_crs": "EPSG:4326", "target_crs": crs},
        )
        pb = await _call(
            tools,
            "project_geometry",
            {"geometry": b, "source_crs": "EPSG:4326", "target_crs": crs},
        )
        buf = await _call(
            tools,
            "buffer",
            {"geometry": pa["geometry"], "distance": float(state["buffer_meters"])},
        )
        inter = await _call(
            tools,
            "intersection",
            {"geometry1": buf["geometry"], "geometry2": pb["geometry"]},
        )
        dist = await _call(
            tools,
            "calculate_geodetic_distance",
            {
                "point1": _lonlat_from_point(a),
                "point2": _lonlat_from_point(b),
            },
        )
        results.update(
            {"project_a": pa, "project_b": pb, "buffer": buf, "intersection": inter, "distance": dist}
        )
        return {"tool_results": results, "errors": []}
    except Exception as exc:  # noqa: BLE001
        return {"errors": [f"execute failed: {exc}"]}


def validate(state: State) -> Dict[str, Any]:
    if state.get("errors"):
        return {"validation_ok": False}
    tr = state.get("tool_results") or {}
    ok = bool(tr.get("utm", {}).get("crs")) and "distance" in tr
    intersects = not _empty((tr.get("intersection") or {}).get("geometry"))
    answer = (
        f"UTM={tr.get('utm', {}).get('crs')}; "
        f"intersects={intersects}; "
        f"distance_m={(tr.get('distance') or {}).get('distance')}; "
        f"validation={'PASS' if ok else 'FAIL'}"
    )
    return {
        "validation_ok": ok,
        "final_answer": answer,
        "errors": [] if ok else ["validation failed"],
    }


def handle_error(state: State) -> Dict[str, Any]:
    return {
        "final_answer": "FAILED: " + "; ".join(state.get("errors") or ["unknown"]),
        "validation_ok": False,
    }


def _route_err(state: State, ok_node: str) -> Literal["handle_error"] | str:
    return "handle_error" if state.get("errors") else ok_node


def build_app():
    g = StateGraph(State)
    g.add_node("interpret", interpret)
    g.add_node("plan", plan)
    g.add_node("execute_tools", execute_tools)
    g.add_node("validate", validate)
    g.add_node("handle_error", handle_error)
    g.add_edge(START, "interpret")
    g.add_conditional_edges(
        "interpret", lambda s: _route_err(s, "plan"), ["plan", "handle_error"]
    )
    g.add_edge("plan", "execute_tools")
    g.add_conditional_edges(
        "execute_tools",
        lambda s: _route_err(s, "validate"),
        ["validate", "handle_error"],
    )
    g.add_conditional_edges(
        "validate",
        lambda s: "handle_error" if not s.get("validation_ok") else END,
        ["handle_error", END],
    )
    g.add_edge("handle_error", END)
    return g.compile()


async def run(request: str = "demo") -> State:
    app = build_app()
    return await app.ainvoke(  # type: ignore[return-value]
        {
            "user_request": request,
            "tool_results": {},
            "errors": [],
            "plan_steps": [],
        }
    )


async def async_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    result = await run("demo" if args.demo else "custom")
    print(result.get("final_answer"))
    return 0 if result.get("validation_ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
