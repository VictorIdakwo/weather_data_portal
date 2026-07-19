"""
Drought & vegetation-health indices.

Phase 2a: SPI (Standardized Precipitation Index) from CHIRPS.

SPI compresses a rolling precipitation total into a z-score against a
long-term climatology fit with a two-parameter gamma distribution.
McKee et al. (1993) is the canonical reference; the WMO endorses this
family of indices for operational drought monitoring.

Interpretation:
    SPI >= +2.0   Extremely wet
    +1.5 to +2.0  Severely wet
    +1.0 to +1.5  Moderately wet
    -1.0 to +1.0  Near normal
    -1.5 to -1.0  Moderate drought
    -2.0 to -1.5  Severe drought
    SPI <  -2.0   Extreme drought

Data:
    CHIRPS Daily v2.0 (UCSB-CHG/CHIRPS/DAILY) on Earth Engine.
    ~5.5 km resolution, 1981-01-01 -> ~5 days ago, 50S-50N.
    Uses the existing service-account credentials.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple, Optional

import ee
import numpy as np
import pandas as pd
from scipy import stats

from .earth_engine_utils import EarthEngineClient


# ---------------------------------------------------------------------------
# Parameter registry (matches the shape used by NASA POWER, ERA5, etc.)
# ---------------------------------------------------------------------------

SPI_PARAMETERS: Dict[str, Dict[str, str]] = {
    "Drought (SPI)": {
        "SPI_1": "SPI-1 (1-month drought / wetness)",
        "SPI_3": "SPI-3 (3-month drought / wetness, seasonal)",
        "SPI_6": "SPI-6 (6-month drought / wetness, medium-term)",
        "SPI_12": "SPI-12 (12-month drought / wetness, long-term)",
    },
    "Precipitation": {
        # Handy raw inputs to eyeball alongside the indices.
        "PRECIP_MM": "Monthly precipitation (mm)",
        "PRECIP_ANOM_MM": "Monthly precipitation anomaly (mm vs 1991-2020 mean)",
    },
}

# SPI is defined on monthly totals; a shorter cadence would smear the
# statistical assumptions. Keep monthly as the only resolution.
TEMPORAL_RESOLUTIONS = ["Monthly"]

# Baseline used for the climatology fit. Standard practice is a 30-year
# WMO reference period; 1991-2020 is the current one.
CLIMATOLOGY_START = 1991
CLIMATOLOGY_END = 2020

SPI_MIN, SPI_MAX = -3.0, 3.0  # clip infinite tail values


# ---------------------------------------------------------------------------
# Public catalog helpers
# ---------------------------------------------------------------------------

def get_available_parameters() -> Dict[str, Dict[str, str]]:
    return SPI_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    return TEMPORAL_RESOLUTIONS


# ---------------------------------------------------------------------------
# CHIRPS monthly aggregation via Earth Engine
# ---------------------------------------------------------------------------

def _monthly_chirps_series(
    locations: List[Tuple[float, float]],
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Pull the monthly-summed CHIRPS precipitation at each location for the
    given year range. Returns a long DataFrame with columns
    (location_id, latitude, longitude, year, month, precip_mm).

    Uses a single batched call per year (12 monthly reductions) via
    reduceRegions so cost scales with years, not locations x months.
    """
    daily = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").select("precipitation")

    # Build a FeatureCollection of the points (with buffer to match CHIRPS
    # nominal grid of ~5.5 km; a single-pixel sample is fine on that scale).
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
            monthly_img = daily.filterDate(m_start, m_end).sum().rename("precip_mm")

            try:
                reduced = monthly_img.reduceRegions(
                    collection=fc,
                    # setOutputs forces the property name; without it EE
                    # names the field 'first' regardless of band name.
                    reducer=ee.Reducer.first().setOutputs(["precip_mm"]),
                    scale=5566,  # CHIRPS native ~5.5 km
                )
                server_feats = reduced.getInfo().get("features", [])
            except Exception as e:
                # Skip individual month failures — don't abandon the fetch.
                # The SPI computation downstream drops NaNs so a few holes
                # are recoverable.
                print(f"[WARN] CHIRPS {year}-{month:02d}: {e}")
                continue

            for feat in server_feats:
                props = feat.get("properties") or {}
                val = props.get("precip_mm")
                # ee.Reducer.first returns None if the pixel is masked.
                if val is None:
                    precip = np.nan
                else:
                    try:
                        precip = float(val)
                    except (TypeError, ValueError):
                        precip = np.nan
                rows.append({
                    "location_id": int(props.get("location_id", -1)),
                    "latitude": props.get("latitude"),
                    "longitude": props.get("longitude"),
                    "year": year,
                    "month": month,
                    "precip_mm": precip,
                })

    if not rows:
        return pd.DataFrame(columns=[
            "location_id", "latitude", "longitude", "year", "month", "precip_mm",
        ])

    df = pd.DataFrame(rows)
    df = df.sort_values(["location_id", "year", "month"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# SPI computation
# ---------------------------------------------------------------------------

def _fit_gamma(values: np.ndarray) -> Tuple[float, float, float]:
    """Fit a 2-parameter gamma distribution to strictly-positive precip
    totals. Returns (shape, scale, p_zero). p_zero is the fraction of zero
    months in the input, used to handle the mixed continuous-discrete case
    (Guttman 1999)."""
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if values.size < 10:
        # Not enough data to fit — signal caller to fall back to z-score.
        return (np.nan, np.nan, np.nan)
    n = values.size
    n_zero = int(np.sum(values <= 0.0))
    p_zero = n_zero / n
    positive = values[values > 0.0]
    if positive.size < 5:
        return (np.nan, np.nan, p_zero)
    # Fix loc=0 — gamma is defined on [0, inf).
    shape, _loc, scale = stats.gamma.fit(positive, floc=0.0)
    return (shape, scale, p_zero)


def _spi_from_gamma(
    value: float,
    shape: float,
    scale: float,
    p_zero: float,
) -> float:
    """Transform a single precipitation value to an SPI z-score using the
    fitted gamma distribution + zero-inflation correction."""
    if np.isnan(value):
        return np.nan
    if np.isnan(shape) or np.isnan(scale):
        return np.nan
    if value <= 0.0:
        p = p_zero
    else:
        gamma_cdf = float(stats.gamma.cdf(value, shape, scale=scale))
        p = p_zero + (1.0 - p_zero) * gamma_cdf
    # Numerical guards: keep p strictly inside (0, 1) so norm.ppf stays finite.
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    z = float(stats.norm.ppf(p))
    return float(np.clip(z, SPI_MIN, SPI_MAX))


def _compute_spi_for_location(
    monthly_df: pd.DataFrame,
    window: int,
    baseline_years: Tuple[int, int],
) -> pd.DataFrame:
    """Compute rolling SPI-N for one location's monthly precipitation series.

    monthly_df must be sorted by (year, month) and cover exactly one
    location_id. Returns a copy of the input with `SPI_{window}` appended.
    """
    df = monthly_df.copy().reset_index(drop=True)
    precip = df["precip_mm"].to_numpy(dtype=float)
    n = len(precip)

    # Rolling-window sums (right-aligned): index i uses months [i-window+1 .. i].
    rolled = np.full(n, np.nan)
    if window > 0 and n >= window:
        cs = np.cumsum(np.concatenate([[0.0], np.nan_to_num(precip, nan=0.0)]))
        # Any window covering a NaN month is itself NaN (avoid biasing the fit).
        has_nan = pd.Series(np.isnan(precip)).rolling(window).sum().to_numpy()
        rolled[window - 1:] = cs[window:] - cs[:-window]
        rolled[has_nan > 0] = np.nan
    df[f"window_sum_{window}"] = rolled

    # Fit a gamma per calendar month using only the baseline period.
    yb0, yb1 = baseline_years
    baseline_mask = (df["year"] >= yb0) & (df["year"] <= yb1)
    df_baseline = df[baseline_mask]

    # Precompute fits per month-of-year.
    fits_by_month: Dict[int, Tuple[float, float, float]] = {}
    for m in range(1, 13):
        vals = df_baseline.loc[df_baseline["month"] == m, f"window_sum_{window}"].to_numpy()
        fits_by_month[m] = _fit_gamma(vals)

    # Apply each fit to every year of that calendar month.
    col = f"SPI_{window}"
    df[col] = np.nan
    for i in range(n):
        m = int(df.loc[i, "month"])
        v = float(df.loc[i, f"window_sum_{window}"])
        shape, scale, p_zero = fits_by_month.get(m, (np.nan, np.nan, np.nan))
        df.loc[i, col] = _spi_from_gamma(v, shape, scale, p_zero)

    return df


def _period_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-calendar-month climatology (mean & std over the baseline
    period) for the anomaly column. Assumes the caller has already trimmed
    to baseline years."""
    grouped = df.groupby("month")["precip_mm"]
    return grouped.agg(["mean", "std"]).rename(columns={"mean": "clim_mean", "std": "clim_std"})


# ---------------------------------------------------------------------------
# Public fetch entry point (weather-schema compatible)
# ---------------------------------------------------------------------------

def fetch_drought_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    credentials_dict: Dict,
) -> pd.DataFrame:
    """Fetch monthly precipitation + SPI indices for each location.

    Returns a DataFrame with columns (date, latitude, longitude, location_id,
    <requested params>). Compatible with the existing weather display and
    export pipeline in app.py.

    Args:
        locations: [(lat, lon), ...]
        parameters: subset of SPI_1/SPI_3/SPI_6/SPI_12 + PRECIP_MM /
                    PRECIP_ANOM_MM.
        start_date, end_date: 'YYYY-MM-DD' strings (only year/month matters).
        temporal_resolution: only 'Monthly' is supported; passed for API
                             compatibility.
        credentials_dict: EE service account credentials.
    """
    if temporal_resolution and temporal_resolution.lower() != "monthly":
        raise ValueError(
            "Drought indices are defined on monthly precipitation totals. "
            "Select 'Monthly' as the temporal resolution."
        )
    if not parameters:
        raise ValueError("No parameters requested.")

    # Initialize EE (idempotent guard inside EarthEngineClient).
    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # We need enough history for the gamma fit + rolling window. Pull from
    # min(start_year - 1, CLIMATOLOGY_START) so SPI-12 has room to warm up
    # even if the user requested a range that starts inside the baseline.
    windows_requested = [
        int(p.split("_")[1]) for p in parameters
        if p.startswith("SPI_") and p.split("_")[1].isdigit()
    ]
    max_window = max(windows_requested) if windows_requested else 1
    warmup_start_year = min(CLIMATOLOGY_START, start_dt.year - (max_window // 12) - 1)
    warmup_start_year = min(warmup_start_year, start_dt.year)  # never higher than target
    fetch_start_year = min(warmup_start_year, CLIMATOLOGY_START)
    fetch_end_year = max(end_dt.year, CLIMATOLOGY_END)

    print(
        f"[SPI] Locations={len(locations)}  "
        f"target={start_dt.date()}..{end_dt.date()}  "
        f"pulling CHIRPS monthly {fetch_start_year}-{fetch_end_year}"
    )

    monthly_all = _monthly_chirps_series(locations, fetch_start_year, fetch_end_year)
    if monthly_all.empty:
        return pd.DataFrame()

    # For each location, compute all requested SPI windows + anomaly.
    windows_needed = sorted(set(windows_requested))
    want_anom = "PRECIP_ANOM_MM" in parameters
    want_raw = "PRECIP_MM" in parameters

    out_frames: List[pd.DataFrame] = []
    for loc_id, loc_df in monthly_all.groupby("location_id"):
        loc_df = loc_df.sort_values(["year", "month"]).reset_index(drop=True)

        # SPI per requested window
        for w in windows_needed:
            loc_df = _compute_spi_for_location(
                loc_df, window=w,
                baseline_years=(CLIMATOLOGY_START, CLIMATOLOGY_END),
            )

        # Anomaly against baseline monthly mean
        if want_anom:
            baseline = loc_df[
                (loc_df["year"] >= CLIMATOLOGY_START)
                & (loc_df["year"] <= CLIMATOLOGY_END)
            ]
            clim = _period_averages(baseline)
            loc_df["PRECIP_ANOM_MM"] = (
                loc_df["precip_mm"]
                - loc_df["month"].map(clim["clim_mean"].to_dict())
            )

        if want_raw:
            loc_df["PRECIP_MM"] = loc_df["precip_mm"]

        # Trim to requested date range and keep only requested columns.
        loc_df["date"] = pd.to_datetime(
            loc_df["year"].astype(str) + "-"
            + loc_df["month"].astype(str).str.zfill(2) + "-01"
        )
        mask = (loc_df["date"] >= start_dt) & (loc_df["date"] <= end_dt)
        loc_df = loc_df.loc[mask].copy()

        keep_cols = ["date", "latitude", "longitude", "location_id"]
        for p in parameters:
            if p in loc_df.columns:
                keep_cols.append(p)
            elif p.startswith("SPI_"):
                w = int(p.split("_")[1])
                src = f"SPI_{w}"
                if src in loc_df.columns and p not in keep_cols:
                    keep_cols.append(p)

        out_frames.append(loc_df[keep_cols])

    if not out_frames:
        return pd.DataFrame()

    result = pd.concat(out_frames, ignore_index=True)
    result = result.sort_values(["location_id", "date"]).reset_index(drop=True)
    print(f"[SUCCESS] SPI: {len(result)} rows across {len(locations)} location(s).")
    return result
