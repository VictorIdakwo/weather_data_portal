"""
Land-degradation indicators.

Phase 5a: MODIS Burned Area (MCD64A1) — per-polygon monthly time
series. For each input AOI polygon and each month in the requested
range, returns the burned area (km²) and the percentage of the
polygon that burned.

Reference:
  Giglio, L. et al. (2018), "The Collection 6 MODIS burned area
  mapping algorithm and product." Remote Sensing of Environment 217.

Data:
  MODIS/061/MCD64A1  Monthly burned area, 500 m, Nov 2000 -> present.
    BurnDate band:
      positive int  day-of-year the pixel burned in this month
      0             not burned
      -1            unclassified
      -2            water

Method:
  Per polygon and per calendar month in the range, computes
  sum(pixelArea * (BurnDate > 0)). The polygon's total area is
  computed once (identity image), so the burned-percentage of each
  polygon is meaningful even when the polygon straddles missing tiles.

Output slots into the weather schema: (date, latitude, longitude,
location_id, polygon_name, BURNED_AREA_KM2, PERCENT_BURNED). The
polygon centroid is emitted as latitude / longitude so the standard
weather display/export path works without additional branching.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple, Optional

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from .earth_engine_utils import EarthEngineClient
from .lulc import _to_2d_geometry, best_polygon_name


# ---------------------------------------------------------------------------
# Parameter registry
# ---------------------------------------------------------------------------

BURNED_AREA_PARAMETERS: Dict[str, Dict[str, str]] = {
    "Burned Area (MODIS MCD64A1)": {
        "BURNED_AREA_KM2": "Monthly burned area (km²)",
        "PERCENT_BURNED": "Percent of polygon burned (%)",
    },
}

TEMPORAL_RESOLUTIONS = ["Monthly"]


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    return BURNED_AREA_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    return TEMPORAL_RESOLUTIONS


# ---------------------------------------------------------------------------
# Polygon prep (same guardrails as LULC / hydrology)
# ---------------------------------------------------------------------------

def _prepare_features(aoi_gdf: gpd.GeoDataFrame) -> Tuple[List, List[Dict]]:
    """Convert AOI GeoDataFrame to (ee.Feature list, meta list).
    3D KMLs are flattened; invalid topology is repaired; unusable rows
    are skipped rather than raising."""
    if aoi_gdf.crs is None or aoi_gdf.crs.to_epsg() != 4326:
        aoi_gdf = aoi_gdf.to_crs(4326)
    features: List = []
    meta: List[Dict] = []
    for idx, row in aoi_gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        geom = _to_2d_geometry(geom)
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        if not geom.is_valid:
            try:
                geom = geom.buffer(0)
            except Exception:
                continue
            if geom.is_empty or geom.geom_type not in ("Polygon", "MultiPolygon"):
                continue
        pname = best_polygon_name(row, idx)
        centroid = geom.centroid
        features.append(
            ee.Feature(ee.Geometry(mapping(geom)), {"polygon_id": int(idx)})
        )
        meta.append({
            "polygon_id": int(idx),
            "polygon_name": pname,
            "latitude": float(centroid.y),
            "longitude": float(centroid.x),
        })
    return features, meta


# ---------------------------------------------------------------------------
# Public fetch entry point
# ---------------------------------------------------------------------------

def fetch_burned_area_from_gdf(
    aoi_gdf: gpd.GeoDataFrame,
    parameters: List[str],
    start_date: str,
    end_date: str,
    credentials_dict: Dict,
    scale_m: int = 500,
) -> pd.DataFrame:
    """Monthly burned-area time series per AOI polygon."""
    if not parameters:
        raise ValueError("No parameters requested.")

    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    features, meta = _prepare_features(aoi_gdf)
    if not features:
        raise ValueError("No usable polygon geometries in input.")
    fc = ee.FeatureCollection(features)
    meta_by_id = {m["polygon_id"]: m for m in meta}

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    pixel_area = ee.Image.pixelArea()

    # Total polygon area, computed once (independent of month).
    total_reduced = pixel_area.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.sum().setOutputs(["total_area_m2"]),
        scale=scale_m,
        tileScale=4,
    )
    try:
        total_feats = total_reduced.getInfo().get("features", [])
    except Exception as e:
        raise RuntimeError(f"Earth Engine total-area query failed: {e}") from e

    total_by_id: Dict[int, float] = {}
    for feat in total_feats:
        props = feat.get("properties") or {}
        try:
            pid = int(props.get("polygon_id"))
            total_by_id[pid] = float(props.get("total_area_m2") or 0.0)
        except (TypeError, ValueError):
            continue

    coll = ee.ImageCollection("MODIS/061/MCD64A1").select("BurnDate")

    rows: List[Dict] = []
    cur = start_dt.replace(day=1)
    end_month = end_dt.replace(day=1)

    print(
        f"[BurnedArea] {len(features)} polygon(s)  "
        f"{cur.date()}..{end_month.date()}  MCD64A1 @ {scale_m} m"
    )

    while cur <= end_month:
        m_start = ee.Date.fromYMD(cur.year, cur.month, 1)
        m_end = m_start.advance(1, "month")
        month_coll = coll.filterDate(m_start, m_end)

        try:
            n_imgs = month_coll.size().getInfo()
        except Exception as e:
            print(f"[WARN] MCD64A1 {cur.year}-{cur.month:02d} size: {e}")
            n_imgs = 0

        server_feats: List = []
        if n_imgs > 0:
            # BurnDate > 0 marks a burned pixel; ignore 0 / -1 / -2.
            burned_mask = month_coll.first().gt(0).unmask(0)
            burned_area_img = pixel_area.multiply(burned_mask).rename("burned_m2")
            try:
                reduced = burned_area_img.reduceRegions(
                    collection=fc,
                    reducer=ee.Reducer.sum().setOutputs(["burned_m2"]),
                    scale=scale_m,
                    tileScale=4,
                )
                server_feats = reduced.getInfo().get("features", [])
            except Exception as e:
                print(f"[WARN] MCD64A1 {cur.year}-{cur.month:02d} reduce: {e}")
                server_feats = []

        got_ids = set()
        for feat in server_feats:
            props = feat.get("properties") or {}
            try:
                pid = int(props.get("polygon_id"))
            except (TypeError, ValueError):
                continue
            m = meta_by_id.get(pid)
            if m is None:
                continue
            got_ids.add(pid)
            burned_m2 = float(props.get("burned_m2") or 0.0)
            total_m2 = total_by_id.get(pid, 0.0)
            pct = (burned_m2 / total_m2 * 100.0) if total_m2 > 0 else 0.0
            rows.append({
                "date": pd.Timestamp(year=cur.year, month=cur.month, day=1),
                "latitude": m["latitude"],
                "longitude": m["longitude"],
                "location_id": pid,
                "polygon_name": m["polygon_name"],
                "BURNED_AREA_KM2": round(burned_m2 / 1_000_000.0, 4),
                "PERCENT_BURNED": round(pct, 3),
            })

        # Fill zero rows for polygons that didn't come back this month
        # (e.g. because there was no MCD64A1 image at all). This keeps the
        # time series contiguous per location.
        for pid, m in meta_by_id.items():
            if pid in got_ids:
                continue
            rows.append({
                "date": pd.Timestamp(year=cur.year, month=cur.month, day=1),
                "latitude": m["latitude"],
                "longitude": m["longitude"],
                "location_id": pid,
                "polygon_name": m["polygon_name"],
                "BURNED_AREA_KM2": 0.0,
                "PERCENT_BURNED": 0.0,
            })

        # Advance one month
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Keep only requested parameters + join keys + polygon_name for context.
    keep_cols = ["date", "latitude", "longitude", "location_id", "polygon_name"]
    for p in parameters:
        if p in df.columns and p not in keep_cols:
            keep_cols.append(p)
    df = df[keep_cols].sort_values(["location_id", "date"]).reset_index(drop=True)
    print(f"[SUCCESS] Burned Area: {len(df)} rows across {len(meta_by_id)} polygon(s).")
    return df
