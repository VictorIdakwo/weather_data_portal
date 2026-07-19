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
    "Forest loss (Hansen Global Forest Change)": {
        "TREE_LOSS_KM2": "Annual tree-cover loss (km²)",
        "PERCENT_LOSS": "Loss as percent of polygon (%)",
        "FOREST_2000_KM2": "Year-2000 forest baseline area (km², >30 % tree cover)",
        "PERCENT_FOREST_2000": "Year-2000 forest as percent of polygon (%)",
    },
}

_BURNED_AREA_PARAM_KEYS = {"BURNED_AREA_KM2", "PERCENT_BURNED"}
_FIRMS_PARAM_KEYS = {"FIRE_DETECTIONS", "MEAN_BRIGHTNESS_K", "MEAN_CONFIDENCE"}
_HANSEN_PARAM_KEYS = {
    "TREE_LOSS_KM2", "PERCENT_LOSS", "FOREST_2000_KM2", "PERCENT_FOREST_2000",
}

# Hansen v1.12 covers loss years 2001 - 2024. Bump this when the annual
# release is refreshed.
HANSEN_ASSET = "UMD/hansen/global_forest_change_2025_v1_13"
HANSEN_MIN_YEAR = 2001
HANSEN_MAX_YEAR = 2025
HANSEN_TREECOVER_THRESHOLD_PCT = 30  # Standard "forest" definition

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


def _compute_hansen_frame(
    fc, meta_by_id: Dict[int, Dict],
    start_dt: datetime, end_dt: datetime, scale_m: int = 30,
) -> pd.DataFrame:
    """Annual tree-cover loss rows from Hansen. Returns columns
    (date, latitude, longitude, location_id, polygon_name,
    TREE_LOSS_KM2, PERCENT_LOSS, FOREST_2000_KM2, PERCENT_FOREST_2000).

    Hansen is a single static image with bands:
      treecover2000  0-100 percent canopy cover in year 2000
      lossyear       1-24 (year - 2000) of loss detection; 0 = no loss
      loss           binary mask of ever-lost pixels

    Method: build 25 masks (one per loss year) plus a treecover2000>30
    forest baseline mask, cat them into one image, sum-reduce per
    polygon in TWO calls (one for the year-invariant baseline and
    total area, one for the per-year loss counts).
    """
    hansen = ee.Image(HANSEN_ASSET)
    lossyear = hansen.select("lossyear")
    treecover = hansen.select("treecover2000")
    pixel_area = ee.Image.pixelArea()

    # -- Baseline + total area (single reduceRegions) ----------------------
    forest_mask = treecover.gte(HANSEN_TREECOVER_THRESHOLD_PCT)
    baseline_img = ee.Image.cat([
        pixel_area.rename("total_area_m2"),
        pixel_area.multiply(forest_mask).rename("forest_2000_m2"),
    ])
    try:
        baseline_reduced = baseline_img.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.sum(),
            scale=scale_m,
            tileScale=4,
        )
        baseline_feats = baseline_reduced.getInfo().get("features", [])
    except Exception as e:
        raise RuntimeError(f"Earth Engine Hansen baseline query failed: {e}") from e

    total_by_id: Dict[int, float] = {}
    forest_by_id: Dict[int, float] = {}
    for feat in baseline_feats:
        props = feat.get("properties") or {}
        try:
            pid = int(props.get("polygon_id"))
        except (TypeError, ValueError):
            continue
        total_by_id[pid] = float(props.get("total_area_m2") or 0.0)
        forest_by_id[pid] = float(props.get("forest_2000_m2") or 0.0)

    # -- Per-year loss (single reduceRegions with a multi-band image) ------
    y_from = max(HANSEN_MIN_YEAR, start_dt.year)
    y_to = min(HANSEN_MAX_YEAR, end_dt.year)
    if y_from > y_to:
        return pd.DataFrame()

    years = list(range(y_from, y_to + 1))
    band_imgs = []
    for y in years:
        # Hansen encodes lossyear as (year - 2000), so 2001 -> 1, 2024 -> 24.
        code = y - 2000
        mask = lossyear.eq(code)
        band_imgs.append(pixel_area.multiply(mask).rename(f"loss_{y}_m2"))
    loss_img = ee.Image.cat(band_imgs)

    try:
        loss_reduced = loss_img.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.sum(),
            scale=scale_m,
            tileScale=4,
        )
        loss_feats = loss_reduced.getInfo().get("features", [])
    except Exception as e:
        raise RuntimeError(f"Earth Engine Hansen loss query failed: {e}") from e

    loss_by_polygon_year: Dict[Tuple[int, int], float] = {}
    for feat in loss_feats:
        props = feat.get("properties") or {}
        try:
            pid = int(props.get("polygon_id"))
        except (TypeError, ValueError):
            continue
        for y in years:
            loss_by_polygon_year[(pid, y)] = float(
                props.get(f"loss_{y}_m2") or 0.0
            )

    print(
        f"[Hansen] {len(meta_by_id)} polygon(s)  loss years "
        f"{y_from}-{y_to}  @ {scale_m} m"
    )

    rows: List[Dict] = []
    for pid, m in meta_by_id.items():
        total_m2 = total_by_id.get(pid, 0.0)
        forest_m2 = forest_by_id.get(pid, 0.0)
        forest_km2 = round(forest_m2 / 1_000_000.0, 4)
        forest_pct = round(forest_m2 / total_m2 * 100.0, 3) if total_m2 > 0 else 0.0
        for y in years:
            loss_m2 = loss_by_polygon_year.get((pid, y), 0.0)
            loss_km2 = round(loss_m2 / 1_000_000.0, 4)
            loss_pct = round(loss_m2 / total_m2 * 100.0, 4) if total_m2 > 0 else 0.0
            rows.append({
                "date": pd.Timestamp(year=y, month=1, day=1),
                "latitude": m["latitude"],
                "longitude": m["longitude"],
                "location_id": pid,
                "polygon_name": m["polygon_name"],
                "TREE_LOSS_KM2": loss_km2,
                "PERCENT_LOSS": loss_pct,
                "FOREST_2000_KM2": forest_km2,
                "PERCENT_FOREST_2000": forest_pct,
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
    need_hansen = any(p in _HANSEN_PARAM_KEYS for p in parameters)

    burned_frame = pd.DataFrame()
    firms_frame = pd.DataFrame()
    hansen_frame = pd.DataFrame()
    if need_burned:
        burned_frame = _compute_burned_area_frame(fc, meta_by_id, start_dt, end_dt, scale_m)
    if need_firms:
        firms_frame = _compute_firms_frame(fc, meta_by_id, start_dt, end_dt)
    if need_hansen:
        hansen_frame = _compute_hansen_frame(fc, meta_by_id, start_dt, end_dt)

    non_empty = [f for f in (burned_frame, firms_frame, hansen_frame) if not f.empty]
    if not non_empty:
        return pd.DataFrame()

    # Merge one at a time on (location_id, date). Hansen is annual (Jan 1
    # of each year), fire products are monthly (first-of-month). Outer join
    # keeps both cadences visible in the merged output; users pick the
    # cadence they want via the requested parameters.
    combined = non_empty[0]
    for frame in non_empty[1:]:
        keep_extra_cols = [
            c for c in frame.columns
            if c not in ("date", "latitude", "longitude", "location_id", "polygon_name")
        ]
        combined = combined.merge(
            frame[["location_id", "date"] + keep_extra_cols],
            on=["location_id", "date"], how="outer",
        )
    # After outer join we may lose latitude/longitude for date rows that
    # only appear in one side. Restore from any non-empty frame.
    for col in ("latitude", "longitude", "polygon_name"):
        if col not in combined.columns:
            combined[col] = None
        for src in non_empty:
            if col not in src.columns:
                continue
            lookup = src.set_index(["location_id", "date"])[col].to_dict()
            mask = combined[col].isna()
            if mask.any():
                combined.loc[mask, col] = combined.loc[mask].apply(
                    lambda r: lookup.get((r["location_id"], r["date"]), None),
                    axis=1,
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
