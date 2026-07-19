"""
Cross-layer analytical engine.

Phase 11 delivers the foundation for combining two or more fetched
result tables into one analytical dataframe. Users can:

  - Join two tables on their natural keys (location_id + date for
    time-series; polygon_id for polygon summaries).
  - Compute derived columns: ratio, difference, product, correlation
    per-location.
  - Aggregate over time (mean, sum, min, max, std) or over polygons.

The engine is intentionally table-agnostic: it inspects columns to
detect join keys, so any pair of results the app produces can be
combined without changes.

Typical use flow:
  df_a = <run one fetch, save via save_snapshot()>
  df_b = <run another fetch, save_snapshot() again>
  merged = cross_join(df_a, df_b)
  merged["ndvi_per_mm"] = derive_ratio(merged, "NDVI_MEAN", "PRECIP_MM")
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


TIME_KEYS = ("date", "datetime")
POLYGON_KEYS = ("polygon_id",)
LOCATION_KEYS = ("location_id",)

RESERVED_JOIN_COLS = set(
    TIME_KEYS + POLYGON_KEYS + LOCATION_KEYS
    + ("latitude", "longitude", "polygon_name", "location_name")
)


def detect_schema(df: pd.DataFrame) -> Dict[str, bool]:
    """Return a dict describing which key families are present."""
    cols = set(df.columns)
    return {
        "has_time":     bool(cols & set(TIME_KEYS)),
        "has_polygon":  bool(cols & set(POLYGON_KEYS)),
        "has_location": bool(cols & set(LOCATION_KEYS)),
        "n_rows":       len(df),
        "n_locations":  df["location_id"].nunique() if "location_id" in df.columns else 0,
        "n_polygons":   df["polygon_id"].nunique() if "polygon_id" in df.columns else 0,
        "value_columns": sorted(cols - RESERVED_JOIN_COLS),
    }


def cross_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    how: str = "inner",
    suffixes: Tuple[str, str] = ("_a", "_b"),
) -> pd.DataFrame:
    """Join two result tables on their overlapping natural keys.

    Rules:
      - If both have location_id + date/datetime: join on both.
      - If both have polygon_id: join on that alone.
      - If both have location_id but only one has date: join on location.
      - Otherwise cross-product isn't well defined and we raise.
    """
    ls = detect_schema(left)
    rs = detect_schema(right)

    def _time_col(df):
        for k in TIME_KEYS:
            if k in df.columns:
                return k
        return None

    join_keys: List[str] = []
    if ls["has_location"] and rs["has_location"]:
        join_keys.append("location_id")
    if ls["has_polygon"] and rs["has_polygon"]:
        join_keys.append("polygon_id")

    lt, rt = _time_col(left), _time_col(right)
    if lt and rt:
        # Normalise both time cols onto the LEFT's name to make merge simple.
        if lt != rt:
            right = right.rename(columns={rt: lt})
        join_keys.append(lt)

    if not join_keys:
        raise ValueError(
            "Cannot join: neither location_id nor polygon_id is common "
            "between the two tables, and no shared time axis."
        )

    # Split reserved passthrough columns so we don't get duplicated
    # latitude / longitude / name columns after the join.
    def _keep_left_side(cols_left, cols_right):
        drop_from_right = []
        for c in ("latitude", "longitude", "location_name", "polygon_name"):
            if c in cols_left and c in cols_right:
                drop_from_right.append(c)
        return drop_from_right

    drop = _keep_left_side(list(left.columns), list(right.columns))
    right = right.drop(columns=drop, errors="ignore")

    merged = left.merge(right, on=join_keys, how=how, suffixes=suffixes)
    return merged


# ---- derived-column helpers ---------------------------------------------

def derive_ratio(
    df: pd.DataFrame, numerator: str, denominator: str,
    fill_zero: bool = True,
) -> pd.Series:
    a = pd.to_numeric(df[numerator], errors="coerce")
    b = pd.to_numeric(df[denominator], errors="coerce")
    with np.errstate(divide="ignore", invalid="ignore"):
        r = a / b
    r = r.replace([np.inf, -np.inf], np.nan)
    if fill_zero:
        r = r.fillna(0)
    return r


def derive_difference(df: pd.DataFrame, a_col: str, b_col: str) -> pd.Series:
    a = pd.to_numeric(df[a_col], errors="coerce")
    b = pd.to_numeric(df[b_col], errors="coerce")
    return a - b


def derive_product(df: pd.DataFrame, a_col: str, b_col: str) -> pd.Series:
    a = pd.to_numeric(df[a_col], errors="coerce")
    b = pd.to_numeric(df[b_col], errors="coerce")
    return a * b


def derive_zscore(df: pd.DataFrame, col: str, group_cols: Optional[List[str]] = None) -> pd.Series:
    """Standardise a column into z-scores. If group_cols is given,
    standardises per group (e.g. per location_id)."""
    x = pd.to_numeric(df[col], errors="coerce")
    if not group_cols:
        return (x - x.mean()) / x.std(ddof=1)
    grp = df[group_cols].copy()
    grp["__x__"] = x
    z = grp.groupby(group_cols)["__x__"].transform(
        lambda s: (s - s.mean()) / s.std(ddof=1)
    )
    return z


def per_location_correlation(
    df: pd.DataFrame, a_col: str, b_col: str,
    group_col: str = "location_id",
) -> pd.DataFrame:
    """Return one row per location with the Pearson correlation between
    two value columns computed over that location's time series."""
    def _r(sub):
        a = pd.to_numeric(sub[a_col], errors="coerce")
        b = pd.to_numeric(sub[b_col], errors="coerce")
        valid = a.notna() & b.notna()
        if valid.sum() < 3:
            return np.nan
        return float(np.corrcoef(a[valid], b[valid])[0, 1])

    out = df.groupby(group_col).apply(_r).rename(f"corr_{a_col}_{b_col}")
    return out.reset_index()


def summarise_over_time(
    df: pd.DataFrame,
    value_cols: List[str],
    stats: List[str] = ("mean", "min", "max", "std"),
    group_col: str = "location_id",
) -> pd.DataFrame:
    """One row per location with time-series summary stats per value col."""
    if not value_cols:
        return pd.DataFrame()
    grouped = df.groupby(group_col)[value_cols].agg(list(stats))
    grouped.columns = [f"{c}_{s}" for c, s in grouped.columns]
    return grouped.reset_index()


def anomaly_vs_baseline(
    df: pd.DataFrame,
    value_col: str,
    baseline_years: Tuple[int, int],
    time_col: str = "date",
    group_col: str = "location_id",
) -> pd.Series:
    """Difference from the per-location, per-calendar-month mean over the
    baseline year range. Useful when combining a "current" fetch with a
    long climatology in one table."""
    if time_col not in df.columns:
        raise ValueError(f"{time_col} not in DataFrame")
    dt = pd.to_datetime(df[time_col], errors="coerce")
    month = dt.dt.month
    year = dt.dt.year
    x = pd.to_numeric(df[value_col], errors="coerce")

    y0, y1 = baseline_years
    baseline_mask = (year >= y0) & (year <= y1)
    means = (
        df.assign(__x__=x, __m__=month)
        .loc[baseline_mask]
        .groupby([group_col, "__m__"])["__x__"]
        .mean()
        .to_dict()
    )
    def _lookup(g, m):
        return means.get((g, m), np.nan)
    out = pd.Series([
        _lookup(g, m) for g, m in zip(df[group_col], month)
    ], index=df.index)
    return x - out
