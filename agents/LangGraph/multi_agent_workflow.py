"""
LangGraph multi-agent GIS workflow (Planner → Analysis → Validation).

Three agents with separated responsibilities share one GISWorkflowMultiState.
Only the Analysis agent calls GIS MCP tools. Validation inspects results
without re-running the full tool chain (avoids redundant MCP/LLM cost).

Sample task: river-hazard setback — does a building intersect a metric
buffer around a hazard line?

Docs: https://gis-mcp.com/gis-ai-agent/langgraph/multi-agent-geospatial-workflow/
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from typing import Any, Dict, List, Literal, Optional, TypedDict

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

load_dotenv()

os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_SERVER_URL = os.getenv("GIS_MCP_URL", "http://127.0.0.1:9010/mcp")
MCP_TRANSPORT = os.getenv("GIS_MCP_CLIENT_TRANSPORT", "streamable_http")
USE_OPENROUTER = bool(OPENROUTER_API_KEY)
MODEL_NAME = os.getenv(
    "GIS_AGENT_MODEL",
    "deepseek/deepseek-chat-v3.1" if USE_OPENROUTER else "gpt-4o-mini",
)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
TEMPERATURE = float(os.getenv("GIS_AGENT_TEMPERATURE", "0.1"))

# Analysis agent is the only role allowed to call GIS MCP.
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
        "get_area",
    }
)

# Distinct from the single-agent transit-coverage demo.
DEMO_REQUEST = """Compliance check: does the proposed building encroach a 150-meter
setback from the river hazard centerline?

River hazard (WGS 84, WKT):
LINESTRING(-73.9900 40.7400, -73.9800 40.7450, -73.9700 40.7420)

Proposed building (WGS 84, WKT):
POLYGON((-73.9780 40.7430, -73.9760 40.7430, -73.9760 40.7445, -73.9780 40.7445, -73.9780 40.7430))

Project to a suitable UTM CRS before buffering. Report whether the building
intersects the 150 m setback buffer and the geodetic distance from the building
centroid to a representative point on the hazard (-73.9800, 40.7450).
"""


class AgentLogEntry(TypedDict, total=False):
    agent: str
    action: str
    summary: str


class MultiAgentGISState(TypedDict, total=False):
    """Shared state across Planner, Analysis, and Validation agents."""

    user_request: str
    # Planner outputs
    hazard_wkt: str
    building_wkt: str
    setback_meters: float
    representative_lonlat: List[float]
    analysis_plan: List[str]
    planner_notes: str
    # Analysis outputs (GIS MCP)
    tool_results: Dict[str, Any]
    analysis_summary: str
    # Validation outputs
    validation_ok: bool
    validation_findings: List[str]
    # Coordination
    agent_log: List[AgentLogEntry]
    errors: List[str]
    final_answer: str
    stage: str


class PlannerOutput(BaseModel):
    hazard_wkt: str = Field(description="WKT of the hazard / setback source geometry")
    building_wkt: str = Field(description="WKT of the building / subject geometry")
    setback_meters: float = Field(description="Setback buffer distance in meters")
    representative_lonlat: List[float] = Field(
        description="[lon, lat] for UTM CRS selection near the study area"
    )
    analysis_plan: List[str] = Field(
        description="Ordered GIS MCP steps the Analysis agent must follow"
    )
    notes: str = Field(description="Short planner rationale (no invented coordinates)")


def resolve_api_key() -> Optional[str]:
    return OPENROUTER_API_KEY or OPENAI_API_KEY


def build_llm() -> ChatOpenAI:
    key = resolve_api_key()
    if not key:
        raise RuntimeError("LLM API key required when SKIP_LLM_PLANNER is not set.")
    if USE_OPENROUTER:
        return ChatOpenAI(
            model=MODEL_NAME,
            api_key=key,
            base_url=OPENROUTER_BASE_URL,
            temperature=TEMPERATURE,
        )
    return ChatOpenAI(model=MODEL_NAME, api_key=key, temperature=TEMPERATURE)


def _append_log(
    state: MultiAgentGISState, agent: str, action: str, summary: str
) -> List[AgentLogEntry]:
    log = list(state.get("agent_log") or [])
    log.append({"agent": agent, "action": action, "summary": summary})
    return log


def _parse_tool_payload(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and "text" in item:
                try:
                    return json.loads(item["text"])
                except (json.JSONDecodeError, TypeError):
                    continue
        return {"raw": raw}
    return {"raw": raw}


def _is_empty_wkt(wkt: Optional[str]) -> bool:
    if not wkt:
        return True
    return "EMPTY" in wkt.upper()


def _wkt_point_to_lonlat(wkt: str) -> List[float]:
    inner = wkt.upper().replace("POINT Z", "POINT").replace("POINT", "")
    inner = inner.replace("(", "").replace(")", "").strip()
    parts = inner.split()
    return [float(parts[0]), float(parts[1])]


def _extract_wkt_candidates(text: str) -> List[str]:
    """Extract WKT geometries with balanced parentheses (order of appearance)."""
    type_pattern = re.compile(
        r"(MULTI(?:POINT|LINESTRING|POLYGON)|POINT|LINESTRING|POLYGON)\s*\(",
        re.IGNORECASE,
    )
    found: List[str] = []
    for match in type_pattern.finditer(text):
        start = match.start()
        paren_start = match.end() - 1  # index of '('
        depth = 0
        for k in range(paren_start, len(text)):
            ch = text[k]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    found.append(text[start : k + 1].strip())
                    break
    return found


def default_analysis_plan() -> List[str]:
    return [
        "is_valid(hazard)",
        "is_valid(building)",
        "get_utm_crs",
        "project_geometry(hazard)",
        "project_geometry(building)",
        "buffer(hazard_utm, setback_meters)",
        "intersection(setback_buffer, building_utm)",
        "get_centroid(building)",
        "calculate_geodetic_distance(building_centroid, hazard_point)",
    ]


def heuristic_planner(user_request: str) -> PlannerOutput:
    """Deterministic Planner used by --demo / verify (no LLM)."""
    wkts = _extract_wkt_candidates(user_request)
    if len(wkts) < 2:
        raise ValueError("Planner needs hazard and building WKT geometries.")
    meters = 150.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*meter", user_request, re.IGNORECASE)
    if m:
        meters = float(m.group(1))
    hazard, building = wkts[0], wkts[1]
    # Prefer an explicit lon/lat mentioned for the hazard sample point.
    lonlat = [-73.9800, 40.7450]
    pt = re.search(
        r"\((-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\)",
        user_request,
    )
    if pt:
        lonlat = [float(pt.group(1)), float(pt.group(2))]
    return PlannerOutput(
        hazard_wkt=hazard,
        building_wkt=building,
        setback_meters=meters,
        representative_lonlat=lonlat,
        analysis_plan=default_analysis_plan(),
        notes=(
            "Heuristic planner: buffer hazard in UTM meters, test building "
            "intersection, measure geodetic distance from building centroid."
        ),
    )


async def load_analysis_tools() -> Dict[str, Any]:
    client = MultiServerMCPClient(
        {
            "gis": {
                "transport": MCP_TRANSPORT,
                "url": MCP_SERVER_URL,
            }
        }
    )
    tools = await client.get_tools()
    filtered = {
        t.name: t for t in tools if getattr(t, "name", None) in ANALYSIS_TOOLS
    }
    missing = ANALYSIS_TOOLS - set(filtered)
    if missing:
        raise RuntimeError(f"Analysis agent missing GIS MCP tools: {sorted(missing)}")
    return filtered


async def call_tool(
    tools: Dict[str, Any], name: str, args: Dict[str, Any]
) -> Dict[str, Any]:
    if name not in ANALYSIS_TOOLS:
        raise PermissionError(f"Tool '{name}' is not allowed for Analysis agent")
    raw = await tools[name].ainvoke(args)
    return _parse_tool_payload(raw)


# --- Agent nodes ---


def planner_agent(state: MultiAgentGISState) -> Dict[str, Any]:
    """
    GIS Planner Agent — interprets the request and writes a structured plan.
    Does NOT call GIS MCP tools (avoids mixing planning with execution).
    """
    request = state.get("user_request") or ""
    skip_llm = os.getenv("SKIP_LLM_PLANNER", "").lower() in {"1", "true", "yes"}
    try:
        if skip_llm or not resolve_api_key():
            plan = heuristic_planner(request)
        else:
            llm = build_llm()
            structured = llm.with_structured_output(PlannerOutput)
            plan = structured.invoke(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are the GIS Planner Agent. Extract hazard and "
                            "building WKT, setback meters, and a representative "
                            "[lon, lat]. Produce an ordered analysis_plan using "
                            "only GIS MCP capabilities: is_valid, get_utm_crs, "
                            "project_geometry, buffer, intersection, get_centroid, "
                            "calculate_geodetic_distance. Do not invent coordinates. "
                            "Do not execute tools."
                        ),
                    },
                    {"role": "user", "content": request},
                ]
            )
            if not plan.analysis_plan:
                plan.analysis_plan = default_analysis_plan()

        return {
            "hazard_wkt": plan.hazard_wkt,
            "building_wkt": plan.building_wkt,
            "setback_meters": float(plan.setback_meters),
            "representative_lonlat": list(plan.representative_lonlat),
            "analysis_plan": list(plan.analysis_plan),
            "planner_notes": plan.notes,
            "errors": [],
            "stage": "planned",
            "agent_log": _append_log(
                state,
                "planner",
                "plan_created",
                f"setback={plan.setback_meters}m; steps={len(plan.analysis_plan)}",
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"planner failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
            "agent_log": _append_log(
                state, "planner", "failed", f"{type(exc).__name__}: {exc}"
            ),
        }


async def analysis_agent(state: MultiAgentGISState) -> Dict[str, Any]:
    """
    GIS Analysis Agent — sole owner of GIS MCP tool calls.
    Follows planner.analysis_plan; does not redesign the study.
    """
    if state.get("errors"):
        return {"stage": "error"}

    try:
        tools = await load_analysis_tools()
        results: Dict[str, Any] = {}
        hazard = state["hazard_wkt"]
        building = state["building_wkt"]
        setback = float(state["setback_meters"])
        lonlat = state["representative_lonlat"]

        results["is_valid_hazard"] = await call_tool(
            tools, "is_valid", {"geometry": hazard}
        )
        results["is_valid_building"] = await call_tool(
            tools, "is_valid", {"geometry": building}
        )
        if not results["is_valid_hazard"].get("is_valid", True):
            raise ValueError(f"Hazard geometry invalid: {results['is_valid_hazard']}")
        if not results["is_valid_building"].get("is_valid", True):
            raise ValueError(
                f"Building geometry invalid: {results['is_valid_building']}"
            )

        utm = await call_tool(tools, "get_utm_crs", {"coordinates": lonlat})
        utm_crs = utm.get("crs")
        if not utm_crs:
            raise ValueError(f"get_utm_crs returned no crs: {utm}")
        results["get_utm_crs"] = utm

        # Optional CRS metadata for the Validation agent (no extra projection).
        results["get_crs_info"] = await call_tool(
            tools, "get_crs_info", {"crs": utm_crs}
        )

        proj_h = await call_tool(
            tools,
            "project_geometry",
            {
                "geometry": hazard,
                "source_crs": "EPSG:4326",
                "target_crs": utm_crs,
            },
        )
        proj_b = await call_tool(
            tools,
            "project_geometry",
            {
                "geometry": building,
                "source_crs": "EPSG:4326",
                "target_crs": utm_crs,
            },
        )
        results["project_hazard"] = proj_h
        results["project_building"] = proj_b
        h_utm = proj_h.get("geometry")
        b_utm = proj_b.get("geometry")
        if not h_utm or not b_utm:
            raise ValueError("Projection missing geometry")

        buffered = await call_tool(
            tools, "buffer", {"geometry": h_utm, "distance": setback}
        )
        results["buffer"] = buffered
        buffer_geom = buffered.get("geometry")
        if not buffer_geom:
            raise ValueError("Buffer missing geometry")

        inter = await call_tool(
            tools,
            "intersection",
            {"geometry1": buffer_geom, "geometry2": b_utm},
        )
        results["intersection"] = inter

        centroid = await call_tool(
            tools, "get_centroid", {"geometry": building}
        )
        results["building_centroid"] = centroid
        c_wkt = centroid.get("geometry")
        if not c_wkt:
            raise ValueError("get_centroid missing geometry")

        dist = await call_tool(
            tools,
            "calculate_geodetic_distance",
            {
                "point1": _wkt_point_to_lonlat(str(c_wkt)),
                "point2": list(lonlat),
            },
        )
        results["geodetic_distance"] = dist

        encroaches = not _is_empty_wkt(inter.get("geometry"))
        summary = (
            f"UTM={utm_crs}; encroaches_setback={encroaches}; "
            f"geodetic_m={dist.get('distance')}"
        )
        return {
            "tool_results": results,
            "analysis_summary": summary,
            "errors": [],
            "stage": "analyzed",
            "agent_log": _append_log(
                state, "analysis", "tools_executed", summary
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": list(state.get("errors") or [])
            + [f"analysis failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
            "agent_log": _append_log(
                state, "analysis", "failed", f"{type(exc).__name__}: {exc}"
            ),
        }


def validation_agent(state: MultiAgentGISState) -> Dict[str, Any]:
    """
    GIS Validation Agent — checks Analysis outputs and CRS assumptions.
    Does NOT call GIS MCP again (no redundant tool round-trips).
    """
    if state.get("errors"):
        return {
            "validation_ok": False,
            "stage": "error",
            "agent_log": _append_log(
                state, "validation", "skipped", "upstream errors present"
            ),
        }

    findings: List[str] = []
    ok = True
    results = state.get("tool_results") or {}

    utm = (results.get("get_utm_crs") or {}).get("crs")
    crs_info = results.get("get_crs_info") or {}
    if not utm:
        ok = False
        findings.append("Missing UTM CRS from Analysis.")
    else:
        findings.append(f"CRS assumption checked: Analysis used {utm}.")
        name = crs_info.get("name")
        if name:
            findings.append(f"CRS name: {name}")
        if "326" not in str(utm) and "327" not in str(utm) and "UTM" not in str(name or ""):
            findings.append(
                "Warning: CRS does not look like a UTM EPSG code; meter buffers may be wrong."
            )

    if not (results.get("is_valid_hazard") or {}).get("is_valid", False):
        ok = False
        findings.append("Hazard geometry reported invalid.")
    if not (results.get("is_valid_building") or {}).get("is_valid", False):
        ok = False
        findings.append("Building geometry reported invalid.")

    proj_h = results.get("project_hazard") or {}
    proj_b = results.get("project_building") or {}
    if proj_h.get("source_crs") != "EPSG:4326" or proj_b.get("source_crs") != "EPSG:4326":
        findings.append("Note: expected source CRS EPSG:4326 for inputs.")
    if utm and (
        proj_h.get("target_crs") != utm or proj_b.get("target_crs") != utm
    ):
        ok = False
        findings.append("Projection target CRS does not match get_utm_crs result.")

    inter = (results.get("intersection") or {}).get("geometry")
    encroaches = not _is_empty_wkt(inter)
    findings.append(f"Building intersects setback buffer: {encroaches}")

    distance = (results.get("geodetic_distance") or {}).get("distance")
    setback = float(state.get("setback_meters") or 0)
    if distance is None:
        ok = False
        findings.append("Missing geodetic distance.")
    else:
        findings.append(f"Geodetic distance to hazard sample point (m): {distance}")
        # Soft QA: very large distances with intersection may indicate swapped CRS.
        if encroaches and float(distance) > max(setback * 20, 5000):
            ok = False
            findings.append(
                "Likely error: intersection non-empty but distance is implausibly large "
                "vs setback — check CRS / coordinates."
            )

    if not results.get("buffer"):
        ok = False
        findings.append("Missing buffer tool result.")

    log = _append_log(
        state,
        "validation",
        "completed",
        f"ok={ok}; findings={len(findings)}",
    )
    # Compose after logging so the Validation agent appears in the audit trail.
    state_for_answer = {**state, "agent_log": log, "validation_findings": findings}
    answer = _compose_final_answer(
        state_for_answer, encroaches, distance, utm, findings, ok
    )
    return {
        "validation_ok": ok,
        "validation_findings": findings,
        "final_answer": answer,
        "stage": "done" if ok else "failed",
        "errors": []
        if ok
        else list(state.get("errors") or [])
        + ["validation failed: " + "; ".join(findings)],
        "agent_log": log,
    }


def _compose_final_answer(
    state: MultiAgentGISState,
    encroaches: bool,
    distance: Any,
    utm: Any,
    findings: List[str],
    ok: bool,
) -> str:
    plan = state.get("analysis_plan") or []
    log = state.get("agent_log") or []
    agents_run = [e.get("agent") for e in log]
    return (
        "Multi-agent GIS setback workflow\n"
        f"- Planner notes: {state.get('planner_notes')}\n"
        f"- Setback: {state.get('setback_meters')} m\n"
        f"- UTM CRS: {utm}\n"
        f"- Building encroaches setback: {encroaches}\n"
        f"- Geodetic distance (building centroid -> hazard sample): {distance} m\n"
        f"- Validation: {'PASS' if ok else 'FAIL'}\n"
        f"- Findings:\n  - " + "\n  - ".join(findings) + "\n"
        f"- Plan: {', '.join(plan)}\n"
        f"- Agents invoked (order): {agents_run}\n"
    )


def handle_error(state: MultiAgentGISState) -> Dict[str, Any]:
    errs = state.get("errors") or ["Unknown multi-agent failure"]
    answer = (
        "Multi-agent GIS workflow failed.\n"
        "Errors:\n- "
        + "\n- ".join(errs)
        + "\nNo invented setback or distance values were returned.\n"
        f"Agent log: {state.get('agent_log')}\n"
    )
    return {
        "final_answer": answer,
        "validation_ok": False,
        "stage": "failed",
        "agent_log": _append_log(state, "system", "handle_error", "workflow aborted"),
    }


def route_after_planner(
    state: MultiAgentGISState,
) -> Literal["analysis_agent", "handle_error"]:
    return "handle_error" if state.get("errors") else "analysis_agent"


def route_after_analysis(
    state: MultiAgentGISState,
) -> Literal["validation_agent", "handle_error"]:
    return "handle_error" if state.get("errors") else "validation_agent"


def build_multi_agent_graph():
    graph = StateGraph(MultiAgentGISState)
    graph.add_node("planner_agent", planner_agent)
    graph.add_node("analysis_agent", analysis_agent)
    graph.add_node("validation_agent", validation_agent)
    graph.add_node("handle_error", handle_error)

    graph.add_edge(START, "planner_agent")
    graph.add_conditional_edges("planner_agent", route_after_planner)
    graph.add_conditional_edges("analysis_agent", route_after_analysis)
    graph.add_edge("validation_agent", END)
    graph.add_edge("handle_error", END)
    return graph.compile()


async def run_multi_agent(user_request: str) -> MultiAgentGISState:
    app = build_multi_agent_graph()
    return await app.ainvoke(  # type: ignore[return-value]
        {
            "user_request": user_request,
            "tool_results": {},
            "validation_findings": [],
            "errors": [],
            "analysis_plan": [],
            "agent_log": [],
        }
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LangGraph multi-agent GIS MCP workflow")
    p.add_argument("--demo", action="store_true", help="Run river setback demo")
    p.add_argument("--request", type=str, default="")
    return p.parse_args()


async def async_main() -> int:
    args = parse_args()
    if args.demo:
        os.environ.setdefault("SKIP_LLM_PLANNER", "1")
        request = DEMO_REQUEST
    elif args.request:
        request = args.request
    else:
        print("Enter a setback / coverage request (or --demo).")
        request = input("You: ").strip()
        if not request:
            return 0

    print(f"MCP URL: {MCP_SERVER_URL} ({MCP_TRANSPORT})")
    result = await run_multi_agent(request)
    print("\n--- stage:", result.get("stage"))
    print("--- agent_log:", result.get("agent_log"))
    print("--- validation_ok:", result.get("validation_ok"))
    print("--- findings:", result.get("validation_findings"))
    if result.get("errors"):
        print("--- errors:", result.get("errors"))
    print("\nFinal answer:\n")
    print(result.get("final_answer") or "(empty)")
    ok = result.get("stage") == "done" and result.get("validation_ok")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
