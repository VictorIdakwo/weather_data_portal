"""
Vegetation phenology metrics from MODIS 16-day NDVI.

Per location and calendar year, extracts:

    SOS_DOY        Start of Season, day-of-year when NDVI crosses
                   a threshold on its ascending limb
    EOS_DOY        End of Season, day-of-year when NDVI drops back
                   below that threshold on the descending limb
    LOS_DAYS       Length of Season (EOS_DOY - SOS_DOY)
    PEAK_NDVI      Maximum smoothed NDVI value in the year
    PEAK_DOY       Day-of-year of the peak
    NDVI_INTEGRAL  Integrated NDVI over the growing season
                   (proxy for total seasonal productivity)

Method:
  - Ingests MODIS MOD13A1 16-day NDVI composites (raw 16-day data,
    NOT the monthly averages used elsewhere) at each point.
  - Optional Savitzky-Golay smoothing (window 5, poly 2) to reduce
    cloud/BRDF noise.
  - Peak by argmax; amplitude = peak - min; threshold = min + 0.2 * amp.
  - SOS = first pre-peak sample above threshold.
  - EOS = first post-peak sample below threshold.

Caveats:
  - Single-season detection; bimodal regimes (Eastern Africa long/short
    rains) collapse to the strongest of the two peaks.
  - Southern-hemisphere seasons that cross calendar-year boundaries are
    detected within each calendar year and may look truncated.
  - Threshold-based SOS/EOS is one of several valid methods; TIMESAT-
    style curve fitting is more robust but too heavy for point queries.

Output schema slots into the existing weather pipeline: one row per
(location, year) with the year encoded as YYYY-01-01 in the `date`
column so display / CSV / GeoJSON / Shapefile exports work as-is.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple, Optional

import ee
import numpy as np
import pandas as pd

from .earth_engine_utils import EarthEngineClient


# ---------------------------------------------------------------------------
# Parameter registry
# ---------------------------------------------------------------------------

PHENOLOGY_PARAMETERS: Dict[str, Dict[str, str]] = {
    "Timing (day-of-year)": {
        "SOS_DOY": "Start of Season (day-of-year, 1-366)",
        "EOS_DOY": "End of Season (day-of-year, 1-366)",
        "PEAK_DOY": "Peak-NDVI day-of-year",
        "LOS_DAYS": "Length of Season (EOS - SOS, days)",
    },
    "Magnitude": {
        "PEAK_NDVI": "Peak smoothed NDVI in the year (-1 to +1)",
        "NDVI_INTEGRAL": "Integrated NDVI over the growing season",
    },
}

TEMPORAL_RESOLUTIONS = ["Annual"]

# Detection thresholds
DEFAULT_AMP_FRACTION = 0.20    # SOS/EOS at 20% of amplitude above baseline
SMOOTH_WINDOW = 5              # Savitzky-Golay window (odd, in composites)
SMOOTH_POLY = 2                # SG polynomial order
MIN_OBSERVATIONS_PER_YEAR = 12 # need at least 12 of ~23 composites
MIN_AMPLITUDE = 0.10           # skip phenology detection below this NDVI amplitude


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    return PHENOLOGY_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    return TEMPORAL_RESOLUTIONS


# ---------------------------------------------------------------------------
# MODIS 16-day NDVI series via Earth Engine
# ---------------------------------------------------------------------------

def _ndvi_16day_series(
    locations: List[Tuple[float, float]],
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Fetch every MOD13A1 16-day NDVI composite at the given locations
    between the two years. Uses a server-side `collection.map(sample)`
    plus `flatten` so one round-trip pulls the whole series.

    Returns columns (location_id, latitude, longitude, date, year, doy, ndvi).
    NDVI is scaled to floats in [-1, +1].
    """
    coll = ee.ImageCollection("MODIS/061/MOD13A1").select("NDVI")

    features = []
    for idx, (lat, lon) in enumerate(locations):
        pt = ee.Geometry.Point([lon, lat])
        features.append(ee.Feature(pt, {
            "location_id": int(idx),
            "latitude": float(lat),
            "longitude": float(lon),
        }))
    fc = ee.FeatureCollection(features)

    filtered = coll.filterDate(f"{start_year}-01-01", f"{end_year + 1}-01-01")

    def sample_image(image):
        date = ee.Date(image.get("system:time_start")).format("YYYY-MM-dd")
        sampled = image.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.first().setOutputs(["ndvi_raw"]),
            scale=500,
        )
        return sampled.map(lambda f: f.set("date", date))

    all_samples = ee.FeatureCollection(
        filtered.map(sample_image)
    ).flatten()

    try:
        raw = all_samples.getInfo().get("features", [])
    except Exception as e:
        raise RuntimeError(
            f"Earth Engine phenology fetch failed: {e}. "
            "Try fewer locations or a shorter date range."
        ) from e

    rows: List[Dict] = []
    for feat in raw:
        props = feat.get("properties") or {}
        v = props.get("ndvi_raw")
        if v is None:
            ndvi = np.nan
        else:
            try:
                ndvi = float(v) / 10000.0  # MOD13A1 NDVI stored as int16 x 10000
            except (TypeError, ValueError):
                ndvi = np.nan
        rows.append({
            "location_id": int(props.get("location_id", -1)),
            "latitude": props.get("latitude"),
            "longitude": props.get("longitude"),
            "date": props.get("date"),
            "ndvi": ndvi,
        })

    if not rows:
        return pd.DataFrame(columns=[
            "location_id", "latitude", "longitude", "date", "year", "doy", "ndvi",
        ])

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["doy"] = df["date"].dt.dayofyear
    df = df.sort_values(["location_id", "date"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Per-location-year phenology extraction (client-side)
# ---------------------------------------------------------------------------

def _extract_phenology_for_year(
    year_df: pd.DataFrame,
    threshold_frac: float = DEFAULT_AMP_FRACTION,
) -> Optional[Dict]:
    """Extract phenology metrics from one location-year of NDVI observations.

    Returns a dict of metrics, or None if the year has too few valid samples.
    Individual metrics can still be None if a season boundary can't be found
    (e.g. no clear SOS crossing).
    """
    yd = year_df.sort_values("doy").reset_index(drop=True)
    ndvi = yd["ndvi"].to_numpy(dtype=float)
    doy = yd["doy"].to_numpy(dtype=int)

    valid = ~np.isnan(ndvi)
    if valid.sum() < MIN_OBSERVATIONS_PER_YEAR:
        return None

    # Fill NaNs with running mean for smoothing, then re-mask at output time.
    filled = ndvi.copy()
    if not valid.all():
        mean_valid = float(np.nanmean(ndvi))
        filled[~valid] = mean_valid

    # Savitzky-Golay smoothing helps but requires enough samples for the window.
    ndvi_s = filled
    if len(filled) >= SMOOTH_WINDOW:
        try:
            from scipy.signal import savgol_filter
            ndvi_s = savgol_filter(filled, SMOOTH_WINDOW, SMOOTH_POLY)
        except Exception:
            ndvi_s = filled

    peak_idx = int(np.argmax(ndvi_s))
    peak_ndvi = float(ndvi_s[peak_idx])
    peak_doy = int(doy[peak_idx])

    year_min = float(np.min(ndvi_s))
    amplitude = peak_ndvi - year_min

    result: Dict = {
        "PEAK_NDVI": round(peak_ndvi, 4),
        "PEAK_DOY": peak_doy,
        "SOS_DOY": None,
        "EOS_DOY": None,
        "LOS_DAYS": None,
        "NDVI_INTEGRAL": None,
    }

    if amplitude < MIN_AMPLITUDE:
        # Too flat to identify a growing season.
        return result

    threshold = year_min + threshold_frac * amplitude

    # SOS: first pre-peak sample above threshold on the ascending limb.
    sos_doy = None
    for i in range(peak_idx + 1):
        if ndvi_s[i] >= threshold:
            sos_doy = int(doy[i])
            break

    # EOS: first post-peak sample below threshold on the descending limb.
    eos_doy = None
    for i in range(peak_idx + 1, len(ndvi_s)):
        if ndvi_s[i] < threshold:
            eos_doy = int(doy[i])
            break

    if sos_doy is not None:
        result["SOS_DOY"] = sos_doy
    if eos_doy is not None:
        result["EOS_DOY"] = eos_doy
    if sos_doy is not None and eos_doy is not None:
        result["LOS_DAYS"] = int(eos_doy - sos_doy)

        # Growing-season integral: sum(NDVI - year_min) over [SOS, EOS].
        mask = (doy >= sos_doy) & (doy <= eos_doy)
        seg = ndvi_s[mask] - year_min
        seg = np.clip(seg, 0.0, None)
        # Trapezoidal integration over day-of-year gives NDVI * days.
        seg_doy = doy[mask]
        if seg.size >= 2:
            # np.trapezoid on modern numpy (>=2.0); fall back to np.trapz
            # on older environments (e.g. Streamlit Cloud still on 1.x).
            trap = getattr(np, "trapezoid", None) or getattr(np, "trapz")
            integral = float(trap(seg, seg_doy))
            result["NDVI_INTEGRAL"] = round(integral, 3)

    return result


# ---------------------------------------------------------------------------
# Public fetch entry point (weather-schema compatible)
# ---------------------------------------------------------------------------

def fetch_phenology_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    credentials_dict: Dict,
) -> pd.DataFrame:
    """Fetch annual phenology metrics per location.

    Returns a DataFrame with columns (date, latitude, longitude,
    location_id, <requested params>). Each row is one (location, year);
    date is YYYY-01-01 so downstream export machinery works as-is.

    Args:
        locations: [(lat, lon), ...]
        parameters: subset of PHENOLOGY_PARAMETERS parameters
        start_date, end_date: 'YYYY-MM-DD' — only the year matters.
        temporal_resolution: 'Annual' (only option; other values raise).
        credentials_dict: EE service account credentials.
    """
    if temporal_resolution and temporal_resolution.lower() != "annual":
        raise ValueError(
            "Phenology metrics are computed per calendar year. "
            "Select 'Annual' as the temporal resolution."
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
        f"[Phenology] Locations={len(locations)}  "
        f"pulling MOD13A1 16-day NDVI {fetch_start_year}-{fetch_end_year}"
    )

    ndvi_df = _ndvi_16day_series(locations, fetch_start_year, fetch_end_year)
    if ndvi_df.empty:
        return pd.DataFrame()

    rows: List[Dict] = []
    for (loc_id, year), year_df in ndvi_df.groupby(["location_id", "year"]):
        result = _extract_phenology_for_year(year_df)
        if result is None:
            continue
        first_row = year_df.iloc[0]
        rows.append({
            "date": pd.Timestamp(year=int(year), month=1, day=1),
            "latitude": first_row["latitude"],
            "longitude": first_row["longitude"],
            "location_id": int(loc_id),
            **result,
        })

    if not rows:
        return pd.DataFrame()

    result_df = pd.DataFrame(rows)
    keep_cols = ["date", "latitude", "longitude", "location_id"]
    for p in parameters:
        if p in result_df.columns and p not in keep_cols:
            keep_cols.append(p)
    result_df = result_df[keep_cols].sort_values(
        ["location_id", "date"]
    ).reset_index(drop=True)
    print(f"[SUCCESS] Phenology: {len(result_df)} rows across {len(locations)} location(s).")
    return result_df
