"""
Minimal LangGraph multi-agent GIS MCP template.

Agents: planner (no tools) → analysis (GIS MCP only) → validation (inspect state).

Customize placeholders. Full tutorial:
docs/gis-ai-agent/langgraph/multi-agent-geospatial-workflow.md
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
os.environ.setdefault("SKIP_LLM_PLANNER", "1")

# --- customize ---
MCP_URL = os.getenv("GIS_MCP_URL", "http://127.0.0.1:9010/mcp")
MCP_TRANSPORT = os.getenv("GIS_MCP_CLIENT_TRANSPORT", "streamable_http")

# PLACEHOLDER: hazard to buffer, subject to test (WGS 84 WKT)
PLACEHOLDER_HAZARD = "LINESTRING(-73.9900 40.7400, -73.9800 40.7450, -73.9700 40.7420)"
PLACEHOLDER_SUBJECT = (
    "POLYGON((-73.9780 40.7430, -73.9760 40.7430, "
    "-73.9760 40.7445, -73.9780 40.7445, -73.9780 40.7430))"
)
SETBACK_METERS = 150.0
REPRESENTATIVE_LONLAT = [-73.9800, 40.7450]

ANALYSIS_TOOLS = frozenset(
    {
        "get_utm_crs",
        "get_crs_info",
        "project_geometry",
        "buffer",
        "intersection",
        "get_centroid",
        "calculate_geodetic_distance",
        "is_valid",
    }
)
# --- end customize ---


class State(TypedDict, total=False):
    user_request: str
    hazard_wkt: str
    subject_wkt: str
    setback_meters: float
    lonlat: List[float]
    analysis_plan: List[str]
    tool_results: Dict[str, Any]
    validation_ok: bool
    findings: List[str]
    errors: List[str]
    final_answer: str
    agent_log: List[str]


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


def _log(state: State, msg: str) -> List[str]:
    return list(state.get("agent_log") or []) + [msg]


def planner_agent(state: State) -> Dict[str, Any]:
    """Planner: structure the job. Does NOT call GIS MCP."""
    # PLACEHOLDER: replace with LLM structured output when SKIP_LLM_PLANNER is unset
    return {
        "hazard_wkt": PLACEHOLDER_HAZARD,
        "subject_wkt": PLACEHOLDER_SUBJECT,
        "setback_meters": SETBACK_METERS,
        "lonlat": list(REPRESENTATIVE_LONLAT),
        "analysis_plan": [
            "is_valid",
            "get_utm_crs",
            "project",
            "buffer",
            "intersection",
            "distance",
        ],
        "errors": [],
        "agent_log": _log(state, "planner:plan_created"),
    }


async def analysis_agent(state: State) -> Dict[str, Any]:
    """Analysis: sole GIS MCP caller."""
    if state.get("errors"):
        return {"agent_log": _log(state, "analysis:skipped")}
    try:
        client = MultiServerMCPClient(
            {"gis": {"transport": MCP_TRANSPORT, "url": MCP_URL}}
        )
        tools = {
            t.name: t
            for t in await client.get_tools()
            if t.name in ANALYSIS_TOOLS
        }
        missing = ANALYSIS_TOOLS - set(tools)
        if missing:
            raise RuntimeError(f"Missing tools: {sorted(missing)}")

        async def call(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            return _payload(await tools[name].ainvoke(args))

        h, s = state["hazard_wkt"], state["subject_wkt"]
        results: Dict[str, Any] = {}
        results["valid_h"] = await call("is_valid", {"geometry": h})
        results["valid_s"] = await call("is_valid", {"geometry": s})
        utm = await call("get_utm_crs", {"coordinates": state["lonlat"]})
        crs = utm["crs"]
        results["utm"] = utm
        results["crs_info"] = await call("get_crs_info", {"crs": crs})
        ph = await call(
            "project_geometry",
            {"geometry": h, "source_crs": "EPSG:4326", "target_crs": crs},
        )
        ps = await call(
            "project_geometry",
            {"geometry": s, "source_crs": "EPSG:4326", "target_crs": crs},
        )
        buf = await call(
            "buffer",
            {"geometry": ph["geometry"], "distance": float(state["setback_meters"])},
        )
        inter = await call(
            "intersection",
            {"geometry1": buf["geometry"], "geometry2": ps["geometry"]},
        )
        cen = await call("get_centroid", {"geometry": s})
        inner = (
            str(cen["geometry"])
            .upper()
            .replace("POINT", "")
            .replace("(", "")
            .replace(")", "")
            .strip()
        )
        x, y = inner.split()[:2]
        dist = await call(
            "calculate_geodetic_distance",
            {"point1": [float(x), float(y)], "point2": list(state["lonlat"])},
        )
        results.update(
            {
                "project_h": ph,
                "project_s": ps,
                "buffer": buf,
                "intersection": inter,
                "centroid": cen,
                "distance": dist,
            }
        )
        return {
            "tool_results": results,
            "errors": [],
            "agent_log": _log(state, "analysis:tools_executed"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"analysis failed: {exc}"],
            "agent_log": _log(state, f"analysis:failed:{exc}"),
        }


def validation_agent(state: State) -> Dict[str, Any]:
    """Validation: inspect results only — no GIS MCP calls."""
    if state.get("errors"):
        return {
            "validation_ok": False,
            "final_answer": "FAILED: " + "; ".join(state["errors"]),
            "agent_log": _log(state, "validation:skipped"),
        }
    tr = state.get("tool_results") or {}
    findings: List[str] = []
    ok = True
    crs = (tr.get("utm") or {}).get("crs")
    if not crs:
        ok = False
        findings.append("missing UTM CRS")
    else:
        findings.append(f"CRS={crs}")
        name = (tr.get("crs_info") or {}).get("name")
        if name:
            findings.append(f"CRS name={name}")
    encroaches = not _empty((tr.get("intersection") or {}).get("geometry"))
    findings.append(f"encroaches={encroaches}")
    distance = (tr.get("distance") or {}).get("distance")
    if distance is None:
        ok = False
        findings.append("missing distance")
    else:
        findings.append(f"distance_m={distance}")
    log = _log(state, "validation:completed")
    answer = (
        f"setback={state.get('setback_meters')}m; "
        f"encroaches={encroaches}; distance_m={distance}; "
        f"validation={'PASS' if ok else 'FAIL'}; "
        f"findings={findings}; agents={log}"
    )
    return {
        "validation_ok": ok,
        "findings": findings,
        "final_answer": answer,
        "errors": [] if ok else ["validation failed"],
        "agent_log": log,
    }


def handle_error(state: State) -> Dict[str, Any]:
    return {
        "final_answer": "FAILED: " + "; ".join(state.get("errors") or ["unknown"]),
        "validation_ok": False,
        "agent_log": _log(state, "system:handle_error"),
    }


def build_app():
    g = StateGraph(State)
    g.add_node("planner_agent", planner_agent)
    g.add_node("analysis_agent", analysis_agent)
    g.add_node("validation_agent", validation_agent)
    g.add_node("handle_error", handle_error)
    g.add_edge(START, "planner_agent")
    g.add_conditional_edges(
        "planner_agent",
        lambda s: "handle_error" if s.get("errors") else "analysis_agent",
        ["analysis_agent", "handle_error"],
    )
    g.add_conditional_edges(
        "analysis_agent",
        lambda s: "handle_error" if s.get("errors") else "validation_agent",
        ["validation_agent", "handle_error"],
    )
    g.add_edge("validation_agent", END)
    g.add_edge("handle_error", END)
    return g.compile()


async def run(request: str = "demo") -> State:
    app = build_app()
    return await app.ainvoke(  # type: ignore[return-value]
        {
            "user_request": request,
            "tool_results": {},
            "errors": [],
            "findings": [],
            "analysis_plan": [],
            "agent_log": [],
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
