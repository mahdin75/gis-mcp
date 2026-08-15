"""Tests for LLM discovery file generation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_llms", ROOT / "scripts" / "generate_llms.py"
)
gen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gen)


def test_md_to_url_index_and_readme():
    assert gen.md_to_url("index.md") == "/"
    assert gen.md_to_url("install/README.md") == "/install/"
    assert gen.md_to_url("api/shapely/buffer.md") == "/api/shapely/buffer/"
    assert gen.md_to_url("getting-started.md") == "/getting-started/"


def test_is_external_does_not_treat_http_transport_as_url():
    assert not gen.is_external("http-transport.md")
    assert gen.is_external("https://gis-mcp.com/http-transport/")
    assert gen.page_url("http-transport.md") == "https://gis-mcp.com/http-transport/"
    assert gen.page_url("gis-ai-agent/README.md") == "https://gis-mcp.com/gis-ai-agent/"


def test_stub_detection():
    assert gen.is_stub_page("# CrewAI\n\n**Planned** — tutorial not published yet.\n")
    assert not gen.is_stub_page("# LangGraph\n\n## Status\n\n**Available** — shipped.\n")


def test_extract_description_skips_headings():
    md = "# Title\n\nThis paragraph explains the tool in enough detail for a note.\n"
    desc = gen.extract_description("api/shapely/buffer.md", md)
    assert "explains the tool" in desc


def test_patch_sitemap_adds_llms_files(tmp_path: Path):
    sitemap = tmp_path / "sitemap.xml"
    sitemap.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "    <url>\n"
        "         <loc>https://gis-mcp.com/</loc>\n"
        "    </url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    gen.patch_sitemap(tmp_path)
    text = sitemap.read_text(encoding="utf-8")
    assert "<loc>https://gis-mcp.com/llms.txt</loc>" in text
    assert "<loc>https://gis-mcp.com/llms-full.txt</loc>" in text
    assert (tmp_path / "sitemap.xml.gz").is_file()


def test_generated_files_are_curated_and_accurate():
    yaml = pytest.importorskip("yaml")
    del yaml
    summary = gen.build_llms_txt()
    nav = gen.load_mkdocs().get("nav") or []
    full = gen.build_llms_full_txt(gen.walk_nav(nav))

    assert summary.startswith("# GIS MCP Server\n")
    assert gen.DEFINITION in summary
    assert "https://gis-mcp.com/http-transport/" in summary
    assert "](http-transport.md)" not in summary
    assert "https://gis-mcp.com/getting-started/" in summary
    assert "api/shapely/buffer" not in summary
    assert "LangGraph (planned)" not in summary
    assert "LangGraph (planned)" not in full
    assert "https://gis-mcp.com/architecture/" in full
    assert "https://gis-mcp.com/vibe-coding/" in full
    assert "https://gis-mcp.com/endpoints/" in full
    assert "https://gis-mcp.com/examples/movement_example/" in full
    assert "https://gis-mcp.com/gis-ai-agent/langgraph/stateful-geospatial-agent/" in full
    assert "https://gis-mcp.com/gis-ai-agent/langgraph/file-based-site-suitability/" in full
    assert "https://gis-mcp.com/gis-ai-agent/langgraph/file-based-site-suitability/" in summary
    assert "Tutorial not published yet" in full
    assert "gis-mcp.com/api/)" not in full
    assert "gis-mcp.com/api/:" not in full
    assert "gis-mcp.com/api/\n" not in full
