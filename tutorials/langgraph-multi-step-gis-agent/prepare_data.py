from __future__ import annotations
import json
from pathlib import Path
DATA_DIR = Path(__file__).resolve().parent / "data"

def ring(minx: float, miny: float, maxx: float, maxy: float) -> list:
    return [
        [minx, miny],
        [maxx, miny],
        [maxx, maxy],
        [minx, maxy],
        [minx, miny],
    ]

def polygon_feature(name: str, bbox: tuple, **props) -> dict:
    minx, miny, maxx, maxy = bbox
    return {
        "type": "Feature",
        "properties": {"name": name, **props},
        "geometry": {"type": "Polygon", "coordinates": [ring(*bbox)]},
    }

def collection(features: list) -> dict:
    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features,
    }

def write(name: str, fc: dict) -> None:
    path = DATA_DIR / name
    path.write_text(json.dumps(fc, indent=2), encoding="utf-8")
    print(f"Wrote {path} ({len(fc['features'])} features)")

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    downtown = collection(
        [polygon_feature("Downtown Riverside", (-74.042, 40.738, -74.032, 40.746))]
    )
    flood = collection(
        [polygon_feature("Riverside flood zone", (-74.042, 40.738, -74.0395, 40.746))]
    )
    parks = collection(
        [
            polygon_feature(
                "Riverside Park", (-74.0340, 40.7442, -74.0324, 40.7458)
            ),
            polygon_feature(
                "Harbor Green", (-74.0338, 40.7430, -74.0323, 40.7442)
            ),
        ]
    )
    # Designed outcomes:
    #   PASS (inside downtown, outside flood, within ~300 m of a park):
    #     Oak Yard, Maple Yard, Cedar Yard
    #   FAIL flood: River Edge, Canal Cut
    #   FAIL distance: Hilltop Lot, South Fill
    #   FAIL clip (outside downtown): North Annex, Harbor Extra
    lots = collection(
        [
            polygon_feature(
                "Oak Yard",
                (-74.0360, 40.7444, -74.0348, 40.7454),
                lot_id="L01",
                area_sqm=1400,
            ),
            polygon_feature(
                "Maple Yard",
                (-74.0358, 40.7432, -74.0346, 40.7440),
                lot_id="L02",
                area_sqm=950,
            ),
            polygon_feature(
                "Cedar Yard",
                (-74.0362, 40.7424, -74.0352, 40.7431),
                lot_id="L03",
                area_sqm=720,
            ),
            polygon_feature(
                "River Edge",
                (-74.0415, 40.7410, -74.0400, 40.7422),
                lot_id="L04",
                area_sqm=1100,
            ),
            polygon_feature(
                "Canal Cut",
                (-74.0412, 40.7438, -74.0398, 40.7450),
                lot_id="L05",
                area_sqm=880,
            ),
            polygon_feature(
                "Hilltop Lot",
                (-74.0388, 40.7386, -74.0376, 40.7396),
                lot_id="L06",
                area_sqm=1300,
            ),
            polygon_feature(
                "South Fill",
                (-74.0382, 40.7398, -74.0370, 40.7408),
                lot_id="L07",
                area_sqm=800,
            ),
            polygon_feature(
                "North Annex",
                (-74.0380, 40.7464, -74.0368, 40.7474),
                lot_id="L08",
                area_sqm=1000,
            ),
            polygon_feature(
                "Harbor Extra",
                (-74.0316, 40.7410, -74.0304, 40.7420),
                lot_id="L09",
                area_sqm=900,
            ),
        ]
    )
    write("downtown.geojson", downtown)
    write("flood_zone.geojson", flood)
    write("parks.geojson", parks)
    write("vacant_lots.geojson", lots)

if __name__ == "__main__":
    main()
