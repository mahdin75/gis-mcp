"""
LangGraph + GIS MCP: stateful site-coverage workflow.

Graph stages (not a free-form ReAct loop):
  interpret → plan → execute_tools → validate → respond
                 ↘ handle_error ↗

Why LangGraph here:
  - Explicit GISWorkflowState (plan, tool_results, validation flags)
  - Deterministic CRS-safe tool order after planning
  - Validation gate before the final answer
  - Error branch without inventing spatial numbers

Docs:
  - https://docs.langchain.com/oss/python/langgraph/quickstart
  - https://github.com/langchain-ai/langchain-mcp-adapters
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

ALLOWED_TOOL_NAMES = frozenset(
    {
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

# Transit-stop coverage demo (different scenario from the LangChain park tutorial).
DEMO_REQUEST = """A planner asks: is this school within a 400-meter walking buffer of the transit stop?

Transit stop (WGS 84, WKT):
POINT(-73.9855 40.7580)

School (WGS 84, WKT):
POINT(-73.9820 40.7595)

Use a metric UTM CRS for the buffer. Report whether the school intersects the
400 m buffer and the geodetic distance between the two points in meters.
"""


class GISWorkflowState(TypedDict, total=False):
    """Explicit graph state for a CRS-safe GIS MCP pipeline."""

    user_request: str
    # Interpreted fields
    site_a_wkt: str  # feature to buffer (e.g. transit stop)
    site_b_wkt: str  # feature to test (e.g. school)
    buffer_meters: float
    representative_lonlat: List[float]
    # Planning / execution
    plan_steps: List[str]
    tool_results: Dict[str, Any]
    # Validation / errors / answer
    validation_ok: bool
    validation_notes: List[str]
    errors: List[str]
    final_answer: str
    stage: str


class InterpretedRequest(BaseModel):
    """Structured extraction from the user request."""

    site_a_wkt: str = Field(description="WKT geometry to buffer (site A)")
    site_b_wkt: str = Field(description="WKT geometry to test against the buffer (site B)")
    buffer_meters: float = Field(description="Buffer distance in meters")
    representative_lonlat: List[float] = Field(
        description="[longitude, latitude] near the study area for UTM selection"
    )


def resolve_api_key() -> Optional[str]:
    return OPENROUTER_API_KEY or OPENAI_API_KEY


def build_llm() -> ChatOpenAI:
    key = resolve_api_key()
    if not key:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY or OPENAI_API_KEY for interpret/respond nodes."
        )
    if USE_OPENROUTER:
        return ChatOpenAI(
            model=MODEL_NAME,
            api_key=key,
            base_url=OPENROUTER_BASE_URL,
            temperature=TEMPERATURE,
        )
    return ChatOpenAI(model=MODEL_NAME, api_key=key, temperature=TEMPERATURE)


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


def _wkt_point_to_lonlat(wkt: str) -> List[float]:
    inner = wkt.upper().replace("POINT Z", "POINT").replace("POINT", "")
    inner = inner.replace("(", "").replace(")", "").strip()
    parts = inner.split()
    return [float(parts[0]), float(parts[1])]


def _is_empty_wkt(wkt: Optional[str]) -> bool:
    if not wkt:
        return True
    return "EMPTY" in wkt.upper()


def _extract_wkt_candidates(text: str) -> List[str]:
    pattern = re.compile(
        r"((?:POINT|POLYGON|LINESTRING|MULTIPOLYGON|MULTIPOINT)"
        r"\s*\([^;]+?\))",
        re.IGNORECASE | re.DOTALL,
    )
    return [m.group(1).strip() for m in pattern.finditer(text)]


def heuristic_interpret(user_request: str) -> InterpretedRequest:
    """Deterministic fallback used by --demo / verify (no LLM)."""
    wkts = _extract_wkt_candidates(user_request)
    if len(wkts) < 2:
        raise ValueError("Need at least two WKT geometries in the request.")
    meters = 400.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*meter", user_request, re.IGNORECASE)
    if m:
        meters = float(m.group(1))
    site_a, site_b = wkts[0], wkts[1]
    if site_a.upper().startswith("POINT"):
        lonlat = _wkt_point_to_lonlat(site_a)
    else:
        lonlat = [-73.9855, 40.7580]
    return InterpretedRequest(
        site_a_wkt=site_a,
        site_b_wkt=site_b,
        buffer_meters=meters,
        representative_lonlat=lonlat,
    )


async def load_mcp_tools() -> Dict[str, Any]:
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
        t.name: t for t in tools if getattr(t, "name", None) in ALLOWED_TOOL_NAMES
    }
    missing = ALLOWED_TOOL_NAMES - set(filtered)
    if missing:
        raise RuntimeError(f"Missing GIS MCP tools: {sorted(missing)}")
    return filtered


async def call_tool(
    tools: Dict[str, Any], name: str, args: Dict[str, Any]
) -> Dict[str, Any]:
    raw = await tools[name].ainvoke(args)
    return _parse_tool_payload(raw)


# --- graph nodes ---


def interpret_node(state: GISWorkflowState) -> Dict[str, Any]:
    """Interpret the user request into structured GIS inputs."""
    request = state.get("user_request") or ""
    # Prefer heuristic for reproducibility when SKIP_LLM_INTERPRET=1 or no key.
    skip_llm = os.getenv("SKIP_LLM_INTERPRET", "").lower() in {"1", "true", "yes"}
    try:
        if skip_llm or not resolve_api_key():
            parsed = heuristic_interpret(request)
        else:
            llm = build_llm()
            structured = llm.with_structured_output(InterpretedRequest)
            parsed = structured.invoke(
                [
                    {
                        "role": "system",
                        "content": (
                            "Extract site A (to buffer), site B (to test), buffer "
                            "meters, and a representative [lon, lat]. Geometries "
                            "must remain WKT. Do not invent coordinates."
                        ),
                    },
                    {"role": "user", "content": request},
                ]
            )
        return {
            "site_a_wkt": parsed.site_a_wkt,
            "site_b_wkt": parsed.site_b_wkt,
            "buffer_meters": float(parsed.buffer_meters),
            "representative_lonlat": list(parsed.representative_lonlat),
            "errors": [],
            "stage": "interpreted",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"interpret failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


def plan_node(state: GISWorkflowState) -> Dict[str, Any]:
    """Build a deterministic CRS-safe GIS MCP plan (stored in state)."""
    if state.get("errors"):
        return {"stage": "error"}
    plan = [
        "is_valid(site_a)",
        "is_valid(site_b)",
        "get_utm_crs",
        "project_geometry(site_a)",
        "project_geometry(site_b)",
        "buffer(site_a_utm)",
        "intersection(buffer, site_b_utm)",
        "calculate_geodetic_distance(site_a, site_b)",
    ]
    return {"plan_steps": plan, "tool_results": {}, "stage": "planned"}


async def execute_tools_node(state: GISWorkflowState) -> Dict[str, Any]:
    """Execute the planned GIS MCP tools in order; record results in state."""
    if state.get("errors"):
        return {"stage": "error"}

    try:
        tools = await load_mcp_tools()
        results: Dict[str, Any] = {}

        a = state["site_a_wkt"]
        b = state["site_b_wkt"]
        buffer_m = float(state["buffer_meters"])
        lonlat = state["representative_lonlat"]

        results["is_valid_a"] = await call_tool(tools, "is_valid", {"geometry": a})
        results["is_valid_b"] = await call_tool(tools, "is_valid", {"geometry": b})
        if not results["is_valid_a"].get("is_valid", True):
            raise ValueError(f"site_a invalid: {results['is_valid_a']}")
        if not results["is_valid_b"].get("is_valid", True):
            raise ValueError(f"site_b invalid: {results['is_valid_b']}")

        utm = await call_tool(tools, "get_utm_crs", {"coordinates": lonlat})
        utm_crs = utm.get("crs")
        if not utm_crs:
            raise ValueError(f"get_utm_crs returned no crs: {utm}")
        results["get_utm_crs"] = utm

        proj_a = await call_tool(
            tools,
            "project_geometry",
            {"geometry": a, "source_crs": "EPSG:4326", "target_crs": utm_crs},
        )
        proj_b = await call_tool(
            tools,
            "project_geometry",
            {"geometry": b, "source_crs": "EPSG:4326", "target_crs": utm_crs},
        )
        results["project_a"] = proj_a
        results["project_b"] = proj_b
        a_utm = proj_a.get("geometry")
        b_utm = proj_b.get("geometry")
        if not a_utm or not b_utm:
            raise ValueError("projection missing geometry")

        buffered = await call_tool(
            tools, "buffer", {"geometry": a_utm, "distance": buffer_m}
        )
        results["buffer"] = buffered
        buffer_geom = buffered.get("geometry")
        if not buffer_geom:
            raise ValueError("buffer missing geometry")

        inter = await call_tool(
            tools,
            "intersection",
            {"geometry1": buffer_geom, "geometry2": b_utm},
        )
        results["intersection"] = inter

        # Geodetic distance: prefer point coords; otherwise centroids.
        if a.upper().startswith("POINT") and b.upper().startswith("POINT"):
            p1, p2 = _wkt_point_to_lonlat(a), _wkt_point_to_lonlat(b)
        else:
            ca = await call_tool(tools, "get_centroid", {"geometry": a})
            cb = await call_tool(tools, "get_centroid", {"geometry": b})
            results["centroid_a"] = ca
            results["centroid_b"] = cb
            p1 = _wkt_point_to_lonlat(str(ca.get("geometry")))
            p2 = _wkt_point_to_lonlat(str(cb.get("geometry")))

        dist = await call_tool(
            tools,
            "calculate_geodetic_distance",
            {"point1": p1, "point2": p2},
        )
        results["geodetic_distance"] = dist

        return {
            "tool_results": results,
            "errors": [],
            "stage": "executed",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": list(state.get("errors") or [])
            + [f"execute_tools failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


def validate_node(state: GISWorkflowState) -> Dict[str, Any]:
    """Validate tool outputs before composing the final answer."""
    if state.get("errors"):
        return {"validation_ok": False, "stage": "error"}

    notes: List[str] = []
    ok = True
    results = state.get("tool_results") or {}

    utm = (results.get("get_utm_crs") or {}).get("crs")
    if not utm:
        ok = False
        notes.append("Missing UTM CRS in tool results.")
    else:
        notes.append(f"UTM CRS: {utm}")

    inter_wkt = (results.get("intersection") or {}).get("geometry")
    intersects = not _is_empty_wkt(inter_wkt)
    notes.append(f"School intersects transit buffer: {intersects}")

    distance = (results.get("geodetic_distance") or {}).get("distance")
    buffer_m = float(state.get("buffer_meters") or 0)
    if distance is None:
        ok = False
        notes.append("Missing geodetic distance.")
    else:
        notes.append(f"Geodetic distance (m): {distance}")
        # Soft consistency check: if distance << buffer, expect intersection for points.
        if float(distance) < buffer_m * 0.95 and not intersects:
            ok = False
            notes.append(
                "Inconsistent: distance is less than buffer but intersection is empty."
            )
        if float(distance) > buffer_m * 1.05 and intersects:
            # Possible for non-point footprints; flag but do not hard-fail points case.
            notes.append(
                "Note: distance exceeds buffer while intersection is non-empty "
                "(check geometry types)."
            )

    return {
        "validation_ok": ok,
        "validation_notes": notes,
        "stage": "validated" if ok else "error",
        "errors": []
        if ok
        else list(state.get("errors") or []) + ["validation failed: " + "; ".join(notes)],
    }


def respond_node(state: GISWorkflowState) -> Dict[str, Any]:
    """Compose the final response from validated state (template; optional LLM polish)."""
    results = state.get("tool_results") or {}
    notes = state.get("validation_notes") or []
    inter_wkt = (results.get("intersection") or {}).get("geometry")
    intersects = not _is_empty_wkt(inter_wkt)
    distance = (results.get("geodetic_distance") or {}).get("distance")
    utm = (results.get("get_utm_crs") or {}).get("crs")
    buffer_m = state.get("buffer_meters")

    answer = (
        "GIS MCP stateful workflow result\n"
        f"- Buffer distance: {buffer_m} m\n"
        f"- UTM CRS: {utm}\n"
        f"- Site B intersects buffered site A: {intersects}\n"
        f"- Geodetic distance: {distance} m\n"
        f"- Validation: {'PASS' if state.get('validation_ok') else 'FAIL'}\n"
        f"- Notes: {'; '.join(notes)}\n"
        f"- Plan executed: {', '.join(state.get('plan_steps') or [])}\n"
    )

    # Optional LLM narrative when a key is present and not skipped.
    skip_llm = os.getenv("SKIP_LLM_RESPOND", "").lower() in {"1", "true", "yes"}
    if resolve_api_key() and not skip_llm:
        try:
            llm = build_llm()
            polished = llm.invoke(
                [
                    {
                        "role": "system",
                        "content": (
                            "Rewrite the GIS facts clearly for a planner. "
                            "Do not change numbers or invent new measurements."
                        ),
                    },
                    {"role": "user", "content": answer},
                ]
            )
            content = polished.content
            if isinstance(content, str) and content.strip():
                answer = content.strip()
        except Exception:
            pass

    return {"final_answer": answer, "stage": "done"}


def handle_error_node(state: GISWorkflowState) -> Dict[str, Any]:
    errs = state.get("errors") or ["Unknown workflow error"]
    answer = (
        "GIS workflow failed before a trusted answer could be produced.\n"
        "Errors:\n- " + "\n- ".join(errs) + "\n"
        "No invented coordinates or distances were returned."
    )
    return {"final_answer": answer, "validation_ok": False, "stage": "failed"}


def route_after_interpret(state: GISWorkflowState) -> Literal["plan", "handle_error"]:
    return "handle_error" if state.get("errors") else "plan"


def route_after_execute(state: GISWorkflowState) -> Literal["validate", "handle_error"]:
    return "handle_error" if state.get("errors") else "validate"


def route_after_validate(state: GISWorkflowState) -> Literal["respond", "handle_error"]:
    if state.get("errors") or not state.get("validation_ok", False):
        return "handle_error"
    return "respond"


def build_graph():
    graph = StateGraph(GISWorkflowState)
    graph.add_node("interpret", interpret_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute_tools", execute_tools_node)
    graph.add_node("validate", validate_node)
    graph.add_node("respond", respond_node)
    graph.add_node("handle_error", handle_error_node)

    graph.add_edge(START, "interpret")
    graph.add_conditional_edges("interpret", route_after_interpret)
    graph.add_edge("plan", "execute_tools")
    graph.add_conditional_edges("execute_tools", route_after_execute)
    graph.add_conditional_edges("validate", route_after_validate)
    graph.add_edge("respond", END)
    graph.add_edge("handle_error", END)
    return graph.compile()


async def run_workflow(user_request: str) -> GISWorkflowState:
    app = build_graph()
    result = await app.ainvoke(
        {
            "user_request": user_request,
            "tool_results": {},
            "validation_notes": [],
            "errors": [],
            "plan_steps": [],
        }
    )
    return result  # type: ignore[return-value]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LangGraph GIS MCP stateful workflow")
    p.add_argument("--demo", action="store_true", help="Run transit-stop coverage demo")
    p.add_argument(
        "--request",
        type=str,
        default="",
        help="Custom user request (otherwise interactive prompt)",
    )
    return p.parse_args()


async def async_main() -> int:
    args = parse_args()
    # Demo/verify path does not require LLM for interpret/respond.
    if args.demo:
        os.environ.setdefault("SKIP_LLM_INTERPRET", "1")
        os.environ.setdefault("SKIP_LLM_RESPOND", "1")
        request = DEMO_REQUEST
    elif args.request:
        request = args.request
    else:
        print("Enter a GIS coverage request (or run with --demo). Empty line exits.")
        request = input("You: ").strip()
        if not request:
            return 0

    print(f"MCP URL: {MCP_SERVER_URL} ({MCP_TRANSPORT})")
    result = await run_workflow(request)
    print("\n--- stage:", result.get("stage"))
    print("--- plan:", result.get("plan_steps"))
    print("--- validation_ok:", result.get("validation_ok"))
    print("--- notes:", result.get("validation_notes"))
    if result.get("errors"):
        print("--- errors:", result.get("errors"))
    print("\nFinal answer:\n")
    print(result.get("final_answer") or "(empty)")
    return 0 if result.get("stage") == "done" and result.get("validation_ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
