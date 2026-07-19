"""
Land-degradation indicators (fire family).

Phase 5a: MODIS Burned Area (MCD64A1) per-polygon monthly time series.
Phase 5b: FIRMS Active Fires per-polygon monthly aggregate.

MCD64A1 answers "how much area burned last month" (post-hoc, ~60-90
day latency). FIRMS answers "how much active-fire activity is
happening now" (near-real-time, ~3-hour latency). Combining them in
one source lets users pick either / both in a single fetch.

References:
  Giglio, L. et al. (2018), "The Collection 6 MODIS burned area
  mapping algorithm and product." Remote Sensing of Environment 217.
  Justice, C. et al. (2002), "The MODIS fire products." RSE 83.

Data:
  MODIS/061/MCD64A1   Monthly burned area, 500 m, Nov 2000 -> present.
      BurnDate band:
        positive int  day-of-year the pixel burned in this month
        0             not burned
        -1            unclassified
        -2            water
  FIRMS               Fire Information for Resource Management System,
                      1 km daily fire detections, 2000-11 -> present.
      T21          brightness temperature at fire pixels (K)
      confidence   0-100 detection confidence

Output slots into the weather schema: (date, latitude, longitude,
location_id, polygon_name, <requested params>). The polygon centroid
is emitted as latitude / longitude so the standard weather display
and export path works without additional branching.
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
    "Active Fires (FIRMS)": {
        "FIRE_DETECTIONS": "Monthly count of fire pixel-days",
        "MEAN_BRIGHTNESS_K": "Mean brightness temperature at fire pixels (K)",
        "MEAN_CONFIDENCE": "Mean detection confidence (0-100)",
    },
}

_BURNED_AREA_PARAM_KEYS = {"BURNED_AREA_KM2", "PERCENT_BURNED"}
_FIRMS_PARAM_KEYS = {"FIRE_DETECTIONS", "MEAN_BRIGHTNESS_K", "MEAN_CONFIDENCE"}

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

def _monthly_iter(start_dt: datetime, end_dt: datetime):
    """Yield (year, month) first-of-month datetimes covering the range."""
    cur = start_dt.replace(day=1)
    end_month = end_dt.replace(day=1)
    while cur <= end_month:
        yield cur
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)


def _compute_burned_area_frame(
    fc, meta_by_id: Dict[int, Dict],
    start_dt: datetime, end_dt: datetime, scale_m: int,
) -> pd.DataFrame:
    """Monthly burned-area rows from MCD64A1. Returns columns
    (date, latitude, longitude, location_id, polygon_name,
    BURNED_AREA_KM2, PERCENT_BURNED)."""
    pixel_area = ee.Image.pixelArea()

    # Total polygon area computed once — independent of month.
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
    print(
        f"[BurnedArea] {len(meta_by_id)} polygon(s)  "
        f"{start_dt.date()}..{end_dt.date()}  MCD64A1 @ {scale_m} m"
    )

    for cur in _monthly_iter(start_dt, end_dt):
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

        # Zero rows for polygons that didn't come back this month keep the
        # per-location time series contiguous.
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

    return pd.DataFrame(rows)


def _compute_firms_frame(
    fc, meta_by_id: Dict[int, Dict],
    start_dt: datetime, end_dt: datetime, scale_m: int = 1000,
) -> pd.DataFrame:
    """Monthly FIRMS aggregate rows. Returns columns (date, latitude,
    longitude, location_id, polygon_name, FIRE_DETECTIONS,
    MEAN_BRIGHTNESS_K, MEAN_CONFIDENCE)."""
    coll = ee.ImageCollection("FIRMS").select(["T21", "confidence"])

    rows: List[Dict] = []
    print(
        f"[FIRMS] {len(meta_by_id)} polygon(s)  "
        f"{start_dt.date()}..{end_dt.date()}  FIRMS @ {scale_m} m"
    )

    for cur in _monthly_iter(start_dt, end_dt):
        m_start = ee.Date.fromYMD(cur.year, cur.month, 1)
        m_end = m_start.advance(1, "month")
        m_coll = coll.filterDate(m_start, m_end)

        try:
            n_imgs = m_coll.size().getInfo()
        except Exception as e:
            print(f"[WARN] FIRMS {cur.year}-{cur.month:02d} size: {e}")
            n_imgs = 0

        server_feats: List = []
        if n_imgs > 0:
            # Fire pixel = T21 > 0. For each daily image, build a small
            # multi-band image whose sum-reduction yields
            #   count of fire pixels, sum of brightness at those pixels,
            #   sum of confidence at those pixels
            # Then sum the daily images to get the monthly totals.
            def per_image(img):
                mask = img.select("T21").gt(0)
                return ee.Image.cat([
                    mask.rename("fire_count"),
                    img.select("T21").multiply(mask).rename("bright_sum"),
                    img.select("confidence").multiply(mask).rename("conf_sum"),
                ])

            monthly_img = m_coll.map(per_image).sum()
            try:
                reduced = monthly_img.reduceRegions(
                    collection=fc,
                    reducer=ee.Reducer.sum(),
                    scale=scale_m,
                    tileScale=4,
                )
                server_feats = reduced.getInfo().get("features", [])
            except Exception as e:
                print(f"[WARN] FIRMS {cur.year}-{cur.month:02d} reduce: {e}")

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
            n_fire = float(props.get("fire_count") or 0.0)
            bright_sum = float(props.get("bright_sum") or 0.0)
            conf_sum = float(props.get("conf_sum") or 0.0)
            mean_bright = (bright_sum / n_fire) if n_fire > 0 else None
            mean_conf = (conf_sum / n_fire) if n_fire > 0 else None
            rows.append({
                "date": pd.Timestamp(year=cur.year, month=cur.month, day=1),
                "latitude": m["latitude"],
                "longitude": m["longitude"],
                "location_id": pid,
                "polygon_name": m["polygon_name"],
                "FIRE_DETECTIONS": int(round(n_fire)),
                "MEAN_BRIGHTNESS_K": round(mean_bright, 2) if mean_bright else None,
                "MEAN_CONFIDENCE": round(mean_conf, 1) if mean_conf else None,
            })

        # Zero rows keep the time series contiguous.
        for pid, m in meta_by_id.items():
            if pid in got_ids:
                continue
            rows.append({
                "date": pd.Timestamp(year=cur.year, month=cur.month, day=1),
                "latitude": m["latitude"],
                "longitude": m["longitude"],
                "location_id": pid,
                "polygon_name": m["polygon_name"],
                "FIRE_DETECTIONS": 0,
                "MEAN_BRIGHTNESS_K": None,
                "MEAN_CONFIDENCE": None,
            })

    return pd.DataFrame(rows)


def fetch_burned_area_from_gdf(
    aoi_gdf: gpd.GeoDataFrame,
    parameters: List[str],
    start_date: str,
    end_date: str,
    credentials_dict: Dict,
    scale_m: int = 500,
) -> pd.DataFrame:
    """Monthly fire time series per AOI polygon.

    Dispatches on the requested parameters: MCD64A1 burned-area
    parameters trigger the burned-area frame; FIRMS parameters trigger
    the FIRMS frame. Both frames are merged on (location_id, date) so
    users can request either family or a mix in one fetch.
    """
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

    need_burned = any(p in _BURNED_AREA_PARAM_KEYS for p in parameters)
    need_firms = any(p in _FIRMS_PARAM_KEYS for p in parameters)

    burned_frame = pd.DataFrame()
    firms_frame = pd.DataFrame()
    if need_burned:
        burned_frame = _compute_burned_area_frame(fc, meta_by_id, start_dt, end_dt, scale_m)
    if need_firms:
        firms_frame = _compute_firms_frame(fc, meta_by_id, start_dt, end_dt)

    if burned_frame.empty and firms_frame.empty:
        return pd.DataFrame()
    if burned_frame.empty:
        combined = firms_frame
    elif firms_frame.empty:
        combined = burned_frame
    else:
        firms_slim = firms_frame[[
            "location_id", "date",
            "FIRE_DETECTIONS", "MEAN_BRIGHTNESS_K", "MEAN_CONFIDENCE",
        ]]
        combined = burned_frame.merge(
            firms_slim, on=["location_id", "date"], how="outer",
        )

    keep_cols = ["date", "latitude", "longitude", "location_id", "polygon_name"]
    for p in parameters:
        if p in combined.columns and p not in keep_cols:
            keep_cols.append(p)
    combined = combined[keep_cols].sort_values(
        ["location_id", "date"]
    ).reset_index(drop=True)
    print(
        f"[SUCCESS] Fire: {len(combined)} rows across "
        f"{len(meta_by_id)} polygon(s), params={parameters}."
    )
    return combined
