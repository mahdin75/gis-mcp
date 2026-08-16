"""
LangGraph + GIS MCP: multi-step playground site suitability.

Graph:
  interpret → plan → inspect_layers → clip_downtown → exclude_flood
  → build_park_buffer → select_suitable → export_and_map → analyze
  → validate → respond
                 ↘ handle_error

GIS math runs on GIS MCP Server. LangGraph stores intermediate paths
and blocks a final answer until validation passes.

OpenRouter is used the same way as the LangChain GIS MCP tutorial:
  ChatOpenAI(..., base_url="https://openrouter.ai/api/v1")
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

load_dotenv()

os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = os.getenv("GIS_AGENT_MODEL", "deepseek/deepseek-chat-v3.1")
MCP_SERVER_URL = os.getenv("GIS_MCP_URL", "http://127.0.0.1:9010/mcp")
MCP_TRANSPORT = os.getenv("GIS_MCP_CLIENT_TRANSPORT", "streamable_http")

EXAMPLE_PROMPT = (
    "We need a new playground in downtown Riverside. "
    "Which vacant lots are inside downtown, outside the flood zone, "
    "and within 300 meters of a park? Rank them by size and make a map."
)

DEMO_REQUEST = EXAMPLE_PROMPT

ALLOWED_TOOL_NAMES = frozenset(
    {
        "read_file_gpd",
        "clip_vector",
        "overlay_gpd",
        "dissolve_gpd",
        "get_utm_crs",
        "project_geometry",
        "buffer",
        "save_results",
        "sjoin_gpd",
        "write_file_gpd",
        "create_map",
        "create_web_map",
        "is_valid",
    }
)


class GISSuitabilityState(TypedDict, total=False):
    user_request: str
    lots_path: str
    downtown_path: str
    flood_path: str
    parks_path: str
    buffer_meters: float
    representative_lonlat: List[float]
    plan_steps: List[str]
    layer_stats: Dict[str, Any]
    intermediate_paths: Dict[str, str]
    tool_results: Dict[str, Any]
    ranked_sites: List[Dict[str, Any]]
    map_png: str
    map_html: str
    validation_ok: bool
    validation_notes: List[str]
    errors: List[str]
    final_answer: str
    stage: str


def skip_llm() -> bool:
    return os.getenv("SKIP_LLM", "").lower() in {"1", "true", "yes"}


def init_llm() -> ChatOpenAI:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY (same OpenRouter setup as the LangChain GIS MCP tutorial)."
        )
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0.2,
    )


def _payload(raw: Any) -> Dict[str, Any]:
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


def _tool_error(payload: Dict[str, Any], name: str) -> Optional[str]:
    status = str(payload.get("status", "")).lower()
    if status == "error":
        return f"{name}: {payload.get('message', payload)}"
    return None


async def load_mcp_tools() -> Dict[str, Any]:
    client = MultiServerMCPClient(
        {"gis": {"transport": MCP_TRANSPORT, "url": MCP_SERVER_URL}}
    )
    tools = await client.get_tools()
    filtered = {
        t.name: t for t in tools if getattr(t, "name", None) in ALLOWED_TOOL_NAMES
    }
    missing = ALLOWED_TOOL_NAMES - set(filtered)
    if missing:
        raise RuntimeError(
            "Missing GIS MCP tools: "
            + ", ".join(sorted(missing))
            + ". Start gis-mcp in HTTP mode. For maps, install gis-mcp[visualize] "
            "and matplotlib in the server environment."
        )
    return filtered


async def call_tool(
    tools: Dict[str, Any], name: str, args: Dict[str, Any]
) -> Dict[str, Any]:
    payload = _payload(await tools[name].ainvoke(args))
    err = _tool_error(payload, name)
    if err:
        raise RuntimeError(err)
    return payload


def _abs_data(filename: str) -> str:
    path = (DATA_DIR / filename).resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run: python prepare_data.py"
        )
    return str(path)


def _meters_from_prompt(text: str) -> float:
    """Read a walking-distance in meters from the user's question."""
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*-?\s*(?:m|meters?|metres?)\b",
        text,
        re.IGNORECASE,
    )
    if match:
        return float(match.group(1))
    return 300.0


def interpret_node(state: GISSuitabilityState) -> Dict[str, Any]:
    """Keep the user prompt in state and pull GIS thresholds from it."""
    try:
        request = (state.get("user_request") or "").strip()
        if not request:
            raise ValueError("Empty prompt. Type a planning question at the You: prompt.")
        return {
            "user_request": request,
            "lots_path": _abs_data("vacant_lots.geojson"),
            "downtown_path": _abs_data("downtown.geojson"),
            "flood_path": _abs_data("flood_zone.geojson"),
            "parks_path": _abs_data("parks.geojson"),
            "buffer_meters": _meters_from_prompt(request),
            "representative_lonlat": [-74.037, 40.742],
            "errors": [],
            "stage": "interpreted",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"interpret failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


def plan_node(state: GISSuitabilityState) -> Dict[str, Any]:
    """Record the CRS-safe GIS MCP sequence (audit trail)."""
    if state.get("errors"):
        return {"stage": "error"}
    return {
        "plan_steps": [
            "read_file_gpd (lots, downtown, flood, parks)",
            "clip_vector lots ∩ downtown",
            "overlay_gpd difference vs flood",
            "dissolve_gpd parks",
            "get_utm_crs",
            "project_geometry parks → UTM",
            "buffer (meters)",
            "project_geometry buffer → EPSG:4326",
            "save_results geojson",
            "sjoin_gpd lots ⋈ park buffer",
            "write_file_gpd",
            "create_map",
            "create_web_map",
        ],
        "tool_results": {},
        "layer_stats": {},
        "intermediate_paths": {},
        "stage": "planned",
    }


async def inspect_layers_node(state: GISSuitabilityState) -> Dict[str, Any]:
    if state.get("errors"):
        return {"stage": "error"}
    try:
        tools = await load_mcp_tools()
        stats: Dict[str, Any] = {}
        results: Dict[str, Any] = dict(state.get("tool_results") or {})
        for key, path in (
            ("lots", state["lots_path"]),
            ("downtown", state["downtown_path"]),
            ("flood", state["flood_path"]),
            ("parks", state["parks_path"]),
        ):
            payload = await call_tool(tools, "read_file_gpd", {"file_path": path})
            results[f"read_{key}"] = payload
            stats[key] = {
                "num_rows": payload.get("num_rows"),
                "crs": payload.get("crs"),
                "columns": payload.get("columns"),
            }
        return {
            "layer_stats": stats,
            "tool_results": results,
            "errors": [],
            "stage": "inspected",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"inspect_layers failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


async def clip_downtown_node(state: GISSuitabilityState) -> Dict[str, Any]:
    if state.get("errors"):
        return {"stage": "error"}
    try:
        tools = await load_mcp_tools()
        payload = await call_tool(
            tools,
            "clip_vector",
            {
                "gdf_path": state["lots_path"],
                "clip_path": state["downtown_path"],
                "output_path": "lots_downtown.geojson",
            },
        )
        path = payload.get("output_path")
        if not path:
            raise RuntimeError("clip_vector did not return output_path")
        results = dict(state.get("tool_results") or {})
        paths = dict(state.get("intermediate_paths") or {})
        results["clip_downtown"] = payload
        paths["lots_downtown"] = path
        return {
            "tool_results": results,
            "intermediate_paths": paths,
            "errors": [],
            "stage": "clipped",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"clip_downtown failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


async def exclude_flood_node(state: GISSuitabilityState) -> Dict[str, Any]:
    if state.get("errors"):
        return {"stage": "error"}
    try:
        tools = await load_mcp_tools()
        clipped = (state.get("intermediate_paths") or {})["lots_downtown"]
        payload = await call_tool(
            tools,
            "overlay_gpd",
            {
                "gdf1_path": clipped,
                "gdf2_path": state["flood_path"],
                "how": "difference",
                "output_path": "lots_no_flood.geojson",
            },
        )
        path = payload.get("output_path")
        if not path:
            raise RuntimeError("overlay_gpd did not return output_path")
        results = dict(state.get("tool_results") or {})
        paths = dict(state.get("intermediate_paths") or {})
        results["exclude_flood"] = payload
        paths["lots_no_flood"] = path
        return {
            "tool_results": results,
            "intermediate_paths": paths,
            "errors": [],
            "stage": "flood_erased",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"exclude_flood failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


async def build_park_buffer_node(state: GISSuitabilityState) -> Dict[str, Any]:
    """File dissolve → WKT → UTM → buffer meters → EPSG:4326 → GeoJSON."""
    if state.get("errors"):
        return {"stage": "error"}
    try:
        tools = await load_mcp_tools()
        dissolved = await call_tool(
            tools,
            "dissolve_gpd",
            {
                "gdf_path": state["parks_path"],
                "output_path": "parks_dissolved.geojson",
            },
        )
        preview = dissolved.get("preview") or []
        if not preview or not preview[0].get("geometry"):
            raise RuntimeError("dissolve_gpd preview missing geometry WKT")
        park_wkt = preview[0]["geometry"]

        valid = await call_tool(tools, "is_valid", {"geometry": park_wkt})
        if valid.get("is_valid") is False:
            raise RuntimeError(f"dissolved parks invalid: {valid}")

        utm = await call_tool(
            tools,
            "get_utm_crs",
            {"coordinates": state["representative_lonlat"]},
        )
        utm_crs = utm.get("crs")
        if not utm_crs:
            raise RuntimeError(f"get_utm_crs returned no crs: {utm}")

        park_utm = await call_tool(
            tools,
            "project_geometry",
            {
                "geometry": park_wkt,
                "source_crs": "EPSG:4326",
                "target_crs": utm_crs,
            },
        )
        buffered = await call_tool(
            tools,
            "buffer",
            {
                "geometry": park_utm["geometry"],
                "distance": float(state["buffer_meters"]),
            },
        )
        buffer_4326 = await call_tool(
            tools,
            "project_geometry",
            {
                "geometry": buffered["geometry"],
                "source_crs": utm_crs,
                "target_crs": "EPSG:4326",
            },
        )
        meters = float(state["buffer_meters"])
        saved = await call_tool(
            tools,
            "save_results",
            {
                "data": {"geometry": buffer_4326["geometry"]},
                "filename": f"park_access_{int(meters)}m",
                "formats": ["geojson"],
                "folder": "outputs",
            },
        )
        saved_files = saved.get("saved_files") or {}
        buffer_path = saved_files.get("geojson")
        if not buffer_path:
            raise RuntimeError(f"save_results missing geojson path: {saved}")

        results = dict(state.get("tool_results") or {})
        paths = dict(state.get("intermediate_paths") or {})
        results.update(
            {
                "dissolve_parks": dissolved,
                "is_valid_parks": valid,
                "get_utm_crs": utm,
                "project_parks_utm": park_utm,
                "buffer_parks": buffered,
                "project_buffer_4326": buffer_4326,
                "save_park_buffer": saved,
            }
        )
        paths["parks_dissolved"] = dissolved.get("output_path") or ""
        paths["park_buffer"] = buffer_path
        return {
            "tool_results": results,
            "intermediate_paths": paths,
            "errors": [],
            "stage": "buffered",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"build_park_buffer failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


async def select_suitable_node(state: GISSuitabilityState) -> Dict[str, Any]:
    if state.get("errors"):
        return {"stage": "error"}
    try:
        tools = await load_mcp_tools()
        paths = state.get("intermediate_paths") or {}
        payload = await call_tool(
            tools,
            "sjoin_gpd",
            {
                "left_path": paths["lots_no_flood"],
                "right_path": paths["park_buffer"],
                "how": "inner",
                "predicate": "intersects",
                "output_path": "suitable_lots.geojson",
            },
        )
        path = payload.get("output_path")
        if not path:
            raise RuntimeError("sjoin_gpd did not return output_path")
        results = dict(state.get("tool_results") or {})
        out_paths = dict(paths)
        results["sjoin_suitable"] = payload
        out_paths["suitable_lots"] = path
        return {
            "tool_results": results,
            "intermediate_paths": out_paths,
            "errors": [],
            "stage": "selected",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"select_suitable failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


def _map_layers(state: GISSuitabilityState) -> List[Dict[str, Any]]:
    paths = state.get("intermediate_paths") or {}
    meters = int(float(state.get("buffer_meters") or 300))
    return [
        {
            "data": state["downtown_path"],
            "style": {"label": "Downtown", "color": "gray", "alpha": 0.25},
        },
        {
            "data": state["flood_path"],
            "style": {"label": "Flood zone", "color": "royalblue", "alpha": 0.4},
        },
        {
            "data": state["parks_path"],
            "style": {"label": "Parks", "color": "green", "alpha": 0.55},
        },
        {
            "data": paths["park_buffer"],
            "style": {
                "label": f"{meters} m park access",
                "color": "lime",
                "alpha": 0.25,
            },
        },
        {
            "data": paths["suitable_lots"],
            "style": {"label": "Suitable lots", "color": "red", "alpha": 0.85},
        },
    ]


async def export_and_map_node(state: GISSuitabilityState) -> Dict[str, Any]:
    if state.get("errors"):
        return {"stage": "error"}
    try:
        tools = await load_mcp_tools()
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        suitable = (state.get("intermediate_paths") or {})["suitable_lots"]
        exported = await call_tool(
            tools,
            "write_file_gpd",
            {
                "gdf_path": suitable,
                "output_path": "suitable_lots_export.geojson",
                "driver": "GeoJSON",
            },
        )
        layers = _map_layers(state)
        meters = float(state.get("buffer_meters") or 300)
        map_title = (
            f"Riverside playground sites — downtown, outside flood, "
            f"within {int(meters)} m of a park"
        )
        png = await call_tool(
            tools,
            "create_map",
            {
                "layers": layers,
                "filename": "playground_suitability",
                "filetype": "png",
                "title": map_title,
                "output_dir": str(OUTPUTS_DIR),
            },
        )
        html = await call_tool(
            tools,
            "create_web_map",
            {
                "layers": layers,
                "filename": "playground_suitability.html",
                "title": map_title,
                "basemap": "OpenStreetMap",
                "output_dir": str(OUTPUTS_DIR),
            },
        )
        results = dict(state.get("tool_results") or {})
        paths = dict(state.get("intermediate_paths") or {})
        results["write_export"] = exported
        results["create_map"] = png
        results["create_web_map"] = html
        paths["suitable_export"] = exported.get("output_path") or ""
        return {
            "tool_results": results,
            "intermediate_paths": paths,
            "map_png": png.get("output_path") or "",
            "map_html": html.get("output_path") or "",
            "errors": [],
            "stage": "mapped",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"export_and_map failed: {type(exc).__name__}: {exc}"],
            "stage": "error",
        }


def analyze_node(state: GISSuitabilityState) -> Dict[str, Any]:
    """Rank remaining lots by the authored area_sqm attribute."""
    if state.get("errors"):
        return {"stage": "error"}
    preview = (
        (state.get("tool_results") or {}).get("sjoin_suitable") or {}
    ).get("preview") or []
    ranked: List[Dict[str, Any]] = []
    for row in preview:
        ranked.append(
            {
                "name": row.get("name") or row.get("NAME"),
                "lot_id": row.get("lot_id"),
                "area_sqm": row.get("area_sqm"),
            }
        )
    ranked.sort(key=lambda r: float(r.get("area_sqm") or 0), reverse=True)
    return {"ranked_sites": ranked, "stage": "analyzed"}


def validate_node(state: GISSuitabilityState) -> Dict[str, Any]:
    if state.get("errors"):
        return {"validation_ok": False, "stage": "error"}
    notes: List[str] = []
    ok = True
    stats = state.get("layer_stats") or {}
    results = state.get("tool_results") or {}
    paths = state.get("intermediate_paths") or {}

    if int((stats.get("lots") or {}).get("num_rows") or 0) < 1:
        ok = False
        notes.append("Lots layer is empty.")
    else:
        notes.append(f"Input lots: {stats['lots']['num_rows']}")

    clip_n = (results.get("clip_downtown") or {}).get("num_features")
    if not clip_n:
        ok = False
        notes.append("Clip to downtown returned no features.")
    else:
        notes.append(f"Lots after downtown clip: {clip_n}")

    flood_n = (results.get("exclude_flood") or {}).get("num_features")
    if not flood_n:
        ok = False
        notes.append("Flood difference returned no features.")
    else:
        notes.append(f"Lots after flood erase: {flood_n}")

    utm = (results.get("get_utm_crs") or {}).get("crs")
    if not utm:
        ok = False
        notes.append("Missing UTM CRS — buffer may not be in meters.")
    else:
        notes.append("UTM CRS present for metric buffer.")

    if not paths.get("park_buffer"):
        ok = False
        notes.append("Park access GeoJSON was not saved.")
    join_n = (results.get("sjoin_suitable") or {}).get("num_features")
    if not join_n:
        ok = False
        notes.append("No lots intersect the 300 m park-access zone.")
    else:
        notes.append(f"Suitable lots: {join_n}")

    if not state.get("map_png") or not state.get("map_html"):
        ok = False
        notes.append("Map outputs missing.")
    else:
        notes.append("Static PNG and web map written.")

    if not state.get("ranked_sites"):
        ok = False
        notes.append("Ranking produced no sites.")

    return {
        "validation_ok": ok,
        "validation_notes": notes,
        "errors": [] if ok else list(state.get("errors") or []) + notes,
        "stage": "validated" if ok else "error",
    }


def _facts_block(state: GISSuitabilityState) -> str:
    ranked = state.get("ranked_sites") or []
    lines = [
        f"USER QUESTION:\n{(state.get('user_request') or '').strip()}",
        "",
        "GIS RESULTS (from GIS MCP tools, not from the LLM):",
        f"- Buffer: {state.get('buffer_meters')} m (after UTM projection)",
        f"- Suitable lots: {len(ranked)}",
    ]
    for i, row in enumerate(ranked, start=1):
        lines.append(
            f"  {i}. {row.get('name')} ({row.get('lot_id')}) area_sqm={row.get('area_sqm')}"
        )
    lines.append(f"- Export: {(state.get('intermediate_paths') or {}).get('suitable_export')}")
    lines.append(f"- PNG map: {state.get('map_png')}")
    lines.append(f"- HTML map: {state.get('map_html')}")
    lines.append("- Map legend: gray=downtown, blue=flood, green=parks, lime=park access, red=suitable lots")
    lines.append("- Validation: " + "; ".join(state.get("validation_notes") or []))
    return "\n".join(lines)


def _answer_without_llm(state: GISSuitabilityState) -> str:
    ranked = state.get("ranked_sites") or []
    question = (state.get("user_request") or "").strip()
    meters = state.get("buffer_meters")
    html = state.get("map_html") or ""
    png = state.get("map_png") or ""
    lines = [
        f'You asked: "{question}"',
        "",
        f"Using GIS MCP, {len(ranked)} vacant lot(s) are inside downtown, "
        f"outside the flood zone, and within {meters} m of a park.",
        "Ranked by area (largest first):",
    ]
    for i, row in enumerate(ranked, start=1):
        lines.append(
            f"  {i}. {row.get('name')} ({row.get('lot_id')}) - {row.get('area_sqm')} sq m"
        )
    lines.extend(
        [
            "",
            "Open the interactive map in a browser (this is the visual result):",
            html,
            "",
            "Static PNG:",
            png,
            "",
            "On the map: gray = downtown, blue = flood, green = parks, "
            "lime = park-access buffer, red = lots that passed. "
            "Toggle layers to see why other lots failed.",
        ]
    )
    return "\n".join(lines)


def respond_node(state: GISSuitabilityState) -> Dict[str, Any]:
    """Answer the original user prompt using GIS facts + map paths."""
    facts = _facts_block(state)
    answer = _answer_without_llm(state)
    if OPENROUTER_API_KEY and not skip_llm():
        try:
            llm = init_llm()
            polished = llm.invoke(
                [
                    {
                        "role": "system",
                        "content": (
                            "You answer the user's planning question. "
                            "Use only the GIS facts. Restate their question in one line, "
                            "then name the ranked lots, then tell them to open the HTML map. "
                            "Describe the legend (gray downtown, blue flood, green parks, "
                            "lime buffer, red suitable lots). "
                            "Do not invent lot names, counts, distances, or file paths."
                        ),
                    },
                    {"role": "user", "content": facts},
                ]
            )
            content = polished.content
            if isinstance(content, str) and content.strip():
                answer = content.strip()
                html = state.get("map_html") or ""
                if html and html not in answer:
                    answer = answer.rstrip() + f"\n\nOpen the map: {html}"
        except Exception:
            answer = _answer_without_llm(state)
    return {"final_answer": answer, "stage": "done"}


def handle_error_node(state: GISSuitabilityState) -> Dict[str, Any]:
    errs = state.get("errors") or ["Unknown workflow error"]
    answer = (
        "GIS workflow failed before a trusted answer could be produced.\n"
        "Errors:\n- "
        + "\n- ".join(errs)
        + "\nNo invented coordinates or rankings were returned."
    )
    return {"final_answer": answer, "validation_ok": False, "stage": "failed"}


def _route(next_node: str):
    def router(
        state: GISSuitabilityState,
    ) -> Literal[
        "plan",
        "inspect_layers",
        "clip_downtown",
        "exclude_flood",
        "build_park_buffer",
        "select_suitable",
        "export_and_map",
        "analyze",
        "validate",
        "respond",
        "handle_error",
    ]:
        return "handle_error" if state.get("errors") else next_node  # type: ignore[return-value]

    return router


def build_graph():
    g = StateGraph(GISSuitabilityState)
    g.add_node("interpret", interpret_node)
    g.add_node("plan", plan_node)
    g.add_node("inspect_layers", inspect_layers_node)
    g.add_node("clip_downtown", clip_downtown_node)
    g.add_node("exclude_flood", exclude_flood_node)
    g.add_node("build_park_buffer", build_park_buffer_node)
    g.add_node("select_suitable", select_suitable_node)
    g.add_node("export_and_map", export_and_map_node)
    g.add_node("analyze", analyze_node)
    g.add_node("validate", validate_node)
    g.add_node("respond", respond_node)
    g.add_node("handle_error", handle_error_node)

    g.add_edge(START, "interpret")
    g.add_conditional_edges("interpret", _route("plan"))
    g.add_edge("plan", "inspect_layers")
    g.add_conditional_edges("inspect_layers", _route("clip_downtown"))
    g.add_conditional_edges("clip_downtown", _route("exclude_flood"))
    g.add_conditional_edges("exclude_flood", _route("build_park_buffer"))
    g.add_conditional_edges("build_park_buffer", _route("select_suitable"))
    g.add_conditional_edges("select_suitable", _route("export_and_map"))
    g.add_conditional_edges("export_and_map", _route("analyze"))
    g.add_edge("analyze", "validate")
    g.add_conditional_edges(
        "validate",
        lambda s: "handle_error" if not s.get("validation_ok") else "respond",
        ["handle_error", "respond"],
    )
    g.add_edge("respond", END)
    g.add_edge("handle_error", END)
    return g.compile()


async def run_workflow(user_request: str) -> GISSuitabilityState:
    app = build_graph()
    result = await app.ainvoke(
        {
            "user_request": user_request,
            "tool_results": {},
            "intermediate_paths": {},
            "layer_stats": {},
            "validation_notes": [],
            "errors": [],
            "plan_steps": [],
            "ranked_sites": [],
        }
    )
    return result  # type: ignore[return-value]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LangGraph GIS MCP site suitability")
    p.add_argument("--demo", action="store_true", help="Run the example playground prompt once")
    p.add_argument("--request", type=str, default="", help="One custom prompt, then exit")
    return p.parse_args()


def _print_result(result: GISSuitabilityState) -> None:
    print("\nAgent:\n")
    print(result.get("final_answer") or "(empty)")
    html = result.get("map_html") or ""
    if html:
        print(f"\nVisual result (open in a browser):\n  {html}\n")


async def run_interactive_session() -> int:
    print("GIS LangGraph agent ready. Type a planning question.")
    print("Type 'exit', 'quit', or 'q' to stop.\n")
    print(f"Example:\n  {EXAMPLE_PROMPT}\n")
    print(f"MCP URL: {MCP_SERVER_URL} ({MCP_TRANSPORT})")
    print(f"OpenRouter: {'yes' if OPENROUTER_API_KEY else 'no (template answer)'}\n")
    last_ok = 0
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
        result = await run_workflow(query)
        _print_result(result)
        last_ok = (
            0 if result.get("stage") == "done" and result.get("validation_ok") else 1
        )
    return last_ok


async def async_main() -> int:
    args = parse_args()
    if args.demo:
        request = DEMO_REQUEST
    elif args.request:
        request = args.request
    else:
        return await run_interactive_session()

    print(f"MCP URL: {MCP_SERVER_URL} ({MCP_TRANSPORT})")
    print(f"OpenRouter: {'yes' if OPENROUTER_API_KEY else 'no (template answer)'}")
    print(f"You: {request}\n")
    result = await run_workflow(request)
    _print_result(result)
    return 0 if result.get("stage") == "done" and result.get("validation_ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
