import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from ..mcp import gis_mcp
from ..storage_config import get_storage_path, resolve_path

from pystac_client import Client
import planetary_computer as pc

import rasterio
from rasterio.transform import Affine
from rasterio.windows import from_bounds as window_from_bounds
from rasterio.mask import mask as rio_mask
from shapely.geometry import box as shapely_box, shape as shapely_shape, mapping as shapely_mapping
from pyproj import Transformer
from shapely.ops import transform as shapely_transform

logger = logging.getLogger(__name__)

MPC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


def _parse_bbox(bbox_str: Optional[str]) -> Optional[List[float]]:
    """
    Parse "minx,miny,maxx,maxy" -> [minx, miny, maxx, maxy]
    """
    if not bbox_str:
        return None
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be 'minx,miny,maxx,maxy'")
    return [float(v) for v in parts]

def _ensure_dir(p: Optional[str]) -> Path:
    if p:
        out_dir = resolve_path(p, relative_to_storage=True)
    else:
        # Use storage path with satellite_imagery subdirectory
        storage = get_storage_path()
        out_dir = storage / "satellite_imagery"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def _pick_item(collection: str,
               bbox: Optional[List[float]],
               datetime: str,
               cloud_cover: Optional[int],
               intersects: Optional[dict] = None):
    catalog = Client.open(MPC_STAC_URL)

    def _search(dt, cc):
        kwargs = {"collections": [collection], "datetime": dt}
        if intersects is not None:
            kwargs["intersects"] = intersects
        elif bbox:
            kwargs["bbox"] = bbox
        if cc is not None:
            kwargs["query"] = {"eo:cloud_cover": {"lt": cc}}
        return list(catalog.search(**kwargs).items())

    items = _search(datetime, cloud_cover)
    if not items and cloud_cover is not None:
        items = _search(datetime, None)
    if not items:
        try:
            start, end = datetime.split("/")
            items = _search(f"{start}/{end}", None)
            if not items:
                items = _search("2018-01-01/2100-01-01", None)
        except Exception:
            items = _search("2018-01-01/2100-01-01", None)

    if not items:
        raise RuntimeError("No items found. Try widening date range or removing cloud filter.")

    items.sort(key=lambda it: it.properties.get("eo:cloud_cover", 1000))
    return items[0]



def _read_and_optionally_clip(
    href: str,
    bbox: Optional[List[float]],
    geometry_geojson: Optional[dict],
    out_crs: Optional[str]
):
    """
    Read a single-band COG from a (signed) href, with robust bbox/geometry handling:
    - If bbox/geometry are assumed WGS84 (typical), they are reprojected to the asset CRS for cropping.
    - Protects against empty windows (0x0) and raises a helpful error instead of cryptic rasterio errors.
    - Optional reprojection to out_crs after cropping.
    """
    signed = pc.sign(href)
    with rasterio.Env():
        with rasterio.open(signed) as src:
            src_crs = src.crs
            if src_crs is None:
                raise RuntimeError("Source asset has no CRS; cannot crop safely.")

            roi_geom_src = None
            if geometry_geojson:
                roi_geom_src = _project_geojson_to(src_crs, geometry_geojson)
            elif bbox:
                bbox_geom_wgs84 = shapely_box(*bbox)
                roi_geom_src = _project_geometry_to(src_crs, bbox_geom_wgs84, from_crs="EPSG:4326")

            if roi_geom_src:
                roi_bounds = shapely_shape(roi_geom_src).bounds
                if not _bounds_intersect(roi_bounds, src.bounds):
                    raise RuntimeError(
                        f"ROI does not intersect asset. ROI(bounds)={roi_bounds}, asset(bounds)={src.bounds}"
                    )
                data, transform = rio_mask(src, [roi_geom_src], crop=True, nodata=src.nodata)
                if data.ndim == 3:
                    data = data[0]
                if data.size == 0 or data.shape[0] == 0 or data.shape[1] == 0:
                    raise RuntimeError("Crop produced an empty window (0x0). Check ROI and CRS.")
                profile = src.profile.copy()
                profile.update({
                    "height": data.shape[0],
                    "width": data.shape[1],
                    "transform": transform,
                    "count": 1,
                    "crs": src_crs
                })
            else:
                data = src.read(1)
                profile = src.profile.copy()
                profile.update({"count": 1})
                if data.size == 0:
                    raise RuntimeError("Read returned empty data unexpectedly.")

            if out_crs and str(out_crs) != str(profile["crs"]):
                from rasterio.vrt import WarpedVRT
                from rasterio.warp import calculate_default_transform

                transform_out, width_out, height_out = calculate_default_transform(
                    src_crs, out_crs, src.width, src.height, *src.bounds
                )
                with WarpedVRT(src, crs=out_crs, transform=transform_out,
                               width=width_out, height=height_out) as vrt:
                    if roi_geom_src:
                        roi_geom_out = _project_geojson_to(
                            out_crs,
                            shapely_mapping(shapely_shape(roi_geom_src)),
                            from_crs=str(src_crs)
                        )

                        data, transform2 = rio_mask(vrt, [roi_geom_out], crop=True, nodata=vrt.nodata)
                        data = data[0] if data.ndim == 3 else data
                        transform = transform2
                    else:
                        data = vrt.read(1)
                        transform = vrt.transform

                if data.size == 0 or data.shape[0] == 0 or data.shape[1] == 0:
                    raise RuntimeError("Reprojected read produced empty data (0x0). Check ROI and CRS.")
                profile.update({
                    "crs": out_crs,
                    "transform": transform,
                    "width": data.shape[1],
                    "height": data.shape[0]
                })

            return data, profile


def _project_geojson_to(to_crs, geom_geojson, from_crs="EPSG:4326"):
    geom = shapely_shape(geom_geojson)
    return shapely_mapping(_project_geometry_to(to_crs, geom, from_crs=from_crs))


def _project_geometry_to(to_crs, geom, from_crs="EPSG:4326"):
    """Project a Shapely geometry from `from_crs` to `to_crs`."""
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    return shapely_transform(lambda x, y: transformer.transform(x, y), geom)


def _bounds_intersect(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1)


def _write_multiband_geotiff(out_path: Path, bands: List[Any], profiles: List[Dict[str, Any]], dtype: Optional[str] = None):
    """
    Write stacked bands into a single GeoTIFF using the first profile as a template.
    Assumes bands are aligned and same shape.
    """
    if not bands:
        raise RuntimeError("No bands to write.")

    base_profile = profiles[0].copy()
    base_profile.update(
        driver="GTiff",
        count=len(bands),
        compress="deflate",
        tiled=True,
        bigtiff="IF_SAFER"
    )
    if dtype:
        base_profile["dtype"] = dtype

    h0, w0 = bands[0].shape
    for i, b in enumerate(bands):
        if b.shape != (h0, w0):
            raise RuntimeError(f"Band shape mismatch at index {i}: {b.shape} vs {(h0, w0)}")

    with rasterio.open(out_path, "w", **base_profile) as dst:
        for i, b in enumerate(bands, start=1):
            dst.write(b, i)

@gis_mcp.resource("gis://operations/satellite_imagery")
def get_satellite_operations() -> dict:
    """List available satellite imagery operations."""
    return {"operations": ["download_satellite_imagery"]}

@gis_mcp.tool()
def download_satellite_imagery(
    collection: str = "sentinel-2-l2a",
    assets: Union[List[str], str] = ("B04", "B03", "B02"),
    datetime: str = "2024-01-01/2024-12-31",
    cloud_cover_lt: Optional[int] = 20,
    bbox: Optional[str] = None, 
    geometry_geojson: Optional[str] = None,
    out_crs: Optional[str] = None,
    filename: Optional[str] = None,
    path: Optional[str] = None,
    include_properties: bool = True,
) -> Dict[str, Any]:
    """
    Download analysis-ready satellite imagery from Microsoft Planetary Computer (STAC + SAS).
    - Picks the least-cloudy item matching your query (by default Sentinel-2 L2A).
    - Downloads specified asset bands and writes a multi-band GeoTIFF.
    - Optional bbox/geometry crop and CRS reprojection.

    Args:
        collection: STAC collection id (e.g., "sentinel-2-l2a", "landsat-8-c2-l2")
        assets: list of asset keys to download (e.g., ["B04","B03","B02"])
        datetime: STAC datetime/interval (e.g., "2025-08-01/2025-08-31" or "2025-08-05")
        cloud_cover_lt: only items with eo:cloud_cover < this value. Use None to disable.
        bbox: "minx,miny,maxx,maxy" (in degrees if using search with WGS84). Used for cropping window.
        geometry_geojson: a GeoJSON geometry (string). If provided, precise clipping is applied.
        out_crs: target CRS for output (e.g., "EPSG:4326"). If None, keep source asset CRS.
        filename: output file name (without path). If None, an automatic name is generated.
        path: output folder. Defaults to ./data/satellite_imagery

    Returns:
        {"status": "success", "file_path": "...", "item_id": "...", "collection": "...", "assets": [...], "properties": {...}}
        or {"status": "error", "message": "..."}
    """
    try:
        if isinstance(assets, str):
            assets = [a.strip() for a in assets.split(",") if a.strip()]

        out_dir = _ensure_dir(path)
        bbox_vals = _parse_bbox(bbox) if bbox else None
        geom_obj = json.loads(geometry_geojson) if geometry_geojson else None

        item = _pick_item(
            collection=collection,
            bbox=bbox_vals,
            datetime=datetime,
            cloud_cover=cloud_cover_lt,
            intersects=geom_obj 
        )
        if geom_obj and not bbox_vals:
            minx, miny, maxx, maxy = shapely_shape(geom_obj).bounds
            bbox_vals = [minx, miny, maxx, maxy]

        bands = []
        profiles = []
        missing_assets = []
        for asset_key in assets:
            if asset_key not in item.assets:
                missing_assets.append(asset_key)
                continue

            href = item.assets[asset_key].href
            data, profile = _read_and_optionally_clip(
                href=href,
                bbox=bbox_vals,
                geometry_geojson=geom_obj,
                out_crs=out_crs
            )
            bands.append(data)
            profiles.append(profile)

        if missing_assets:
            logger.warning("Missing assets in item %s: %s", item.id, ", ".join(missing_assets))
            if not bands:
                raise RuntimeError(f"Requested assets not available in the chosen item: {missing_assets}")

        if not filename:
            safe_assets = "-".join([a.lower() for a in assets if a not in missing_assets]) or "bands"
            filename = f"{collection}_{item.id}_{safe_assets}.tif"
        out_path = out_dir / filename

        dtype = profiles[0].get("dtype")

        _write_multiband_geotiff(out_path=out_path, bands=bands, profiles=profiles, dtype=dtype)

        logger.info("Saved satellite imagery (%s) to %s", assets, out_path)

        from ..compact import stac_summary
        payload = {
            "status": "success",
            "file_path": str(out_path),
            "item_id": item.id,
            "collection": collection,
            "assets": [a for a in assets if a not in missing_assets],
            "missing_assets": missing_assets,
            "summary": stac_summary(item.properties),
        }
        if include_properties:
            payload["properties"] = item.properties
        return payload

    except Exception as e:
        logger.exception("Failed to download satellite imagery")
        return {"status": "error", "message": str(e)}
