"""Compact MCP payloads without dropping the result of a spatial operation."""

from __future__ import annotations

import math
from typing import Any, Iterable, Optional, Sequence


def _is_nan(value: Any) -> bool:
    return isinstance(value, float) and math.isnan(value)


def json_value(value: Any, precision: Optional[int] = None) -> Any:
    """Convert a cell to a JSON value. Floats are rounded only when precision is set."""
    if value is None or _is_nan(value):
        return None
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except Exception:
            value = str(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        if precision is None:
            return float(value)
        return round(value, precision)
    if isinstance(value, str):
        return value
    return str(value)


def cap_sequence(values: Iterable[Any], limit: Optional[int] = None) -> Any:
    """Return the full list unless ``limit`` is set and the series is longer.

    ``limit=None`` keeps the previous full-array result.
    """
    if hasattr(values, "tolist"):
        seq = values.tolist()
    else:
        seq = list(values)
    if limit is None:
        return seq
    limit = max(0, int(limit))
    if len(seq) <= limit:
        out = []
        for item in seq:
            if isinstance(item, bool) or item is None:
                out.append(item)
            elif isinstance(item, (int, float)):
                out.append(json_value(item, precision=8))
            else:
                try:
                    out.append(float(item))
                except (TypeError, ValueError):
                    out.append(json_value(item))
        return out

    numbers = []
    for item in seq:
        try:
            numbers.append(float(item))
        except (TypeError, ValueError):
            numbers.append(float("nan"))
    finite = [n for n in numbers if not math.isnan(n)]
    head = [json_value(n, precision=8) for n in numbers[:limit]]
    return {
        "count": len(seq),
        "truncated": True,
        "limit": limit,
        "min": min(finite) if finite else None,
        "max": max(finite) if finite else None,
        "mean": (sum(finite) / len(finite)) if finite else None,
        "head": head,
    }


def vector_preview(
    gdf: Any,
    *,
    max_features: int = 5,
    offset: int = 0,
    columns: Optional[str] = None,
    include_geometry: bool = True,
    precision: Optional[int] = None,
    bbox: Optional[str] = None,
    simplify: Optional[float] = None,
) -> dict:
    """Page a GeoDataFrame into a small JSON preview.

    The full dataset is unchanged. Geometry is omitted unless requested.
    """
    import shapely.wkt

    total = int(len(gdf))
    view = gdf
    if bbox:
        parts = [float(part.strip()) for part in str(bbox).split(",")]
        if len(parts) != 4:
            raise ValueError("bbox must be minx,miny,maxx,maxy")
        minx, miny, maxx, maxy = parts
        view = view.cx[minx:maxx, miny:maxy]

    geom_name = view.geometry.name
    if columns:
        wanted = [part.strip() for part in columns.split(",") if part.strip()]
        keep = [col for col in wanted if col in view.columns and col != geom_name]
        view = view[keep + [geom_name]]

    matched = int(len(view))
    offset = max(0, int(offset))
    max_features = max(0, int(max_features))
    page = view.iloc[offset : offset + max_features]
    records = []
    for _, row in page.iterrows():
        record = {}
        for col, val in row.items():
            if col == geom_name:
                if not include_geometry:
                    continue
                geom = val
                if geom is not None and simplify:
                    geom = geom.simplify(float(simplify), preserve_topology=True)
                if geom is None:
                    record["geometry"] = None
                elif precision is None:
                    record["geometry"] = geom.wkt
                else:
                    record["geometry"] = shapely.wkt.dumps(
                        geom, rounding_precision=int(precision)
                    )
            else:
                record[col] = json_value(val, precision)
        records.append(record)

    return {
        "preview": records,
        "returned": len(records),
        "offset": offset,
        "matched": matched,
        "truncated": offset + len(records) < matched,
        "total_features": total,
    }


def stac_summary(properties: Any) -> dict:
    """Keep the STAC fields a client needs to identify a scene."""
    if not isinstance(properties, dict):
        return {}
    keys = (
        "datetime",
        "start_datetime",
        "end_datetime",
        "platform",
        "constellation",
        "eo:cloud_cover",
        "gsd",
    )
    summary = {}
    for key in keys:
        if key not in properties or properties[key] is None:
            continue
        value = properties[key]
        if isinstance(value, (str, int, float, bool)):
            summary[key] = value
        else:
            summary[key] = str(value)
    return summary


def species_summary(record: Any) -> dict:
    """Keep the GBIF fields needed to identify a taxon."""
    if not isinstance(record, dict):
        return {}
    keys = (
        "usageKey",
        "scientificName",
        "canonicalName",
        "rank",
        "status",
        "confidence",
        "matchType",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
        "species",
    )
    return {key: record[key] for key in keys if key in record and record[key] is not None}


def table_preview(
    gdf: Any,
    columns: Sequence[str],
    n: int = 5,
    include_geometry: bool = True,
    geometry_key: str = "geometry",
) -> list:
    """Preview rows. Geometry WKT is included unless include_geometry is false."""
    geom_name = getattr(getattr(gdf, "geometry", None), "name", None)
    use = [col for col in columns if col in getattr(gdf, "columns", []) and col != geom_name]
    page = gdf.head(n)
    if use:
        frame = page[use].copy()
        for col in frame.columns:
            frame[col] = frame[col].map(lambda value: json_value(value))
        records = frame.to_dict(orient="records")
    else:
        records = [{} for _ in range(len(page))]
    if include_geometry and geom_name is not None:
        for record, geom in zip(records, page.geometry):
            record[geometry_key] = None if geom is None else geom.wkt
    return records
