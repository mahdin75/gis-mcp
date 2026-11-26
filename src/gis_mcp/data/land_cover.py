import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from ..mcp import gis_mcp
from ..storage_config import get_storage_path, resolve_path

from pystac_client import Client
import planetary_computer as pc

import numpy as np
import rasterio
from rasterio.enums import Resampling, ColorInterp
from rasterio.mask import mask as rio_mask
from shapely.geometry import shape as shapely_shape, box as shapely_box, mapping as shapely_mapping
from shapely.ops import transform as shapely_transform
from pyproj import Transformer

logger = logging.getLogger(__name__)

MPC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


def _ensure_dir(p: Optional[str]) -> Path:
    if p:
        out_dir = resolve_path(p, relative_to_storage=True)
    else:
        # Use storage path with land_products subdirectory
        storage = get_storage_path()
        out_dir = storage / "land_products"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def _parse_bbox(bbox_str: Optional[str]) -> Optional[List[float]]:
    if not bbox_str:
        return None
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be 'minx,miny,maxx,maxy'")
    return [float(v) for v in parts]

def _project_geometry_to(to_crs: str, geom, from_crs: str = "EPSG:4326"):
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    return shapely_transform(lambda x, y: transformer.transform(x, y), geom)

def _project_geojson_to(to_crs: str, geom_geojson: dict, from_crs: str = "EPSG:4326"):
    geom = shapely_shape(geom_geojson)
    return shapely_mapping(_project_geometry_to(to_crs, geom, from_crs=from_crs))

def _bounds_intersect(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1)

def _stac_search_one(collection: str,
                     intersects: Optional[dict],
                     bbox: Optional[List[float]],
                     datetime: Optional[str],
                     query: Optional[dict] = None):
    """Return first matching item; prefer least-cloudy if eo:cloud_cover exists."""
    catalog = Client.open(MPC_STAC_URL)

    def _run(dt, q):
        kwargs = {"collections": [collection]}
        if dt:
            kwargs["datetime"] = dt
        if intersects is not None:
            kwargs["intersects"] = intersects
        elif bbox:
            kwargs["bbox"] = bbox
        if q:
            kwargs["query"] = q
        return list(catalog.search(**kwargs).items())

    items = _run(datetime, query)
    if not items and datetime:
        items = _run(None, query)

    if not items:
        raise RuntimeError("No items found for collection/search constraints.")

    items.sort(key=lambda it: it.properties.get("eo:cloud_cover", 0 if "eo:cloud_cover" in it.properties else 0))
    return items[0]

def _read_clip_reproject(href: str,
                         geometry_geojson: Optional[dict],
                         bbox_vals: Optional[List[float]],
                         out_crs: Optional[str],
                         resampling: Resampling = Resampling.nearest):
    """Open a (signed) COG, optionally clip to ROI, and optionally reproject to out_crs."""
    signed = pc.sign(href)
    with rasterio.Env():
        with rasterio.open(signed) as src:
            src_crs = src.crs
            if src_crs is None:
                raise RuntimeError("Source asset has no CRS; cannot process safely.")

            roi_geom_src = None
            if geometry_geojson:
                roi_geom_src = _project_geojson_to(str(src_crs), geometry_geojson)
            elif bbox_vals:
                roi_geom_src = _project_geojson_to(str(src_crs), shapely_mapping(shapely_box(*bbox_vals)))

            if roi_geom_src:
                roi_bounds = shapely_shape(roi_geom_src).bounds
                if not _bounds_intersect(roi_bounds, src.bounds):
                    raise RuntimeError(
                        f"ROI does not intersect asset. ROI(bounds)={roi_bounds}, asset(bounds)={src.bounds}"
                    )
                data, transform = rio_mask(src, [roi_geom_src], crop=True, nodata=src.nodata)
                profile = src.profile.copy()
                count = data.shape[0]
            else:
                data = src.read()
                transform = src.transform
                profile = src.profile.copy()
                count = profile.get("count", data.shape[0])

            if out_crs and str(out_crs) != str(src_crs):
                from rasterio.vrt import WarpedVRT
                from rasterio.warp import calculate_default_transform
                transform_out, width_out, height_out = calculate_default_transform(
                    src_crs, out_crs, src.width, src.height, *src.bounds
                )
                with rasterio.open(signed) as rs:
                    with WarpedVRT(rs, crs=out_crs, transform=transform_out,
                                   width=width_out, height=height_out,
                                   resampling=resampling) as vrt:
                        if roi_geom_src:
                            roi_geom_out = _project_geojson_to(
                                out_crs, shapely_mapping(shapely_shape(roi_geom_src)), from_crs=str(src_crs)
                            )
                            data, transform = rio_mask(vrt, [roi_geom_out], crop=True, nodata=vrt.nodata)
                        else:
                            data = vrt.read()
                            transform = vrt.transform
                profile.update({"crs": out_crs, "transform": transform,
                                "width": data.shape[-1], "height": data.shape[-2], "count": data.shape[0]})
            else:
                profile.update({"transform": transform,
                                "width": data.shape[-1], "height": data.shape[-2], "count": count})

            if data.size == 0:
                raise RuntimeError("Read produced empty data. Check ROI and CRS.")

            return data, profile

def _write_gtiff(out_path: Path, data: np.ndarray, profile: Dict[str, Any],
                 colorinterp: Optional[List[ColorInterp]] = None):
    prof = profile.copy()
    prof.update(driver="GTiff", compress="deflate", tiled=True, bigtiff="IF_SAFER")
    with rasterio.open(out_path, "w", **prof) as dst:
        if data.ndim == 2:
            dst.write(data, 1)
        else:
            for i in range(data.shape[0]):
                dst.write(data[i], i + 1)
        if colorinterp:
            dst.colorinterp = tuple(colorinterp)

@gis_mcp.resource("gis://operations/land_products")
def get_land_products() -> dict:
    """List available land products operations."""
    return {"operations": ["download_worldcover", "compute_s2_ndvi"]}

@gis_mcp.tool()
def download_worldcover(
    year: int = 2021,
    collection: Optional[str] = None,
    asset_key: str = "map",
    bbox: Optional[str] = None,
    geometry_geojson: Optional[str] = None,
    out_crs: Optional[str] = "EPSG:4326",
    filename: Optional[str] = None,
    path: Optional[str] = None,
    include_properties: bool = True,
) -> Dict[str, Any]:
    """
    Download ESA WorldCover (10 m) for the given AOI and year from Microsoft Planetary Computer.
    - Crops to bbox/geometry (WGS84), optional reprojection.
    - Writes a single-band categorical GeoTIFF (land cover classes).
    Notes:
      * On MPC, the collection is commonly 'esa-worldcover' with yearly items; the default here
        auto-selects by year. If your deployment uses different IDs, pass `collection` explicitly.
      * `asset_key` is typically 'map'.

    Args:
        year: WorldCover year (e.g., 2020, 2021, 2023).
        collection: STAC collection (default resolves to 'esa-worldcover').
        asset_key: Asset key to read ('map' usually).
        bbox: "minx,miny,maxx,maxy" WGS84.
        geometry_geojson: GeoJSON geometry string (WGS84).
        out_crs: Output CRS (default EPSG:4326).
        filename: Output filename (e.g., "worldcover_iran_2021.tif").
        path: Output directory.

    Returns:
        dict with status, file_path, item_id, collection, properties.
    """
    try:
        out_dir = _ensure_dir(path)
        bbox_vals = _parse_bbox(bbox) if bbox else None
        geom_obj = json.loads(geometry_geojson) if geometry_geojson else None

        coll = collection or "esa-worldcover"
        dt = f"{year}-01-01/{year}-12-31"

        item = _stac_search_one(
            collection=coll,
            intersects=geom_obj,
            bbox=bbox_vals,
            datetime=dt,
            query=None
        )

        if asset_key not in item.assets:
            raise RuntimeError(f"Asset '{asset_key}' not found in item '{item.id}'. Available: {list(item.assets.keys())}")

        data, profile = _read_clip_reproject(
            href=item.assets[asset_key].href,
            geometry_geojson=geom_obj,
            bbox_vals=bbox_vals,
            out_crs=out_crs,
            resampling=Resampling.nearest
        )

        if not filename:
            filename = f"worldcover_{year}_{item.id}.tif"
        out_path = out_dir / filename

        profile.update(count=1, dtype=data.dtype.name if hasattr(data, "dtype") else profile.get("dtype", "uint16"))
        if data.ndim == 3:
            data = data[0]

        _write_gtiff(out_path, data, profile)

        logger.info("Saved WorldCover to %s", out_path)
        from ..compact import stac_summary
        payload = {
            "status": "success",
            "file_path": str(out_path),
            "item_id": item.id,
            "collection": coll,
            "year": year,
            "asset": asset_key,
            "summary": stac_summary(item.properties),
        }
        if include_properties:
            payload["properties"] = item.properties
        return payload
    except Exception as e:
        logger.exception("Failed to download WorldCover")
        return {"status": "error", "message": str(e)}

@gis_mcp.tool()
def compute_s2_ndvi(
    datetime: str = "2024-07-01/2024-07-15",
    cloud_cover_lt: Optional[int] = 20,
    bbox: Optional[str] = None,
    geometry_geojson: Optional[str] = None,
    out_crs: Optional[str] = "EPSG:4326",
    filename: Optional[str] = None,
    path: Optional[str] = None,
    include_properties: bool = True,
) -> Dict[str, Any]:
    """
    Compute NDVI from Sentinel-2 L2A (B08=NIR, B04=Red) for an AOI/time window via MPC.
    - Picks a low-cloud item intersecting the AOI.
    - Clips to AOI and writes single-band NDVI GeoTIFF scaled to float32 (-1..1).

    Args:
        datetime: STAC datetime/interval (e.g., "2024-07-01/2024-07-15").
        cloud_cover_lt: Only consider items with eo:cloud_cover < value. Use None to disable.
        bbox: "minx,miny,maxx,maxy" (WGS84).
        geometry_geojson: GeoJSON geometry (WGS84).
        out_crs: Output CRS for NDVI raster.
        filename: Output filename (default auto-generated).
        path: Output directory.

    Returns:
        dict with status, file_path, item_id, collection, properties.
    """
    try:
        out_dir = _ensure_dir(path)
        bbox_vals = _parse_bbox(bbox) if bbox else None
        geom_obj = json.loads(geometry_geojson) if geometry_geojson else None

        collection = "sentinel-2-l2a"
        query = {"eo:cloud_cover": {"lt": cloud_cover_lt}} if cloud_cover_lt is not None else None

        item = _stac_search_one(
            collection=collection,
            intersects=geom_obj,
            bbox=bbox_vals,
            datetime=datetime,
            query=query
        )

        need_assets = {"B08": "NIR", "B04": "RED"}
        hrefs = {}
        for k in need_assets.keys():
            if k not in item.assets:
                raise RuntimeError(f"Sentinel-2 asset '{k}' not available in item '{item.id}'.")
            hrefs[k] = item.assets[k].href

        nir, nir_profile = _read_clip_reproject(
            href=hrefs["B08"], geometry_geojson=geom_obj, bbox_vals=bbox_vals, out_crs=out_crs,
            resampling=Resampling.bilinear
        )
        red, red_profile = _read_clip_reproject(
            href=hrefs["B04"], geometry_geojson=geom_obj, bbox_vals=bbox_vals, out_crs=out_crs,
            resampling=Resampling.bilinear
        )

        nir_arr = nir[0] if nir.ndim == 3 else nir
        red_arr = red[0] if red.ndim == 3 else red

        if nir_arr.shape != red_arr.shape:
            raise RuntimeError(f"Band shape mismatch after processing: NIR{nir_arr.shape} vs RED{red_arr.shape}")

        nir_arr = nir_arr.astype("float32")
        red_arr = red_arr.astype("float32")
        denom = (nir_arr + red_arr)
        ndvi = (nir_arr - red_arr) / np.where(denom == 0, np.nan, denom)
        ndvi = np.nan_to_num(ndvi, nan=0.0).astype("float32")

        out_profile = nir_profile.copy()
        out_profile.update(count=1, dtype="float32", nodata=np.float32(0.0))

        if not filename:
            filename = f"s2_ndvi_{item.id}.tif"
        out_path = out_dir / filename

        _write_gtiff(out_path, ndvi, out_profile)

        logger.info("Saved NDVI to %s", out_path)
        from ..compact import stac_summary
        payload = {
            "status": "success",
            "file_path": str(out_path),
            "item_id": item.id,
            "collection": collection,
            "assets": ["B08", "B04"],
            "summary": stac_summary(item.properties),
        }
        if include_properties:
            payload["properties"] = item.properties
        return payload
    except Exception as e:
        logger.exception("Failed to compute NDVI")
        return {"status": "error", "message": str(e)}
