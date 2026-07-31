"""
Storage HTTP endpoints for GIS MCP Server.

This module provides HTTP endpoints for file upload, download, and listing
operations when the server runs in HTTP/SSE transport mode. Operations go
through the configured storage adapter (local filesystem or GCP).
"""

import io
import logging
from typing import Optional

from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.datastructures import UploadFile

from .mcp import gis_mcp
from .storage_config import get_storage_adapter

logger = logging.getLogger("gis-mcp")


@gis_mcp.custom_route("/storage/upload", methods=["POST"])
async def upload_file(request: Request) -> JSONResponse:
    """
    Upload a file to remote storage.

    Expected request:
    - Content-Type: multipart/form-data
    - Fields: 'file' (file data), 'path' (optional remote path)

    Returns JSON with:
    - remote_path: Path where file was saved
    - size: File size in bytes
    - message: Success message
    """
    try:
        form = await request.form()

        if "file" not in form:
            return JSONResponse(
                {"error": "Missing 'file' field in form data"},
                status_code=400,
            )

        file_item = form["file"]
        if not isinstance(file_item, UploadFile):
            return JSONResponse(
                {"error": "Invalid file field"},
                status_code=400,
            )

        remote_path = form.get("path")
        if remote_path is None:
            remote_path = file_item.filename or "uploaded_file"

        remote_path = str(remote_path).lstrip("/")
        adapter = get_storage_adapter()

        # Ensure parent "directory" exists for local / cache backends
        parent = "/".join(remote_path.split("/")[:-1])
        if parent:
            adapter.ensure_dir(parent)

        file_content = await file_item.read()
        stored_path = adapter.write_bytes(remote_path, file_content)
        file_size = len(file_content)

        logger.info(
            "File uploaded: %s (%s bytes) via %s",
            stored_path,
            file_size,
            adapter.describe(),
        )

        return JSONResponse(
            {
                "remote_path": stored_path,
                "size": file_size,
                "message": f"File uploaded successfully to {stored_path}",
            }
        )

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        return JSONResponse(
            {"error": str(e), "message": f"Failed to upload file: {str(e)}"},
            status_code=500,
        )


@gis_mcp.custom_route("/storage/download", methods=["GET"])
async def download_file(request: Request):
    """
    Download a file from remote storage.

    Query parameters:
    - path: Path to the file to download (required)

    Returns the file content with appropriate Content-Type.
    """
    try:
        path_param = request.query_params.get("path")
        if not path_param:
            return JSONResponse(
                {"error": "Missing 'path' query parameter"},
                status_code=400,
            )

        remote_path = str(path_param).lstrip("/")
        adapter = get_storage_adapter()

        if not adapter.exists(remote_path):
            return JSONResponse(
                {"error": f"File not found: {remote_path}"},
                status_code=404,
            )

        if not adapter.is_file(remote_path):
            return JSONResponse(
                {"error": f"Path is not a file: {remote_path}"},
                status_code=400,
            )

        data = adapter.read_bytes(remote_path)
        filename = remote_path.split("/")[-1] or "download"

        logger.info(
            "File download requested: %s via %s",
            remote_path,
            adapter.describe(),
        )

        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(data)),
            },
        )

    except FileNotFoundError as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=404,
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}", exc_info=True)
        return JSONResponse(
            {"error": str(e), "message": f"Failed to download file: {str(e)}"},
            status_code=500,
        )


@gis_mcp.custom_route("/storage/list", methods=["GET"])
async def list_files(request: Request) -> JSONResponse:
    """
    List files in remote storage.

    Query parameters:
    - path: Optional directory path to list (defaults to storage root)

    Returns JSON with:
    - files: List of file/directory information
    - path: The path that was listed
    """
    try:
        path_param = request.query_params.get("path")
        remote_path = str(path_param).lstrip("/") if path_param else ""
        adapter = get_storage_adapter()

        try:
            entries = adapter.list_dir(remote_path)
        except FileNotFoundError:
            return JSONResponse(
                {"error": f"Path not found: {remote_path or 'root'}"},
                status_code=404,
            )
        except PermissionError:
            return JSONResponse(
                {"error": f"Permission denied: {remote_path or 'root'}"},
                status_code=403,
            )

        files_list = [
            {
                "name": entry.name,
                "path": entry.path,
                "size": entry.size,
                "type": entry.type,
                "modified": entry.modified,
            }
            for entry in entries
        ]

        logger.info(
            "Listed %s items in %s via %s",
            len(files_list),
            remote_path or "root",
            adapter.describe(),
        )

        return JSONResponse(
            {
                "files": files_list,
                "path": remote_path or "/",
            }
        )

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        return JSONResponse(
            {"error": str(e), "message": f"Failed to list files: {str(e)}"},
            status_code=500,
        )
