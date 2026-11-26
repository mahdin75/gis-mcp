"""Compare the MCP tool catalog and representative payloads before and after optimization.

Usage (from the repository root, with the project virtualenv):

    python scripts/benchmark_mcp_tokens.py

Token counts:
- chars/4 is a rough estimate (character length divided by 4).
- cl100k is tiktoken's cl100k_base encoding when that package is installed.
  It is a representative BPE tokenizer, not the Claude, Cursor, or ChatGPT tokenizer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gis_mcp.catalog import estimate_tokens, measure_catalog  # noqa: E402
from gis_mcp.compact import vector_preview  # noqa: E402
from gis_mcp.mcp import gis_mcp  # noqa: E402


BASELINE_PATH = ROOT / "docs" / "benchmarks" / "baseline_summary.json"


def _line(label: str, before: int, after: int) -> str:
    delta = after - before
    pct = (100.0 * delta / before) if before else 0.0
    return f"| {label} | {before} | {after} | {delta} | {pct:.1f}% |"


def _preview_sizes() -> dict:
    import geopandas as gpd
    from shapely.geometry import Polygon

    polygons = []
    for i in range(200):
        # A 30-vertex ring is enough to show WKT cost without a huge fixture.
        coords = [(i, 0)] + [(i + (k / 29), (k % 5) / 10) for k in range(30)] + [(i, 0)]
        polygons.append(Polygon(coords))
    gdf = gpd.GeoDataFrame(
        {"name": [f"f{i}" for i in range(200)], "value": list(range(200))},
        geometry=polygons,
        crs="EPSG:4326",
    )
    full = vector_preview(gdf, max_features=5, include_geometry=True, precision=8)
    compact = vector_preview(gdf, max_features=5, include_geometry=False, precision=6)
    full_text = json.dumps(full["preview"], separators=(",", ":"))
    compact_text = json.dumps(compact["preview"], separators=(",", ":"))
    return {
        "features": 200,
        "page": 5,
        "with_geometry_chars": len(full_text),
        "without_geometry_chars": len(compact_text),
        "with_geometry_tokens": estimate_tokens(full_text),
        "without_geometry_tokens": estimate_tokens(compact_text),
    }


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    current = measure_catalog(gis_mcp, include_fastmcp_meta=False)
    payload = json.dumps(
        [
            tool.to_mcp_tool(include_fastmcp_meta=False).model_dump(mode="json", exclude_none=True)
            for tool in gis_mcp._tool_manager._tools.values()
        ],
        separators=(",", ":"),
    )
    after_tokens = estimate_tokens(payload)
    before_tokens = {
        "chars": baseline["payload_chars"],
        "chars_div_4": (baseline["payload_chars"] + 3) // 4,
        "cl100k": None,
    }
    previews = _preview_sizes()

    before_desc = baseline["descriptions"]
    after_desc = current["descriptions"]
    shared = sorted(set(before_desc) & set(after_desc))
    desc_before = sum(len(before_desc[name]) for name in shared)
    desc_after = sum(len(after_desc[name]) for name in shared)
    desc_before_tokens = estimate_tokens("\n".join(before_desc[name] for name in shared))
    desc_after_tokens = estimate_tokens("\n".join(after_desc[name] for name in shared))

    report = {
        "tokenizer_note": (
            "chars_div_4 is len/4. cl100k is tiktoken cl100k_base when installed, "
            "otherwise null. Neither is a live Claude or Cursor bill."
        ),
        "tool_count_before": baseline["tool_count"],
        "tool_count_after": current["tool_count"],
        "payload_chars_before": baseline["payload_chars"],
        "payload_chars_after": current["payload_chars"],
        "payload_tokens_before_chars_div_4": before_tokens["chars_div_4"],
        "payload_tokens_after": after_tokens,
        "description_chars_before": baseline["description_chars"],
        "description_chars_after": current["description_chars"],
        "input_schema_chars_before": baseline["input_schema_chars"],
        "input_schema_chars_after": current["input_schema_chars"],
        "output_schema_chars_before": baseline["output_schema_chars"],
        "output_schema_chars_after": current["output_schema_chars"],
        "meta_chars_before": baseline["meta_chars"],
        "meta_chars_after": current["meta_chars"],
        "shared_description_chars_before": desc_before,
        "shared_description_chars_after": desc_after,
        "description_tokens_before": desc_before_tokens,
        "description_tokens_after": desc_after_tokens,
        "average_description_chars_before": round(baseline["description_chars"] / baseline["tool_count"], 1),
        "average_description_chars_after": round(current["description_chars"] / current["tool_count"], 1),
        "average_input_schema_chars_before": round(baseline["input_schema_chars"] / baseline["tool_count"], 1),
        "average_input_schema_chars_after": round(current["input_schema_chars"] / current["tool_count"], 1),
        "preview": previews,
        "structured_content": (
            "FastMCP 2.13 copies dict results into content and structuredContent. "
            "Both copies are sent unless GIS_MCP_STRUCTURED_CONTENT=0. "
            "The default keeps structuredContent so existing clients still receive it."
        ),
    }
    out = ROOT / "docs" / "benchmarks" / "after_summary.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print()
    print("| Metric | Before | After | Delta | Percent |")
    print("| --- | ---: | ---: | ---: | ---: |")
    print(_line("Catalog chars", baseline["payload_chars"], current["payload_chars"]))
    print(_line("Description chars", baseline["description_chars"], current["description_chars"]))
    print(_line("Input schema chars", baseline["input_schema_chars"], current["input_schema_chars"]))
    print(_line("Output schema chars", baseline["output_schema_chars"], current["output_schema_chars"]))
    print(_line("Meta chars", baseline["meta_chars"], current["meta_chars"]))
    print(_line(
        "5-feature preview chars",
        previews["with_geometry_chars"],
        previews["without_geometry_chars"],
    ))


if __name__ == "__main__":
    main()
