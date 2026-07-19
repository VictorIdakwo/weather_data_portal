"""
Vegetation productivity — MODIS + PML_V2.

Monthly per-location time series covering three complementary
productivity families:

  Structure     LAI, FAPAR       from MODIS MOD15A2H (8-day)
  Water flux    ET, PET          from MODIS MOD16A2 gap-filled (8-day)
  Carbon flux   GPP              from PML_V2 (8-day)

For LAI / FAPAR the monthly value is the mean of the 8-day composites
covering the month. For ET / PET / GPP the monthly value is the SUM
of the 8-day composite values (rescaled to mm/month or gC/m²/month),
since those quantities are already accumulations over their reporting
window.

References:
  Myneni, R. et al. (2015) MOD15 LAI/FPAR user guide.
  Running, S. et al. (2019) MOD16 evapotranspiration user guide.
  Zhang, Y. et al. (2019) Coupled estimation of 500 m and 8-day
    resolution global evapotranspiration and gross primary production
    in 2002-2017. Remote Sensing of Environment 222.

Data:
  MODIS/061/MOD15A2H            LAI + FPAR, 500 m, 8-day, 2002-07 -> present
  MODIS/061/MOD16A2GF           gap-filled ET, 500 m, 8-day, 2001-01 -> present
  CAS/IGSNRR/PML/V2_v018        PML_V2 GPP, 500 m, 8-day, 2000-02 -> present

Output slots into the weather schema (date, latitude, longitude,
location_id, <requested params>) so the standard display and CSV /
JSON / Excel exports work without any new branching.
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

PRODUCTIVITY_PARAMETERS: Dict[str, Dict[str, str]] = {
    "Vegetation structure (MOD15A2H)": {
        "LAI_M2M2": "Leaf Area Index (m^2/m^2, monthly mean)",
        "FAPAR": "Fraction of Absorbed PAR (0-1, monthly mean)",
    },
    "Evapotranspiration (MOD16A2)": {
        "ET_MM": "Actual evapotranspiration (mm/month, gap-filled)",
        "PET_MM_MODIS": "Potential evapotranspiration (mm/month, gap-filled)",
    },
    "Carbon flux (PML_V2)": {
        "GPP_GC_M2": "Gross Primary Productivity (gC/m^2/month)",
    },
}

TEMPORAL_RESOLUTIONS = ["Monthly"]

# Individual band metadata. EE does NOT auto-scale MODIS values in the
# reduceRegions path — the docs "This dataset has been transformed" only
# applies to the visualisation defaults, not the raw sampled values. So
# the documented per-band scale factors have to be applied here to get
# physical units back.
#
# aggregation: "mean" for structural bands (LAI, FAPAR), "sum" for
# accumulated fluxes (ET, PET, GPP composites).
_PARAM_META: Dict[str, Dict] = {
    "LAI_M2M2": {
        "asset": "MODIS/061/MOD15A2H", "band": "Lai_500m",
        "scale_m": 500, "aggregation": "mean", "value_scale": 0.1,
    },
    "FAPAR": {
        "asset": "MODIS/061/MOD15A2H", "band": "Fpar_500m",
        "scale_m": 500, "aggregation": "mean", "value_scale": 0.01,
    },
    "ET_MM": {
        "asset": "MODIS/061/MOD16A2GF", "band": "ET",
        "scale_m": 500, "aggregation": "sum", "value_scale": 0.1,
    },
    "PET_MM_MODIS": {
        "asset": "MODIS/061/MOD16A2GF", "band": "PET",
        "scale_m": 500, "aggregation": "sum", "value_scale": 0.1,
    },
    "GPP_GC_M2": {
        # PML_V2 GPP is already stored as gC/m^2/day (no MODIS-style
        # int scale factor). Sum of 8-day composite values * 8 (days
        # per composite) = monthly total in gC/m^2.
        "asset": "CAS/IGSNRR/PML/V2_v018", "band": "GPP",
        "scale_m": 500, "aggregation": "sum", "value_scale": 8.0,
    },
}


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    return PRODUCTIVITY_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    return TEMPORAL_RESOLUTIONS


# ---------------------------------------------------------------------------
# Generic monthly fetcher (mean or sum aggregation)
# ---------------------------------------------------------------------------

def _monthly_ee_series(
    locations: List[Tuple[float, float]],
    asset_id: str,
    band: str,
    out_field: str,
    scale_m: int,
    aggregation: str,
    value_scale: float,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Batched monthly fetcher over any EE ImageCollection band.

    aggregation:
        'mean' - reduce the collection with .mean() before sampling
                 (correct for structural variables like LAI / FAPAR).
        'sum'  - reduce with .sum() before sampling
                 (correct for accumulated fluxes like ET / GPP).
    value_scale multiplies the sampled value before it hits the DataFrame,
    turning raw scaled ints into their physical units.
    """
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
            m_coll = coll.filterDate(m_start, m_end)

            if aggregation == "mean":
                monthly_img = m_coll.mean().rename(band)
            elif aggregation == "sum":
                monthly_img = m_coll.sum().rename(band)
            else:
                raise ValueError(f"Unknown aggregation: {aggregation}")

            try:
                reduced = monthly_img.reduceRegions(
                    collection=fc,
                    reducer=ee.Reducer.mean().setOutputs([out_field]),
                    scale=scale_m,
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

    df = pd.DataFrame(rows)
    return df.sort_values(["location_id", "year", "month"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Public fetch entry point
# ---------------------------------------------------------------------------

def fetch_productivity_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    credentials_dict: Dict,
) -> pd.DataFrame:
    """Fetch monthly vegetation-productivity time series per location.

    Weather-schema compatible: (date, latitude, longitude, location_id,
    <requested params>).
    """
    if temporal_resolution and temporal_resolution.lower() != "monthly":
        raise ValueError(
            "Vegetation productivity is aggregated to monthly. "
            "Select 'Monthly' as the temporal resolution."
        )
    if not parameters:
        raise ValueError("No parameters requested.")

    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    fetch_start_year = start_dt.year
    fetch_end_year = end_dt.year

    print(
        f"[Productivity] Locations={len(locations)}  "
        f"target={start_dt.date()}..{end_dt.date()}  "
        f"pulling {fetch_start_year}-{fetch_end_year}  "
        f"params={parameters}"
    )

    # One EE query per requested parameter — each hits a different band
    # (and often a different asset). Merge on (location_id, year, month).
    frames_by_loc: Dict[int, pd.DataFrame] = {}
    for p in parameters:
        meta = _PARAM_META.get(p)
        if meta is None:
            continue
        raw_df = _monthly_ee_series(
            locations=locations,
            asset_id=meta["asset"],
            band=meta["band"],
            out_field=p,
            scale_m=meta["scale_m"],
            aggregation=meta["aggregation"],
            value_scale=meta["value_scale"],
            start_year=fetch_start_year,
            end_year=fetch_end_year,
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

    result = pd.concat(out_frames, ignore_index=True)
    result = result.sort_values(["location_id", "date"]).reset_index(drop=True)
    print(f"[SUCCESS] Productivity: {len(result)} rows across {len(locations)} location(s).")
    return result
