"""Generate llms.txt / llms-full.txt from MkDocs nav and docs pages.

Used as a MkDocs hook (on_pre_build / on_post_build) and as a CLI:

    python scripts/generate_llms.py
"""

from __future__ import annotations

import gzip
import re
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MKDOCS_YML = ROOT / "mkdocs.yml"
SITE_URL = "https://gis-mcp.com"
PRODUCT_NAME = "GIS MCP Server"
DEFINITION = (
    "GIS MCP is an open-source Model Context Protocol server for "
    "GIS/geospatial analysis and AI agents."
)

# Curated paths for /llms.txt (src relative to docs/). Keep this short.
CURATED_START = [
    ("Home", "index.md"),
    ("Getting started", "getting-started.md"),
    ("Architecture", "architecture.md"),
    ("Install", "install/README.md"),
    ("Vibe coding", "vibe-coding.md"),
]
CURATED_AGENTS = [
    ("GIS AI agent overview", "gis-ai-agent/README.md"),
    ("Agent architecture", "gis-ai-agent/architecture.md"),
    ("Choosing a framework", "gis-ai-agent/choosing-framework.md"),
    ("Best practices", "gis-ai-agent/best-practices.md"),
    ("LangChain park-buffer agent", "gis-ai-agent/langchain/basic-geospatial-agent.md"),
    ("LangGraph stateful agent", "gis-ai-agent/langgraph/stateful-geospatial-agent.md"),
    ("LangGraph multi-agent workflow", "gis-ai-agent/langgraph/multi-agent-geospatial-workflow.md"),
    ("LangGraph file-based site suitability", "gis-ai-agent/langgraph/file-based-site-suitability.md"),
    ("OpenAI Agents SDK (Node.js)", "gis-ai-agent/openai-nodejs/basic-geospatial-agent.md"),
]
CURATED_CONFIG = [
    ("HTTP transport", "http-transport.md"),
    ("Storage configuration", "storage-configuration.md"),
    ("Server endpoints", "endpoints.md"),
]
CURATED_API = [
    ("Data gathering", "data-gathering/README.md"),
    ("Shapely", "api/shapely/README.md"),
    ("PyProj", "api/pyproj/README.md"),
    ("GeoPandas", "api/geopandas/README.md"),
    ("Rasterio", "api/rasterio/README.md"),
    ("PySAL", "api/pysal/README.md"),
    ("Visualization", "api/visualize/README.md"),
]
CURATED_OPTIONAL = [
    ("Examples", "examples/README.md"),
    ("Contributing", "contributing.md"),
    ("Related MCP servers", "related-mcp-servers.md"),
    ("CrewAI", "gis-ai-agent/crewai/README.md"),
    ("LlamaIndex", "gis-ai-agent/llamaindex/README.md"),
    ("Google ADK", "gis-ai-agent/google-adk/README.md"),
]

STUB_MARKERS = (
    "tutorial not published yet",
    "status: coming soon",
    "**status: coming soon",
    "no tutorial yet",
)

_CODE_FENCE = re.compile(r"```.*?```", re.S)
_FRONTMATTER = re.compile(r"^---\r?\n.*?\r?\n---\r?\n", re.S)
_STYLE = re.compile(r"<style\b[^>]*>.*?</style>", re.S | re.I)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_HTML = re.compile(r"<[^>]+>")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_WS = re.compile(r"\s+")


def is_external(href: str) -> bool:
    return href.startswith("http://") or href.startswith("https://")


def md_to_url(src: str) -> str:
    """Map a docs-relative markdown path to the published MkDocs URL path."""
    path = src.replace("\\", "/")
    if path.endswith("/README.md"):
        path = path[: -len("README.md")]
    elif path == "index.md":
        return "/"
    elif path.endswith(".md"):
        path = path[: -len(".md")] + "/"
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path += "/"
    return path


def page_url(src: str) -> str:
    return urljoin(SITE_URL + "/", md_to_url(src).lstrip("/"))


def load_mkdocs() -> dict:
    import yaml

    class Loader(yaml.SafeLoader):
        pass

    def _python_name(loader, suffix, node):
        return None

    Loader.add_multi_constructor("tag:yaml.org,2002:python/name:", _python_name)
    with MKDOCS_YML.open(encoding="utf-8") as fh:
        return yaml.load(fh, Loader=Loader)


def walk_nav(items: Iterable, section: str = "") -> list[tuple[str, str, str]]:
    """Return (section, title, href_or_src) from MkDocs nav."""
    rows: list[tuple[str, str, str]] = []
    for item in items:
        if isinstance(item, str):
            rows.append((section, item, item))
            continue
        if not isinstance(item, dict):
            continue
        for title, value in item.items():
            if isinstance(value, str):
                display = str(title)
                if display.lower() == "overview" and section:
                    parent = section.rsplit(" / ", 1)[-1]
                    parent = parent[:1].upper() + parent[1:] if parent else parent
                    display = f"{parent} overview"
                rows.append((section, display, value))
            elif isinstance(value, list):
                child_section = str(title) if not section else f"{section} / {title}"
                rows.extend(walk_nav(value, child_section))
    return rows


def _group_key(section: str) -> str:
    if not section:
        return "Docs"
    parts = section.split(" / ")
    if parts[0].upper() == "DOCUMENTATIONS":
        if len(parts) > 1:
            name = parts[1]
        else:
            name = "Project"
    else:
        name = parts[0]
    if name.lower() == "examples":
        return "Examples"
    return name


def strip_markup(text: str) -> str:
    text = _FRONTMATTER.sub("", text, count=1)
    text = _CODE_FENCE.sub(" ", text)
    text = _STYLE.sub(" ", text)
    text = _COMMENT.sub(" ", text)
    text = _MD_LINK.sub(r"\1", text)
    text = _HTML.sub(" ", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return text


def extract_description(src: str, markdown: str) -> str:
    if src.replace("\\", "/") == "index.md":
        return (
            "Open-source MCP server that connects GIS libraries "
            "(Shapely, PyProj, GeoPandas, Rasterio, PySAL) to LLMs."
        )

    body = strip_markup(markdown)
    paragraphs: list[str] = []
    buf: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            if buf:
                paragraphs.append(" ".join(buf))
                buf = []
            continue
        if not line:
            if buf:
                paragraphs.append(" ".join(buf))
                buf = []
            continue
        if line.startswith("|") or line.startswith("- ") or line.startswith("* "):
            continue
        if line.lower().startswith("tool:") or line.lower() in {
            "parameters",
            "returns",
            "example",
            "examples",
        }:
            continue
        if line.startswith("{") or line.startswith("json "):
            continue
        buf.append(line)
    if buf:
        paragraphs.append(" ".join(buf))

    for para in paragraphs:
        clean = _WS.sub(" ", para).strip(" >-")
        if len(clean) >= 24:
            if len(clean) > 180:
                clean = clean[:177].rstrip() + "..."
            return clean
    return ""


def is_stub_page(markdown: str) -> bool:
    head = markdown[:1200].lower()
    return any(marker in head for marker in STUB_MARKERS)


def read_docs(src: str) -> str:
    path = DOCS / src
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def link_line(title: str, src: str, note: str) -> str:
    url = src if is_external(src) else page_url(src)
    if note:
        return f"- [{title}]({url}): {note}"
    return f"- [{title}]({url})"


def note_for(src: str, title: str, markdown: str) -> str:
    rel = src.replace("\\", "/")
    if rel == "donate.md":
        return "Support GIS MCP Server development"
    if is_stub_page(markdown):
        return "Tutorial not published yet"
    desc = extract_description(src, markdown)
    if desc:
        return desc
    return title


def build_llms_txt() -> str:
    def section(heading: str, entries: list[tuple[str, str]]) -> str:
        lines = [f"## {heading}", ""]
        for title, src in entries:
            markdown = read_docs(src)
            lines.append(link_line(title, src, note_for(src, title, markdown)))
        lines.append("")
        return "\n".join(lines)

    parts = [
        f"# {PRODUCT_NAME}",
        "",
        f"> {DEFINITION}",
        "",
        "Install with `pip install gis-mcp`. Default transport is STDIO (`gis-mcp`).",
        "HTTP and SSE are also supported (`/mcp` or `/sse`; storage at `/storage`).",
        "Docker serves HTTP on port 9010. Optional extras: `[visualize]`,",
        "`[administrative-boundaries]`, `[climate]`, `[ecology]`, `[movement]`,",
        "`[land-cover]`, `[satellite-imagery]`, `[gcp]`.",
        "",
        "GIS MCP exposes Shapely, GeoPandas, Rasterio, PyProj, and PySAL as MCP",
        "tools so agents run real geospatial operations instead of invented math.",
        "",
        section("Start here", CURATED_START),
        section("GIS AI agents", CURATED_AGENTS),
        section("Configuration", CURATED_CONFIG),
        section("API overviews", CURATED_API),
        "## Optional",
        "",
        link_line(
            "Full LLM context",
            f"{SITE_URL}/llms-full.txt",
            "Complete page and tool inventory",
        ),
    ]
    for title, src in CURATED_OPTIONAL:
        markdown = read_docs(src)
        parts.append(link_line(title, src, note_for(src, title, markdown)))
    parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def build_llms_full_txt(nav_rows: list[tuple[str, str, str]]) -> str:
    extras = (
        "`pip install gis-mcp` (Python 3.10+). Optional extras: "
        "`[visualize]`, `[administrative-boundaries]`, `[climate]`, `[ecology]`, "
        "`[movement]`, `[land-cover]`, `[satellite-imagery]`, `[gcp]`, or `[all]`."
    )
    parts = [
        f"# {PRODUCT_NAME}",
        "",
        f"> {DEFINITION}",
        "",
        "GIS MCP (GIS MCP Server) lets AI agents run real GIS workflows through",
        "Shapely, GeoPandas, Rasterio, PyProj, and PySAL. Optional helpers add",
        "administrative boundaries, climate, ecology, movement, land cover,",
        "satellite imagery, visualization, and Google Cloud Storage.",
        "",
        "## About",
        "",
        f"- {DEFINITION}",
        f"- Install: {extras}",
        "- Transports: STDIO (default, `gis-mcp`), HTTP, SSE.",
        "- HTTP/SSE endpoints: `/mcp` or `/sse`; storage API at `/storage`.",
        "- Storage: `GIS_MCP_STORAGE_PATH` / `--storage-path` (default `~/.gis_mcp/data`), or GCS via `[gcp]`.",
        "- Docker: `docker build -t gis-mcp .` then `docker run -p 9010:9010 gis-mcp` (HTTP on 9010).",
        "- Debug logs: `--debug`.",
        f"- Site: {SITE_URL}/",
        f"- Summary for small context windows: {SITE_URL}/llms.txt",
        "",
        "## Capabilities",
        "",
        "- Shapely: buffer, overlay, centroid, bounds, simplify, make_valid, distance/area/length.",
        "- PyProj: CRS transforms, EPSG/UTM helpers, geodetic distance/area/point.",
        "- GeoPandas: vector IO, spatial join/overlay, dissolve, clip, explode, nearest.",
        "- Rasterio: GeoTIFF IO, clip/reproject/resample, NDVI, hillshade, focal/zonal stats, tile.",
        "- PySAL: Moran/Geary/Getis-Ord, weights, Markov, OLS diagnostics, clustering.",
        "- Visualization: static maps and interactive web maps (Folium/PyDeck with `[visualize]`).",
        "",
        "## Use with AI editors and agents",
        "",
        "- Pin this file or fetch it from the docs site when the model has a large window.",
        "- Configure `.cursor/mcp.json` or Claude Desktop to run `gis-mcp` (stdio) or HTTP.",
        f"- Agent tutorials: {SITE_URL}/gis-ai-agent/",
        "",
    ]

    grouped: dict[str, list[tuple[str, str]]] = {}
    seen_src: set[str] = set()
    for section, title, href in nav_rows:
        grouped.setdefault(_group_key(section), []).append((title, href))
        if not is_external(href):
            seen_src.add(href.replace("\\", "/"))

    for heading, entries in grouped.items():
        parts.append(f"## {heading}")
        parts.append("")
        for title, href in entries:
            if is_external(href):
                parts.append(link_line(title, href, ""))
                continue
            markdown = read_docs(href)
            parts.append(link_line(title, href, note_for(href, title, markdown)))
        parts.append("")

    extra_pages: list[tuple[str, str]] = []
    extra_labels = {"donate.md": "Donate"}
    for path in sorted(DOCS.rglob("*.md")):
        rel = path.relative_to(DOCS).as_posix()
        if rel in seen_src:
            continue
        extra_pages.append((rel, rel))
    if extra_pages:
        parts.append("## Additional pages")
        parts.append("")
        for title, src in extra_pages:
            markdown = read_docs(src)
            label = extra_labels.get(src, Path(src).stem.replace("_", " "))
            parts.append(link_line(label, src, note_for(src, label, markdown)))
        parts.append("")

    parts.append("## LLM files")
    parts.append("")
    parts.append(
        link_line("llms.txt", f"{SITE_URL}/llms.txt", "Curated summary for small context windows")
    )
    parts.append(
        link_line(
            "llms-full.txt",
            f"{SITE_URL}/llms-full.txt",
            "This file; complete documentation map",
        )
    )
    parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def write_llms_files() -> tuple[Path, Path]:
    nav = load_mkdocs().get("nav") or []
    nav_rows = walk_nav(nav)
    summary = build_llms_txt()
    full = build_llms_full_txt(nav_rows)

    outputs = [
        ROOT / "llms.txt",
        DOCS / "llms.txt",
        ROOT / "llms-full.txt",
        DOCS / "llms-full.txt",
    ]
    outputs[0].write_text(summary, encoding="utf-8", newline="\n")
    outputs[1].write_text(summary, encoding="utf-8", newline="\n")
    outputs[2].write_text(full, encoding="utf-8", newline="\n")
    outputs[3].write_text(full, encoding="utf-8", newline="\n")
    return outputs[0], outputs[2]


def patch_sitemap(site_dir: Path, site_url: str | None = None) -> None:
    """Ensure sitemap.xml lists llms.txt and llms-full.txt."""
    sitemap = site_dir / "sitemap.xml"
    if not sitemap.is_file():
        return
    base = (site_url or SITE_URL).rstrip("/") + "/"
    text = sitemap.read_text(encoding="utf-8")
    today = date.today().isoformat()
    additions = []
    for name in ("llms.txt", "llms-full.txt"):
        loc = f"{base}{name}"
        if f"<loc>{loc}</loc>" in text:
            continue
        additions.append(
            "    <url>\n"
            f"         <loc>{loc}</loc>\n"
            f"         <lastmod>{today}</lastmod>\n"
            "    </url>"
        )
    if additions:
        closing = "</urlset>"
        if closing not in text:
            return
        text = text.replace(closing, "\n".join(additions) + "\n" + closing)
        if not text.endswith("\n"):
            text += "\n"
        sitemap.write_text(text, encoding="utf-8")

    gz_path = site_dir / "sitemap.xml.gz"
    with gzip.open(gz_path, "wb") as fh:
        fh.write(sitemap.read_bytes())


def on_pre_build(config) -> None:
    write_llms_files()


def on_post_build(config) -> None:
    site_dir = Path(config["site_dir"])
    site_url = str(config.get("site_url") or SITE_URL)
    patch_sitemap(site_dir, site_url)


def main() -> None:
    summary, full = write_llms_files()
    print(f"Wrote {summary.relative_to(ROOT)} and {full.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
