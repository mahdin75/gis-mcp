"""
Verify GIS MCP HTTP connectivity and the park-buffer workflow without an LLM.

Calls the same tools the LangChain tutorial relies on, via MultiServerMCPClient.
Requires a running GIS MCP server (default http://localhost:9010/mcp).

Usage:
  python verify_tools.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")

MCP_SERVER_URL = os.getenv("GIS_MCP_URL", "http://127.0.0.1:9010/mcp")
MCP_TRANSPORT = os.getenv("GIS_MCP_CLIENT_TRANSPORT", "streamable_http")

PARK_WGS84 = (
    "POLYGON((-73.9730 40.7720, -73.9710 40.7720, "
    "-73.9710 40.7735, -73.9730 40.7735, -73.9730 40.7720))"
)
BUILDING_WGS84 = (
    "POLYGON((-73.9705 40.7724, -73.9698 40.7724, "
    "-73.9698 40.7729, -73.9705 40.7729, -73.9705 40.7724))"
)
PARK_POINT = [-73.9720, 40.77275]
BUILDING_POINT = [-73.97015, 40.77265]


def _parse_tool_payload(raw: Any) -> Dict[str, Any]:
    """Normalize LangChain tool return values to a dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
    if isinstance(raw, list):
        # Some adapters wrap content blocks
        for item in raw:
            if isinstance(item, dict) and "text" in item:
                try:
                    return json.loads(item["text"])
                except (json.JSONDecodeError, TypeError):
                    continue
        return {"raw": raw}
    return {"raw": raw}


async def call_tool(tools_by_name: Dict[str, Any], name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name not in tools_by_name:
        raise RuntimeError(f"Tool not available from MCP server: {name}")
    raw = await tools_by_name[name].ainvoke(args)
    payload = _parse_tool_payload(raw)
    print(f"OK  {name}: {json.dumps(payload, default=str)[:240]}")
    return payload


async def main() -> int:
    print(f"Connecting to {MCP_SERVER_URL} (transport={MCP_TRANSPORT})")
    client = MultiServerMCPClient(
        {
            "gis": {
                "transport": MCP_TRANSPORT,
                "url": MCP_SERVER_URL,
            }
        }
    )
    try:
        tools = await client.get_tools()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL get_tools: {type(exc).__name__}: {exc}")
        return 1

    tools_by_name = {t.name: t for t in tools}
    print(f"Discovered {len(tools)} tools")

    required = [
        "get_utm_crs",
        "project_geometry",
        "buffer",
        "intersection",
        "get_centroid",
        "calculate_geodetic_distance",
        "get_area",
    ]
    missing = [n for n in required if n not in tools_by_name]
    if missing:
        print(f"FAIL missing tools: {missing}")
        return 1

    utm = await call_tool(tools_by_name, "get_utm_crs", {"coordinates": PARK_POINT})
    utm_crs = utm.get("crs")
    if not utm_crs:
        print(f"FAIL get_utm_crs did not return crs: {utm}")
        return 1

    park_utm = await call_tool(
        tools_by_name,
        "project_geometry",
        {"geometry": PARK_WGS84, "source_crs": "EPSG:4326", "target_crs": utm_crs},
    )
    building_utm = await call_tool(
        tools_by_name,
        "project_geometry",
        {"geometry": BUILDING_WGS84, "source_crs": "EPSG:4326", "target_crs": utm_crs},
    )
    park_geom = park_utm.get("geometry")
    building_geom = building_utm.get("geometry")
    if not park_geom or not building_geom:
        print("FAIL projection missing geometry")
        return 1

    buffered = await call_tool(
        tools_by_name,
        "buffer",
        {"geometry": park_geom, "distance": 100.0},
    )
    buffer_geom = buffered.get("geometry")
    if not buffer_geom:
        print("FAIL buffer missing geometry")
        return 1

    inter = await call_tool(
        tools_by_name,
        "intersection",
        {"geometry1": buffer_geom, "geometry2": building_geom},
    )
    inter_geom = (inter.get("geometry") or "").strip().upper()
    intersects = inter_geom not in {"", "GEOMETRYCOLLECTION EMPTY", "POLYGON EMPTY", "POINT EMPTY"}
    # EMPTY keyword covers most Shapely empty WKTs
    if "EMPTY" in inter_geom:
        intersects = False

    area = await call_tool(tools_by_name, "get_area", {"geometry": buffer_geom})
    park_c = await call_tool(tools_by_name, "get_centroid", {"geometry": PARK_WGS84})
    building_c = await call_tool(tools_by_name, "get_centroid", {"geometry": BUILDING_WGS84})

    def wkt_point_to_lonlat(wkt: str) -> list[float]:
        inner = wkt.upper().replace("POINT", "").replace("(", "").replace(")", "").strip()
        x_str, y_str = inner.split()[:2]
        return [float(x_str), float(y_str)]

    park_centroid_wkt = park_c.get("geometry")
    building_centroid_wkt = building_c.get("geometry")
    if not park_centroid_wkt or not building_centroid_wkt:
        print(f"get_centroid park payload: {park_c}")
        print(f"get_centroid building payload: {building_c}")
        print("FAIL get_centroid payload unexpected")
        return 1

    dist = await call_tool(
        tools_by_name,
        "calculate_geodetic_distance",
        {
            "point1": wkt_point_to_lonlat(str(park_centroid_wkt)),
            "point2": wkt_point_to_lonlat(str(building_centroid_wkt)),
        },
    )

    print("\n=== Workflow summary ===")
    print(f"UTM CRS: {utm_crs}")
    print(f"Building intersects 100 m park buffer: {intersects}")
    print(f"Buffer area (m^2 in UTM): {area.get('area')}")
    print(f"Geodetic centroid distance (m): {dist.get('distance')}")

    if not intersects:
        print("FAIL expected building to intersect 100 m park buffer for this fixture")
        return 1
    distance = dist.get("distance")
    if distance is None or not (50 < float(distance) < 400):
        print(f"FAIL unexpected geodetic distance: {distance}")
        return 1

    print("PASS park-buffer proximity workflow via MCP tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
