"""
Air-quality point time series from Sentinel-5P TROPOMI + MODIS AOD.

Phase 10 delivers monthly per-location values for:

  Sentinel-5P TROPOMI (7 km native, Sept 2018 -> present):
    NO2, SO2, CO, CH4  - tropospheric column densities in mol/m^2
                          (raw EE units; multiply by 6.02e23 for
                          molecules/cm^2 if you need Dobson-style
                          quantities)

  MODIS Terra AOD (MOD11A2 / MCD19A2, 1 km, daily):
    AOD_550NM  - Aerosol Optical Depth at 550 nm (0..1+, higher =
                 more atmospheric particulate)

Output is weather-schema: (date, latitude, longitude, location_id,
<requested params>).
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

import ee
import numpy as np
import pandas as pd

from .earth_engine_utils import EarthEngineClient


AIR_QUALITY_PARAMETERS: Dict[str, Dict[str, str]] = {
    "TROPOMI (Sentinel-5P) trace gases": {
        "NO2":  "Nitrogen Dioxide tropospheric column (mol/m^2)",
        "SO2":  "Sulfur Dioxide column (mol/m^2)",
        "CO":   "Carbon Monoxide column (mol/m^2)",
        "CH4":  "Methane column (ppb)",
    },
    "MODIS aerosol": {
        "AOD_550NM": "MODIS Aerosol Optical Depth at 550 nm (unitless)",
    },
}

TEMPORAL_RESOLUTIONS = ["Monthly"]

# Band metadata: EE asset, band, scale, value_scale
_PARAM_META: Dict[str, Dict] = {
    "NO2":  {"asset": "COPERNICUS/S5P/OFFL/L3_NO2",  "band": "tropospheric_NO2_column_number_density", "scale_m": 7000, "value_scale": 1.0},
    "SO2":  {"asset": "COPERNICUS/S5P/OFFL/L3_SO2",  "band": "SO2_column_number_density",              "scale_m": 7000, "value_scale": 1.0},
    "CO":   {"asset": "COPERNICUS/S5P/OFFL/L3_CO",   "band": "CO_column_number_density",               "scale_m": 7000, "value_scale": 1.0},
    "CH4":  {"asset": "COPERNICUS/S5P/OFFL/L3_CH4",  "band": "CH4_column_volume_mixing_ratio_dry_air", "scale_m": 7000, "value_scale": 1.0},
    "AOD_550NM": {"asset": "MODIS/061/MCD19A2_GRANULES", "band": "Optical_Depth_055", "scale_m": 1000, "value_scale": 0.001},
}


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    return AIR_QUALITY_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    return TEMPORAL_RESOLUTIONS


def _monthly_series(
    locations: List[Tuple[float, float]],
    asset_id: str,
    band: str,
    out_field: str,
    scale_m: int,
    value_scale: float,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Batched monthly-mean fetcher matching the shape of the drought /
    productivity code paths."""
    coll = ee.ImageCollection(asset_id).select(band)

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
                    scale=scale_m,
                    tileScale=4,
                )
                server_feats = reduced.getInfo().get("features", [])
            except Exception as e:
                print(f"[WARN] {asset_id} {year}-{month:02d}: {e}")
                continue
            for feat in server_feats:
                props = feat.get("properties") or {}
                raw = props.get(out_field)
                if raw is None:
                    v = np.nan
                else:
                    try:
                        v = float(raw) * value_scale
                    except (TypeError, ValueError):
                        v = np.nan
                rows.append({
                    "location_id": int(props.get("location_id", -1)),
                    "latitude": props.get("latitude"),
                    "longitude": props.get("longitude"),
                    "year": year,
                    "month": month,
                    out_field: v,
                })

    if not rows:
        return pd.DataFrame(columns=[
            "location_id", "latitude", "longitude", "year", "month", out_field,
        ])
    return pd.DataFrame(rows).sort_values(["location_id", "year", "month"]).reset_index(drop=True)


def fetch_air_quality_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    credentials_dict: Dict,
) -> pd.DataFrame:
    """Fetch monthly air-quality time series per location."""
    if temporal_resolution and temporal_resolution.lower() != "monthly":
        raise ValueError("Air quality is aggregated to monthly.")
    if not parameters:
        raise ValueError("No parameters requested.")

    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    frames_by_loc: Dict[int, pd.DataFrame] = {}
    for p in parameters:
        meta = _PARAM_META.get(p)
        if meta is None:
            continue
        raw_df = _monthly_series(
            locations=locations,
            asset_id=meta["asset"],
            band=meta["band"],
            out_field=p,
            scale_m=meta["scale_m"],
            value_scale=meta["value_scale"],
            start_year=start_dt.year,
            end_year=end_dt.year,
        )
        if raw_df.empty:
            continue
        for loc_id, loc_df in raw_df.groupby("location_id"):
            loc_id = int(loc_id)
            existing = frames_by_loc.get(loc_id)
            if existing is None:
                frames_by_loc[loc_id] = loc_df.copy()
            else:
                existing = existing.merge(
                    loc_df[["location_id", "year", "month", p]],
                    on=["location_id", "year", "month"],
                    how="outer",
                )
                frames_by_loc[loc_id] = existing

    if not frames_by_loc:
        return pd.DataFrame()

    out_frames: List[pd.DataFrame] = []
    for loc_df in frames_by_loc.values():
        loc_df = loc_df.sort_values(["year", "month"]).reset_index(drop=True)
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
    return pd.concat(out_frames, ignore_index=True).sort_values(
        ["location_id", "date"]
    ).reset_index(drop=True)
