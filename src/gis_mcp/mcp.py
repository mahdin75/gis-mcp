# MCP imports using the new SDK patterns
import os

from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware


# Sent once in the MCP initialize result. Kept short so it does not
# outweigh the catalog savings. Per-tool text should not repeat this.
INSTRUCTIONS = (
    "Geometry strings are WKT. Paths are local files. "
    "Defaults match the full result. "
    "Pass include_geometry=false, compact=true, max_features, max_records, limit, or precision to shrink a response."
)


class CompactResultMiddleware(Middleware):
    """Omit structuredContent when it duplicates the JSON text content.

    MCP requires ``content``. FastMCP also copies a dict into structuredContent.
    That duplicate stays on by default so existing clients keep working.
    Set GIS_MCP_STRUCTURED_CONTENT=0 to send the JSON text only.
    """

    async def on_call_tool(self, context, call_next):
        result = await call_next(context)
        flag = os.getenv("GIS_MCP_STRUCTURED_CONTENT", "1").strip().lower()
        if flag in {"0", "false", "no", "off"}:
            result.structured_content = None
        return result


gis_mcp = FastMCP(
    "GIS MCP",
    instructions=INSTRUCTIONS,
    include_fastmcp_meta=False,
)
gis_mcp.add_middleware(CompactResultMiddleware())
