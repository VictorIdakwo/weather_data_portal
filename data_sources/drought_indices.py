"""
Drought & vegetation-health indices.

Phase 2a: SPI (Standardized Precipitation Index) from CHIRPS.
Phase 2b: VCI / TCI / VHI (vegetation health) from MODIS NDVI + LST.

--- SPI ---
McKee et al. (1993): rolling precipitation sum -> gamma fit against
long-term climatology -> z-score.

    SPI >= +2.0   Extremely wet
    +1.5 to +2.0  Severely wet
    +1.0 to +1.5  Moderately wet
    -1.0 to +1.0  Near normal
    -1.5 to -1.0  Moderate drought
    -2.0 to -1.5  Severe drought
    SPI <  -2.0   Extreme drought

--- VCI / TCI / VHI ---
Kogan (1990, 1995) vegetation-health indices, in [0, 100]:

    VCI = (NDVI - NDVI_min) / (NDVI_max - NDVI_min) * 100
    TCI = (LST_max - LST) / (LST_max - LST_min) * 100
    VHI = 0.5 * VCI + 0.5 * TCI

    VHI  0-10   Extreme drought / vegetation stress
    VHI  10-20  Severe drought
    VHI  20-30  Moderate drought
    VHI  30-40  Mild drought
    VHI  40-60  Fair
    VHI  >  60  Favourable

Baseline percentiles for NDVI/LST are computed per calendar-month from
the 2001-2020 climatology.

Data:
    CHIRPS Daily v2.0 (UCSB-CHG/CHIRPS/DAILY)  - precipitation
    MOD13A1  (MODIS/061/MOD13A1, 500 m, 16-day) - NDVI
    MOD11A2  (MODIS/061/MOD11A2, 1 km,  8-day)  - LST_Day_1km
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
    "Vegetation Health": {
        "VCI": "VCI - Vegetation Condition Index (NDVI 0-100)",
        "TCI": "TCI - Temperature Condition Index (LST 0-100)",
        "VHI": "VHI - Vegetation Health Index (0.5*VCI + 0.5*TCI, 0-100)",
    },
    "Vegetation raw": {
        "NDVI_MEAN": "Monthly mean NDVI (MODIS MOD13A1)",
        "LST_DAY_C": "Monthly mean daytime LST (°C, MODIS MOD11A2)",
    },
}

# SPI is defined on monthly totals; a shorter cadence would smear the
# statistical assumptions. Keep monthly as the only resolution.
TEMPORAL_RESOLUTIONS = ["Monthly"]

# Baseline used for the climatology fit. Standard practice is a 30-year
# WMO reference period; 1991-2020 is the current one.
CLIMATOLOGY_START = 1991
CLIMATOLOGY_END = 2020

# MODIS starts in 2000; use a 2001-2020 window for VCI/TCI baselines.
MODIS_CLIMATOLOGY_START = 2001
MODIS_CLIMATOLOGY_END = 2020

SPI_MIN, SPI_MAX = -3.0, 3.0  # clip infinite tail values

_SPI_PARAM_PREFIXES = ("SPI_", "PRECIP")
_VEG_HEALTH_PARAMS = {"VCI", "TCI", "VHI", "NDVI_MEAN", "LST_DAY_C"}


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
# MODIS NDVI & LST monthly aggregation via Earth Engine
# ---------------------------------------------------------------------------

def _monthly_modis_series(
    locations: List[Tuple[float, float]],
    asset_id: str,
    band: str,
    out_field: str,
    scale_m: int,
    start_year: int,
    end_year: int,
    value_scale: float = 1.0,
    value_offset: float = 0.0,
) -> pd.DataFrame:
    """Generic monthly-mean fetcher for a MODIS ImageCollection band.

    Uses one batched reduceRegions per (year, month) — same pattern as
    _monthly_chirps_series so cost scales with months, not locations.

    Returns columns (location_id, latitude, longitude, year, month, <out_field>).
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
            monthly_img = coll.filterDate(m_start, m_end).mean().rename(band)

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
                        v = float(raw) * value_scale + value_offset
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
    df = df.sort_values(["location_id", "year", "month"]).reset_index(drop=True)
    return df


def _monthly_ndvi_series(
    locations: List[Tuple[float, float]], start_year: int, end_year: int,
) -> pd.DataFrame:
    """MODIS MOD13A1 monthly-mean NDVI. NDVI is stored as int16 x 10000."""
    return _monthly_modis_series(
        locations=locations,
        asset_id="MODIS/061/MOD13A1",
        band="NDVI",
        out_field="ndvi",
        scale_m=500,
        start_year=start_year,
        end_year=end_year,
        value_scale=1.0 / 10000.0,
    )


def _monthly_lst_series(
    locations: List[Tuple[float, float]], start_year: int, end_year: int,
) -> pd.DataFrame:
    """MODIS MOD11A2 monthly-mean daytime LST in °C.
    Raw storage is Kelvin x 0.02; we scale then convert to °C.
    """
    return _monthly_modis_series(
        locations=locations,
        asset_id="MODIS/061/MOD11A2",
        band="LST_Day_1km",
        out_field="lst_c",
        scale_m=1000,
        start_year=start_year,
        end_year=end_year,
        value_scale=0.02,
        value_offset=-273.15,
    )


# ---------------------------------------------------------------------------
# VCI / TCI / VHI computations (client-side, per location)
# ---------------------------------------------------------------------------

def _min_max_by_month(
    df: pd.DataFrame, value_col: str, baseline_years: Tuple[int, int]
) -> Tuple[Dict[int, float], Dict[int, float]]:
    """Per-calendar-month min and max of value_col over the baseline period."""
    yb0, yb1 = baseline_years
    base = df[(df["year"] >= yb0) & (df["year"] <= yb1)]
    grouped = base.groupby("month")[value_col]
    return grouped.min().to_dict(), grouped.max().to_dict()


def _apply_condition_index(
    df: pd.DataFrame,
    value_col: str,
    baseline_years: Tuple[int, int],
    invert: bool,
    out_col: str,
) -> pd.DataFrame:
    """Compute a Kogan-style condition index (VCI or TCI) column.

    If invert=False (VCI): 100 * (v - min) / (max - min)
    If invert=True  (TCI): 100 * (max - v) / (max - min)
    """
    df = df.copy()
    mins, maxs = _min_max_by_month(df, value_col, baseline_years)
    vals = df[value_col].to_numpy(dtype=float)
    months = df["month"].to_numpy(dtype=int)

    out = np.full_like(vals, np.nan, dtype=float)
    for i in range(len(df)):
        m = months[i]
        v = vals[i]
        vmin = mins.get(m)
        vmax = maxs.get(m)
        if np.isnan(v) or vmin is None or vmax is None:
            continue
        denom = vmax - vmin
        if denom <= 0:
            continue
        if invert:
            out[i] = float(np.clip((vmax - v) / denom * 100.0, 0.0, 100.0))
        else:
            out[i] = float(np.clip((v - vmin) / denom * 100.0, 0.0, 100.0))
    df[out_col] = out
    return df


# ---------------------------------------------------------------------------
# Public fetch entry point (weather-schema compatible)
# ---------------------------------------------------------------------------

def _add_date_col(df: pd.DataFrame) -> pd.DataFrame:
    """Attach a 'date' column built from year/month, first-of-month."""
    df = df.copy()
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + "-"
        + df["month"].astype(str).str.zfill(2) + "-01"
    )
    return df


def _compute_spi_frame(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_dt: datetime,
    end_dt: datetime,
) -> pd.DataFrame:
    """Fetch CHIRPS + compute SPI/anomaly/raw for all requested SPI-family
    parameters. Returns rows indexed by (location_id, date). Empty df if
    no SPI-family params were requested."""
    spi_params = [p for p in parameters if p.startswith(_SPI_PARAM_PREFIXES)]
    if not spi_params:
        return pd.DataFrame()

    windows_requested = [
        int(p.split("_")[1]) for p in spi_params
        if p.startswith("SPI_") and p.split("_")[1].isdigit()
    ]
    max_window = max(windows_requested) if windows_requested else 1
    warmup_start_year = min(
        CLIMATOLOGY_START, start_dt.year - (max_window // 12) - 1
    )
    warmup_start_year = min(warmup_start_year, start_dt.year)
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

    windows_needed = sorted(set(windows_requested))
    want_anom = "PRECIP_ANOM_MM" in spi_params
    want_raw = "PRECIP_MM" in spi_params

    out_frames: List[pd.DataFrame] = []
    for _loc_id, loc_df in monthly_all.groupby("location_id"):
        loc_df = loc_df.sort_values(["year", "month"]).reset_index(drop=True)
        for w in windows_needed:
            loc_df = _compute_spi_for_location(
                loc_df, window=w,
                baseline_years=(CLIMATOLOGY_START, CLIMATOLOGY_END),
            )
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
        loc_df = _add_date_col(loc_df)
        mask = (loc_df["date"] >= start_dt) & (loc_df["date"] <= end_dt)
        loc_df = loc_df.loc[mask].copy()
        out_frames.append(loc_df)

    if not out_frames:
        return pd.DataFrame()
    frame = pd.concat(out_frames, ignore_index=True)
    return frame


def _compute_veg_health_frame(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_dt: datetime,
    end_dt: datetime,
) -> pd.DataFrame:
    """Fetch MODIS NDVI + LST as needed and compute VCI/TCI/VHI + raw
    NDVI_MEAN / LST_DAY_C. Returns rows indexed by (location_id, date)."""
    want_vci = "VCI" in parameters
    want_tci = "TCI" in parameters
    want_vhi = "VHI" in parameters
    want_ndvi_raw = "NDVI_MEAN" in parameters
    want_lst_raw = "LST_DAY_C" in parameters

    need_ndvi = want_vci or want_vhi or want_ndvi_raw
    need_lst = want_tci or want_vhi or want_lst_raw
    if not (need_ndvi or need_lst):
        return pd.DataFrame()

    # We need enough history for the min/max climatology.
    fetch_start_year = min(MODIS_CLIMATOLOGY_START, start_dt.year - 1)
    fetch_end_year = max(end_dt.year, MODIS_CLIMATOLOGY_END)

    frames_by_loc: Dict[int, pd.DataFrame] = {}

    if need_ndvi:
        print(
            f"[VegHealth] Pulling MODIS NDVI monthly "
            f"{fetch_start_year}-{fetch_end_year}"
        )
        ndvi_df = _monthly_ndvi_series(locations, fetch_start_year, fetch_end_year)
        for loc_id, loc_df in ndvi_df.groupby("location_id"):
            loc_df = loc_df.sort_values(["year", "month"]).reset_index(drop=True)
            if want_vci or want_vhi:
                loc_df = _apply_condition_index(
                    loc_df, "ndvi",
                    (MODIS_CLIMATOLOGY_START, MODIS_CLIMATOLOGY_END),
                    invert=False, out_col="VCI",
                )
            if want_ndvi_raw:
                loc_df["NDVI_MEAN"] = loc_df["ndvi"]
            frames_by_loc[loc_id] = loc_df

    if need_lst:
        print(
            f"[VegHealth] Pulling MODIS LST monthly "
            f"{fetch_start_year}-{fetch_end_year}"
        )
        lst_df = _monthly_lst_series(locations, fetch_start_year, fetch_end_year)
        for loc_id, loc_df in lst_df.groupby("location_id"):
            loc_df = loc_df.sort_values(["year", "month"]).reset_index(drop=True)
            if want_tci or want_vhi:
                loc_df = _apply_condition_index(
                    loc_df, "lst_c",
                    (MODIS_CLIMATOLOGY_START, MODIS_CLIMATOLOGY_END),
                    invert=True, out_col="TCI",
                )
            if want_lst_raw:
                loc_df["LST_DAY_C"] = loc_df["lst_c"]
            existing = frames_by_loc.get(loc_id)
            if existing is None:
                frames_by_loc[loc_id] = loc_df
            else:
                # Merge NDVI-side and LST-side by (year, month).
                merged = existing.merge(
                    loc_df.drop(columns=["latitude", "longitude"], errors="ignore"),
                    on=["location_id", "year", "month"], how="outer",
                )
                frames_by_loc[loc_id] = merged

    if not frames_by_loc:
        return pd.DataFrame()

    # VHI = 0.5 * VCI + 0.5 * TCI (when both are available).
    out_frames = []
    for loc_id, loc_df in frames_by_loc.items():
        if want_vhi and "VCI" in loc_df.columns and "TCI" in loc_df.columns:
            loc_df["VHI"] = (
                0.5 * loc_df["VCI"].astype(float)
                + 0.5 * loc_df["TCI"].astype(float)
            )
        loc_df = _add_date_col(loc_df)
        mask = (loc_df["date"] >= start_dt) & (loc_df["date"] <= end_dt)
        out_frames.append(loc_df.loc[mask].copy())

    if not out_frames:
        return pd.DataFrame()
    return pd.concat(out_frames, ignore_index=True)


def fetch_drought_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    credentials_dict: Dict,
) -> pd.DataFrame:
    """Fetch monthly precipitation + drought/vegetation indices per location.

    Returns a DataFrame with columns (date, latitude, longitude, location_id,
    <requested params>). Weather-schema compatible.

    Args:
        locations: [(lat, lon), ...]
        parameters: any subset of the SPI, precipitation, vegetation-health,
                    and raw NDVI/LST parameters exposed by get_available_parameters().
        start_date, end_date: 'YYYY-MM-DD' strings (only year/month matters).
        temporal_resolution: only 'Monthly' is supported; passed for API compat.
        credentials_dict: EE service account credentials.
    """
    if temporal_resolution and temporal_resolution.lower() != "monthly":
        raise ValueError(
            "Drought / vegetation indices are defined on monthly aggregates. "
            "Select 'Monthly' as the temporal resolution."
        )
    if not parameters:
        raise ValueError("No parameters requested.")

    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    spi_frame = _compute_spi_frame(locations, parameters, start_dt, end_dt)
    veg_frame = _compute_veg_health_frame(locations, parameters, start_dt, end_dt)

    if spi_frame.empty and veg_frame.empty:
        return pd.DataFrame()

    # Merge the two side-by-side on (location_id, date). Prefer the union of
    # rows so a fetch that requests only SPI or only vegetation still succeeds.
    if spi_frame.empty:
        result = veg_frame
    elif veg_frame.empty:
        result = spi_frame
    else:
        # Keep only the join keys + carrier columns from veg_frame to avoid
        # duplicating latitude/longitude.
        veg_keep = ["location_id", "date"] + [
            c for c in veg_frame.columns
            if c in ("VCI", "TCI", "VHI", "NDVI_MEAN", "LST_DAY_C")
        ]
        result = spi_frame.merge(
            veg_frame[veg_keep],
            on=["location_id", "date"],
            how="outer",
        )
        # If SPI failed for some months but veg didn't (or vice versa),
        # restore lat/lon from whichever side has them.
        for col in ("latitude", "longitude"):
            if col not in result.columns:
                result[col] = np.nan
            if col in spi_frame.columns:
                lookup = spi_frame.set_index(["location_id", "date"])[col]
                mask = result[col].isna()
                if mask.any():
                    result.loc[mask, col] = result.loc[mask].apply(
                        lambda r: lookup.get((r["location_id"], r["date"]), np.nan),
                        axis=1,
                    )

    # Keep only what the caller asked for + the join columns.
    keep_cols = ["date", "latitude", "longitude", "location_id"]
    for p in parameters:
        if p in result.columns and p not in keep_cols:
            keep_cols.append(p)
    result = result[keep_cols]
    result = result.sort_values(["location_id", "date"]).reset_index(drop=True)
    print(
        f"[SUCCESS] Drought/veg indices: {len(result)} rows across "
        f"{len(locations)} location(s), params={parameters}."
    )
    return result
