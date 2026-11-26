"""Helper utilities for testing GIS MCP functions."""
import json
from fastmcp import Client
from gis_mcp.mcp import gis_mcp


async def call_tool(tool_name: str, **kwargs):
    """
    Helper function to call MCP tools and return parsed JSON result.
    
    Args:
        tool_name: Name of the tool to call
        **kwargs: Tool parameters
        
    Returns:
        dict: Parsed JSON result from the tool
    """
    async with Client(gis_mcp) as client:
        result = await client.call_tool(tool_name, kwargs)
        # According to FastMCP docs, use result.data
        # result.data contains the actual return value from the tool
        if hasattr(result, 'data'):
            return result.data
        # Fallback for older versions or different result types
        elif hasattr(result, 'text'):
            return json.loads(result.text)
        else:
            return result


def get_result_data(result):
    """
    Extract data from a CallToolResult.

    Structured content is omitted by default to avoid sending the same JSON
    twice. Fall back to the text content block, which remains the MCP payload.
    """
    data = getattr(result, "data", None)
    if data is not None:
        return data
    content = getattr(result, "content", None) or []
    if content:
        text = getattr(content[0], "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"message": text}
    if hasattr(result, "text"):
        return json.loads(result.text)
    return result
