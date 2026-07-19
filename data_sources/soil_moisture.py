"""
Soil moisture from NASA SMAP.

Uses SMAP L4 Global 3-Hourly 9 km Soil Moisture (SPL4SMGP v7) aggregated
to monthly means, delivering both the surface (0-5 cm) and root-zone
(0-100 cm) layers.

Reference:
  Reichle, R. et al. (2019), "SMAP L4 9 km EASE-Grid Surface and Root
  Zone Soil Moisture Analysis Update". NSIDC.

Data:
  NASA/SMAP/SPL4SMGP/008
    sm_surface   0-5 cm soil moisture (m^3/m^3)
    sm_rootzone  0-100 cm root-zone soil moisture (m^3/m^3)
  ~9 km, 3-hourly, 2015-04 -> present.

Output slots into the weather schema: (date, latitude, longitude,
location_id, <requested params>). Anomalies are computed against the
2015-2024 per-calendar-month climatology (default baseline; extended
whenever SMAP produces a longer record).
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

import ee
import numpy as np
import pandas as pd

from .earth_engine_utils import EarthEngineClient


# ---------------------------------------------------------------------------
# Parameter registry
# ---------------------------------------------------------------------------

SMAP_PARAMETERS: Dict[str, Dict[str, str]] = {
    "Soil Moisture (SMAP L4)": {
        "SM_SURFACE": "Surface soil moisture (0-5 cm, m^3/m^3)",
        "SM_ROOTZONE": "Root-zone soil moisture (0-100 cm, m^3/m^3)",
    },
    "Anomalies": {
        "SM_SURFACE_ANOM": "Surface soil moisture anomaly (vs 2015-2024 mean)",
        "SM_ROOTZONE_ANOM": "Root-zone soil moisture anomaly (vs 2015-2024 mean)",
    },
}

TEMPORAL_RESOLUTIONS = ["Monthly"]

# Baseline used for the per-calendar-month climatology.
BASELINE_START = 2015
BASELINE_END = 2024


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    return SMAP_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    return TEMPORAL_RESOLUTIONS


# ---------------------------------------------------------------------------
# Monthly aggregation via Earth Engine
# ---------------------------------------------------------------------------

def _monthly_smap_series(
    locations: List[Tuple[float, float]],
    band: str,
    out_field: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Batched monthly-mean fetcher for one SMAP band. One reduceRegions
    call per (year, month) covers every input location."""
    coll = ee.ImageCollection("NASA/SMAP/SPL4SMGP/008").select(band)

    feats = []
    for idx, (lat, lon) in enumerate(locations):
        pt = ee.Geometry.Point([lon, lat])
        feats.append(ee.Feature(pt, {
            "location_id": int(idx),
            "latitude": float(lat),
            "longitude": float(lon),
        }))
    fc = ee.FeatureCollection(feats)

    rows: List[Dict] = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            m_start = ee.Date.fromYMD(year, month, 1)
            m_end = m_start.advance(1, "month")
            monthly_img = coll.filterDate(m_start, m_end).mean().rename(band)

            try:
                reduced = monthly_img.reduceRegions(
                    collection=fc,
                    reducer=ee.Reducer.mean().setOutputs([out_field]),
                    scale=11000,  # SMAP native ~9 km; 11 km gives safety
                )
                server_feats = reduced.getInfo().get("features", [])
            except Exception as e:
                print(f"[WARN] SMAP {band} {year}-{month:02d}: {e}")
                continue

            for feat in server_feats:
                props = feat.get("properties") or {}
                val = props.get(out_field)
                if val is None:
                    sm = np.nan
                else:
                    try:
                        sm = float(val)
                    except (TypeError, ValueError):
                        sm = np.nan
                rows.append({
                    "location_id": int(props.get("location_id", -1)),
                    "latitude": props.get("latitude"),
                    "longitude": props.get("longitude"),
                    "year": year,
                    "month": month,
                    out_field: sm,
                })

    if not rows:
        return pd.DataFrame(columns=[
            "location_id", "latitude", "longitude", "year", "month", out_field,
        ])

    df = pd.DataFrame(rows)
    return df.sort_values(["location_id", "year", "month"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Public fetch entry point (weather-schema compatible)
# ---------------------------------------------------------------------------

def fetch_smap_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    credentials_dict: Dict,
) -> pd.DataFrame:
    """Fetch monthly SMAP soil moisture per location.

    Returns a DataFrame with columns (date, latitude, longitude,
    location_id, <requested params>). Weather-schema compatible.

    Args:
        locations: [(lat, lon), ...]
        parameters: subset of SM_SURFACE / SM_ROOTZONE plus anomalies.
        start_date, end_date: 'YYYY-MM-DD' strings (only year/month matters).
        temporal_resolution: 'Monthly' (only supported).
        credentials_dict: EE service account credentials.
    """
    if temporal_resolution and temporal_resolution.lower() != "monthly":
        raise ValueError(
            "SMAP soil moisture is aggregated to monthly means. "
            "Select 'Monthly' as the temporal resolution."
        )
    if not parameters:
        raise ValueError("No parameters requested.")

    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    need_anom = any("_ANOM" in p for p in parameters)
    if need_anom:
        fetch_start_year = min(BASELINE_START, start_dt.year)
        fetch_end_year = max(BASELINE_END, end_dt.year)
    else:
        fetch_start_year = start_dt.year
        fetch_end_year = end_dt.year

    want_surface = any(p.startswith("SM_SURFACE") for p in parameters)
    want_rootzone = any(p.startswith("SM_ROOTZONE") for p in parameters)

    print(
        f"[SMAP] Locations={len(locations)}  "
        f"target={start_dt.date()}..{end_dt.date()}  "
        f"pulling {fetch_start_year}-{fetch_end_year}  "
        f"(surface={want_surface}, rootzone={want_rootzone})"
    )

    frames_by_loc: Dict[int, pd.DataFrame] = {}

    if want_surface:
        sm_s = _monthly_smap_series(
            locations, "sm_surface", "sm_surface_raw",
            fetch_start_year, fetch_end_year,
        )
        for loc_id, loc_df in sm_s.groupby("location_id"):
            frames_by_loc[int(loc_id)] = loc_df.copy()

    if want_rootzone:
        sm_rz = _monthly_smap_series(
            locations, "sm_rootzone", "sm_rootzone_raw",
            fetch_start_year, fetch_end_year,
        )
        for loc_id, loc_df in sm_rz.groupby("location_id"):
            loc_id = int(loc_id)
            existing = frames_by_loc.get(loc_id)
            if existing is None:
                frames_by_loc[loc_id] = loc_df.copy()
            else:
                merged = existing.merge(
                    loc_df[["location_id", "year", "month", "sm_rootzone_raw"]],
                    on=["location_id", "year", "month"],
                    how="outer",
                )
                frames_by_loc[loc_id] = merged

    if not frames_by_loc:
        return pd.DataFrame()

    out_frames: List[pd.DataFrame] = []
    for loc_id, loc_df in frames_by_loc.items():
        loc_df = loc_df.sort_values(["year", "month"]).reset_index(drop=True)

        # Anomalies against the baseline monthly climatology (per calendar month).
        baseline = loc_df[
            (loc_df["year"] >= BASELINE_START) & (loc_df["year"] <= BASELINE_END)
        ]
        if "SM_SURFACE_ANOM" in parameters and "sm_surface_raw" in loc_df.columns:
            clim = baseline.groupby("month")["sm_surface_raw"].mean().to_dict()
            loc_df["SM_SURFACE_ANOM"] = (
                loc_df["sm_surface_raw"] - loc_df["month"].map(clim)
            )
        if "SM_ROOTZONE_ANOM" in parameters and "sm_rootzone_raw" in loc_df.columns:
            clim = baseline.groupby("month")["sm_rootzone_raw"].mean().to_dict()
            loc_df["SM_ROOTZONE_ANOM"] = (
                loc_df["sm_rootzone_raw"] - loc_df["month"].map(clim)
            )

        # Rename the raw columns to the public parameter names for the output.
        if "SM_SURFACE" in parameters and "sm_surface_raw" in loc_df.columns:
            loc_df["SM_SURFACE"] = loc_df["sm_surface_raw"]
        if "SM_ROOTZONE" in parameters and "sm_rootzone_raw" in loc_df.columns:
            loc_df["SM_ROOTZONE"] = loc_df["sm_rootzone_raw"]

        loc_df["date"] = pd.to_datetime(
            loc_df["year"].astype(str) + "-"
            + loc_df["month"].astype(str).str.zfill(2) + "-01"
        )
        mask = (loc_df["date"] >= start_dt) & (loc_df["date"] <= end_dt)
        loc_df = loc_df.loc[mask].copy()

        keep = ["date", "latitude", "longitude", "location_id"]
        for p in parameters:
            if p in loc_df.columns and p not in keep:
                keep.append(p)
        out_frames.append(loc_df[keep])

    if not out_frames:
        return pd.DataFrame()

    result = pd.concat(out_frames, ignore_index=True)
    result = result.sort_values(["location_id", "date"]).reset_index(drop=True)
    print(f"[SUCCESS] SMAP: {len(result)} rows across {len(locations)} location(s).")
    return result
