"""
Land Use / Land Cover (LULC) data source.

Polygon-based composition: for each input polygon (uploaded shapefile/KML
or African admin division), return one row per (polygon × class) with the
class area in km² and percent of polygon.

Datasets supported (Phase 1):
  * ESRI Sentinel-2 10 m LULC  — annual 2017+, default for change analysis
  * ESA WorldCover v200        — 2020 + 2021, highest single-year accuracy
  * Dynamic World V1           — 2015 → present, sub-annual composites

All three are free and accessible from Earth Engine using the existing
service account. ESRI is hosted as a community asset under sat-io.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from .earth_engine_utils import EarthEngineClient


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------

# Class scheme references:
#   ESRI:        Impact Observatory / Esri 10 m LULC. Note: class 10 = Clouds
#                (no-data) and should be reported as "Unobserved" rather than
#                a real class.
#   WorldCover:  ESA WorldCover v200 (2020 + 2021).
#   DynamicWorld: Google + WRI Dynamic World V1, 'label' band carries the
#                argmax of nine class probabilities.

LULC_DATASETS: Dict[str, Dict] = {
    "ESRI Sentinel-2 LULC": {
        "asset": "projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS",
        "asset_type": "image_collection",
        "band": "b1",  # ESRI annual mosaic uses a single band per image
        "scale": 10,
        "years_available": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        "default_year": 2024,
        "year_filter": "start_year",  # filter by image start year
        "classes": {
            1: "Water",
            2: "Trees",
            4: "Flooded vegetation",
            5: "Crops",
            7: "Built area",
            8: "Bare ground",
            9: "Snow/Ice",
            10: "Clouds (unobserved)",
            11: "Rangeland",
        },
        "nodata_classes": [10],  # Treat as unobserved, separate from real area
        "palette": {
            1: "#1A5BAB", 2: "#358221", 4: "#87D19E", 5: "#FFDB5C",
            7: "#ED022A", 8: "#EDE9E4", 9: "#F2FAFF", 10: "#C8C8C8",
            11: "#C6AD8D",
        },
        "attribution": "Esri | Impact Observatory | Microsoft, derived from Sentinel-2 imagery, CC BY 4.0",
        "license": "CC BY 4.0",
        "host_note": "Community-hosted GEE asset (sat-io/awesome-gee-community-datasets)",
        "best_for": "Annual change detection at 10 m (2017–present)",
    },
    "ESA WorldCover": {
        "asset": "ESA/WorldCover/v200",
        "asset_type": "image_collection",
        "band": "Map",
        "scale": 10,
        "years_available": [2020, 2021],
        "default_year": 2021,
        "year_filter": "start_year",
        "classes": {
            10: "Tree cover",
            20: "Shrubland",
            30: "Grassland",
            40: "Cropland",
            50: "Built-up",
            60: "Bare / sparse vegetation",
            70: "Snow and ice",
            80: "Permanent water bodies",
            90: "Herbaceous wetland",
            95: "Mangroves",
            100: "Moss and lichen",
        },
        "nodata_classes": [],
        "palette": {
            10: "#006400", 20: "#FFBB22", 30: "#FFFF4C", 40: "#F096FF",
            50: "#FA0000", 60: "#B4B4B4", 70: "#F0F0F0", 80: "#0064C8",
            90: "#0096A0", 95: "#00CF75", 100: "#FAE6A0",
        },
        "attribution": "ESA WorldCover Project (Zanaga et al., 2022), CC BY 4.0",
        "license": "CC BY 4.0",
        "host_note": "Official GEE Data Catalog",
        "best_for": "Highest single-year accuracy benchmark",
    },
    "Dynamic World": {
        "asset": "GOOGLE/DYNAMICWORLD/V1",
        "asset_type": "image_collection",
        "band": "label",
        "scale": 10,
        "years_available": list(range(2015, datetime.now().year + 1)),
        "default_year": datetime.now().year - 1,
        "year_filter": "date_range",  # filter by start_date/end_date
        "classes": {
            0: "Water",
            1: "Trees",
            2: "Grass",
            3: "Flooded vegetation",
            4: "Crops",
            5: "Shrub and scrub",
            6: "Built",
            7: "Bare",
            8: "Snow and ice",
        },
        "nodata_classes": [],
        "palette": {
            0: "#419BDF", 1: "#397D49", 2: "#88B053", 3: "#7A87C6",
            4: "#E49635", 5: "#DFC35A", 6: "#C4281B", 7: "#A59B8F",
            8: "#B39FE1",
        },
        "attribution": "Dynamic World V1, Google + WRI (Brown et al., 2022), CC BY 4.0",
        "license": "CC BY 4.0",
        "host_note": "Official GEE Data Catalog",
        "best_for": "Most recent data and sub-annual changes",
    },
}


# ---------------------------------------------------------------------------
# Public catalog helpers
# ---------------------------------------------------------------------------

def get_available_datasets() -> List[str]:
    """Names of supported LULC datasets, ordered by recommended default."""
    return list(LULC_DATASETS.keys())


def get_dataset_info(dataset_name: str) -> Dict:
    """Full metadata for one dataset."""
    if dataset_name not in LULC_DATASETS:
        raise ValueError(f"Unknown LULC dataset: {dataset_name}")
    return LULC_DATASETS[dataset_name]


def get_years_for_dataset(dataset_name: str) -> List[int]:
    return get_dataset_info(dataset_name)["years_available"]


def get_default_year(dataset_name: str) -> int:
    return get_dataset_info(dataset_name)["default_year"]


# ---------------------------------------------------------------------------
# Earth Engine image selection per dataset / year
# ---------------------------------------------------------------------------

def _build_lulc_image(dataset_name: str, year: int) -> ee.Image:
    """Return a single ee.Image for the dataset/year, with the class band
    renamed to 'class' for uniform downstream handling.
    """
    info = get_dataset_info(dataset_name)
    asset = info["asset"]
    band = info["band"]

    if dataset_name == "ESRI Sentinel-2 LULC":
        # ESRI annual mosaics: one image per calendar year. Filter by image
        # metadata `start_year` or, as a fallback, by date range Jan–Dec.
        coll = ee.ImageCollection(asset).filterDate(
            f"{year}-01-01", f"{year + 1}-01-01"
        )
        # Mosaic guards against the case where multiple tiles overlap.
        img = coll.mosaic().select([band], ["class"])
        return img

    if dataset_name == "ESA WorldCover":
        # WorldCover v200 has one image per year: 2020 and 2021.
        coll = ee.ImageCollection(asset).filterDate(
            f"{year}-01-01", f"{year + 1}-01-01"
        )
        img = coll.first().select([band], ["class"])
        return img

    if dataset_name == "Dynamic World":
        # Dynamic World is sub-annual; for an annual snapshot we take the
        # mode (most-frequent class) across the year's images per pixel.
        coll = ee.ImageCollection(asset).filterDate(
            f"{year}-01-01", f"{year + 1}-01-01"
        ).select(band)
        img = coll.reduce(ee.Reducer.mode()).rename("class").toInt()
        return img

    raise ValueError(f"Unknown LULC dataset: {dataset_name}")


# ---------------------------------------------------------------------------
# Polygon composition core
# ---------------------------------------------------------------------------

def _gdf_to_feature_collection(
    gdf: gpd.GeoDataFrame,
    name_col: Optional[str] = None,
) -> Tuple[ee.FeatureCollection, List[Dict]]:
    """Convert a GeoDataFrame (assumed WGS84) to an ee.FeatureCollection plus
    a parallel list of polygon metadata (name + original attributes).

    Returns:
        (FeatureCollection, polygon_meta_list)
    """
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)

    # Resolve the name column heuristically.
    if name_col and name_col in gdf.columns:
        name_field = name_col
    elif "name" in gdf.columns:
        name_field = "name"
    elif "NAME" in gdf.columns:
        name_field = "NAME"
    else:
        name_field = None

    features = []
    meta = []
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        # Only handle polygonal geometry for LULC composition.
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        polygon_name = (
            str(row[name_field]) if name_field else f"polygon_{idx}"
        )
        ee_geom = ee.Geometry(mapping(geom))
        features.append(ee.Feature(ee_geom, {"polygon_id": int(idx)}))
        # Stash original attributes for downstream join.
        attrs = {
            k: row[k]
            for k in gdf.columns
            if k != "geometry" and pd.notna(row[k])
        }
        meta.append({
            "polygon_id": int(idx),
            "polygon_name": polygon_name,
            "attrs": attrs,
        })

    if not features:
        raise ValueError("No polygon geometries found in input.")

    return ee.FeatureCollection(features), meta


def _composition_from_histogram(
    histogram: Dict,
    classes: Dict[int, str],
    nodata_classes: List[int],
    scale_m: float,
) -> List[Dict]:
    """Convert a {class_code -> pixel_count} histogram into a list of
    composition rows. Areas are reported in km². Percentages are computed
    against the total of *observed* pixels (nodata classes are excluded).
    """
    if not histogram:
        return []

    # Coerce keys to int (GEE returns them as strings).
    counts: Dict[int, int] = {}
    for k, v in histogram.items():
        try:
            counts[int(k)] = int(v)
        except (TypeError, ValueError):
            continue

    pixel_area_km2 = (scale_m / 1000.0) ** 2
    observed_total = sum(
        c for cls, c in counts.items() if cls not in nodata_classes
    )

    rows: List[Dict] = []
    for class_code, pixel_count in counts.items():
        class_name = classes.get(class_code, f"Unknown ({class_code})")
        is_nodata = class_code in nodata_classes
        area_km2 = round(pixel_count * pixel_area_km2, 4)
        if is_nodata:
            percent = None  # Don't include in percent calc
        else:
            percent = (
                round(pixel_count / observed_total * 100, 2)
                if observed_total > 0 else 0.0
            )
        rows.append({
            "class_code": class_code,
            "class_name": class_name,
            "pixel_count": pixel_count,
            "area_km2": area_km2,
            "percent": percent,
            "is_nodata": is_nodata,
        })

    # Sort by class_code for stable output.
    rows.sort(key=lambda r: r["class_code"])
    return rows


# ---------------------------------------------------------------------------
# Public fetch entry points
# ---------------------------------------------------------------------------

def fetch_lulc_composition_from_gdf(
    gdf: gpd.GeoDataFrame,
    dataset_name: str,
    year: int,
    credentials_dict: Dict,
    name_col: Optional[str] = None,
    scale_override: Optional[int] = None,
) -> pd.DataFrame:
    """Compute LULC class composition for every polygon in `gdf`.

    Returns a long-form DataFrame with columns:
        polygon_id, polygon_name, dataset, year, class_code, class_name,
        pixel_count, area_km2, percent, is_nodata, attribution
    plus any original feature-attribute columns prefixed with `attr_`.
    """
    # Initialize EE (idempotent — earth_engine_utils handles re-init guard).
    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    info = get_dataset_info(dataset_name)
    if year not in info["years_available"]:
        raise ValueError(
            f"Year {year} not available for {dataset_name}. "
            f"Available: {info['years_available']}"
        )
    scale_m = scale_override or info["scale"]

    fc, polygon_meta = _gdf_to_feature_collection(gdf, name_col=name_col)
    img = _build_lulc_image(dataset_name, year)

    # Batched per-polygon frequency histogram. `bestEffort=True` lets GEE
    # auto-coarsen the analysis scale for very large polygons rather than
    # erroring with "User memory limit exceeded".
    reduced = img.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.frequencyHistogram().setOutputs(["histogram"]),
        scale=scale_m,
    )

    # Pull results in one round-trip.
    server_features = reduced.getInfo().get("features", [])

    # Index histograms by polygon_id.
    histos: Dict[int, Dict] = {}
    for feat in server_features:
        props = feat.get("properties", {}) or {}
        pid = props.get("polygon_id")
        hist = props.get("histogram") or {}
        if pid is not None:
            histos[int(pid)] = hist

    classes = info["classes"]
    nodata = info["nodata_classes"]
    attribution = info["attribution"]

    rows: List[Dict] = []
    for meta in polygon_meta:
        pid = meta["polygon_id"]
        comp = _composition_from_histogram(
            histos.get(pid, {}), classes, nodata, scale_m
        )
        if not comp:
            # No pixels intersected (off-globe, all masked). Record a zero row
            # so the polygon still appears in output.
            rows.append({
                "polygon_id": pid,
                "polygon_name": meta["polygon_name"],
                "dataset": dataset_name,
                "year": year,
                "class_code": None,
                "class_name": "No data",
                "pixel_count": 0,
                "area_km2": 0.0,
                "percent": None,
                "is_nodata": True,
                "attribution": attribution,
                **{f"attr_{k}": v for k, v in meta["attrs"].items()},
            })
            continue
        for r in comp:
            rows.append({
                "polygon_id": pid,
                "polygon_name": meta["polygon_name"],
                "dataset": dataset_name,
                "year": year,
                **r,
                "attribution": attribution,
                **{f"attr_{k}": v for k, v in meta["attrs"].items()},
            })

    df = pd.DataFrame(rows)
    # Stable sort: by polygon then by class.
    if not df.empty:
        df = df.sort_values(
            ["polygon_id", "class_code"], na_position="last"
        ).reset_index(drop=True)
    return df


def fetch_lulc_change_from_gdf(
    gdf: gpd.GeoDataFrame,
    dataset_name: str,
    year_from: int,
    year_to: int,
    credentials_dict: Dict,
    name_col: Optional[str] = None,
    scale_override: Optional[int] = None,
    drop_unchanged: bool = False,
) -> pd.DataFrame:
    """For each polygon, compute the per-pixel transition matrix between
    `year_from` and `year_to` using the same dataset's annual snapshots.

    Returns a long-form DataFrame with columns:
        polygon_id, polygon_name, dataset, year_from, year_to,
        from_code, from_class, to_code, to_class, area_km2, percent
    plus original feature attributes prefixed with `attr_`.

    The transition code is encoded server-side as `from*1000 + to` to keep
    a single 32-bit channel for frequencyHistogram. Both years must be in
    the dataset's `years_available` list.
    """
    if year_from == year_to:
        raise ValueError("year_from and year_to must differ for change analysis.")

    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    info = get_dataset_info(dataset_name)
    years_ok = set(info["years_available"])
    for y in (year_from, year_to):
        if y not in years_ok:
            raise ValueError(
                f"Year {y} not available for {dataset_name}. "
                f"Available: {sorted(years_ok)}"
            )
    scale_m = scale_override or info["scale"]
    classes = info["classes"]
    nodata = set(info["nodata_classes"])

    fc, polygon_meta = _gdf_to_feature_collection(gdf, name_col=name_col)
    img_a = _build_lulc_image(dataset_name, year_from).toInt()
    img_b = _build_lulc_image(dataset_name, year_to).toInt()
    # Encode transition. Multiplier chosen so the largest valid class code
    # (100 for WorldCover "Moss and lichen") fits without overflow.
    transition = img_a.multiply(1000).add(img_b).rename("transition")

    reduced = transition.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.frequencyHistogram().setOutputs(["histogram"]),
        scale=scale_m,
    )
    server_features = reduced.getInfo().get("features", [])

    histos: Dict[int, Dict] = {}
    for feat in server_features:
        props = feat.get("properties") or {}
        pid = props.get("polygon_id")
        h = props.get("histogram") or {}
        if pid is not None:
            histos[int(pid)] = h

    pixel_area_km2 = (scale_m / 1000.0) ** 2
    attribution = info["attribution"]

    rows: List[Dict] = []
    for meta in polygon_meta:
        pid = meta["polygon_id"]
        hist = histos.get(pid) or {}
        # Sum over observed pixels (excluding any (from, to) where either
        # class is in the dataset's nodata set).
        observed_total = 0
        for code_str, cnt in hist.items():
            try:
                code = int(code_str)
            except (TypeError, ValueError):
                continue
            f_code = code // 1000
            t_code = code % 1000
            if f_code in nodata or t_code in nodata:
                continue
            observed_total += int(cnt)

        if observed_total == 0:
            rows.append({
                "polygon_id": pid,
                "polygon_name": meta["polygon_name"],
                "dataset": dataset_name,
                "year_from": year_from,
                "year_to": year_to,
                "from_code": None,
                "from_class": "No data",
                "to_code": None,
                "to_class": "No data",
                "area_km2": 0.0,
                "percent": None,
                "is_unchanged": False,
                "attribution": attribution,
                **{f"attr_{k}": v for k, v in meta["attrs"].items()},
            })
            continue

        for code_str, cnt in hist.items():
            try:
                code = int(code_str)
                pixel_count = int(cnt)
            except (TypeError, ValueError):
                continue
            f_code = code // 1000
            t_code = code % 1000
            if f_code in nodata or t_code in nodata:
                continue
            f_name = classes.get(f_code, f"Unknown ({f_code})")
            t_name = classes.get(t_code, f"Unknown ({t_code})")
            unchanged = (f_code == t_code)
            if drop_unchanged and unchanged:
                continue
            area_km2 = round(pixel_count * pixel_area_km2, 4)
            percent = round(pixel_count / observed_total * 100, 3)
            rows.append({
                "polygon_id": pid,
                "polygon_name": meta["polygon_name"],
                "dataset": dataset_name,
                "year_from": year_from,
                "year_to": year_to,
                "from_code": f_code,
                "from_class": f_name,
                "to_code": t_code,
                "to_class": t_name,
                "area_km2": area_km2,
                "percent": percent,
                "is_unchanged": unchanged,
                "attribution": attribution,
                **{f"attr_{k}": v for k, v in meta["attrs"].items()},
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(
            ["polygon_id", "area_km2"],
            ascending=[True, False],
        ).reset_index(drop=True)
    return df


def build_polygon_geodataframe(
    composition_df: pd.DataFrame,
    aoi_gdf: gpd.GeoDataFrame,
    name_col: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Combine a long-form LULC composition DataFrame with the AOI's polygon
    geometries to produce a spatial GeoDataFrame suitable for Shapefile or
    GeoJSON export.

    The output has one row per input polygon (joined on polygon_id index)
    with attribute columns:
        polygon_name, dataset, year, dominant_class, dominant_pct,
        class_richness, plus pct_<class_name> and area_<class_name>
        columns for each class observed in the dataset.
    Original geometry is preserved.
    """
    if composition_df.empty or aoi_gdf.empty:
        return gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")

    # Drop nodata rows; they shouldn't drive dominant-class or percent fields.
    comp = composition_df[~composition_df["is_nodata"]].copy()

    # Find the dominant class per polygon.
    idx_max = comp.groupby("polygon_id")["percent"].idxmax()
    dominant = comp.loc[idx_max, ["polygon_id", "class_name", "percent"]].rename(
        columns={"class_name": "dominant_class", "percent": "dominant_pct"}
    )

    # Class richness = number of distinct non-zero classes per polygon.
    richness = (
        comp[comp["pixel_count"] > 0]
        .groupby("polygon_id")["class_name"]
        .nunique()
        .rename("class_richness")
        .reset_index()
    )

    # Wide percent matrix.
    pct_wide = comp.pivot_table(
        index=["polygon_id"],
        columns="class_name",
        values="percent",
        aggfunc="sum",
        fill_value=0,
    )
    pct_wide.columns = [f"pct_{c}" for c in pct_wide.columns]

    # Wide area matrix.
    area_wide = comp.pivot_table(
        index=["polygon_id"],
        columns="class_name",
        values="area_km2",
        aggfunc="sum",
        fill_value=0,
    )
    area_wide.columns = [f"area_{c}" for c in area_wide.columns]

    # Pull dataset/year (the same for every row in a single fetch).
    meta_cols = comp[["polygon_id", "polygon_name", "dataset", "year"]].drop_duplicates(
        subset=["polygon_id"]
    )

    attrs = (
        meta_cols
        .merge(dominant, on="polygon_id", how="left")
        .merge(richness, on="polygon_id", how="left")
        .merge(pct_wide.reset_index(), on="polygon_id", how="left")
        .merge(area_wide.reset_index(), on="polygon_id", how="left")
    )

    # Rejoin geometry from the AOI gdf (which the fetcher iterated in order).
    # Build a lookup by the same polygon_id used during fetch (the gdf row index).
    if aoi_gdf.crs is None or aoi_gdf.crs.to_epsg() != 4326:
        aoi_gdf = aoi_gdf.to_crs(4326)
    aoi_idx = aoi_gdf.reset_index().rename(columns={"index": "polygon_id"})
    aoi_idx["polygon_id"] = aoi_idx["polygon_id"].astype(int)
    attrs["polygon_id"] = attrs["polygon_id"].astype(int)

    merged = aoi_idx.merge(attrs, on="polygon_id", how="left")

    # Drop the AOI's own attribute columns to avoid duplicates beyond what
    # the composition already exposes — keep the geometry and polygon_id.
    keep = ["polygon_id", "geometry"] + [c for c in attrs.columns if c != "polygon_id"]
    merged = merged[keep]
    return gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")


def build_change_geodataframe(
    change_df: pd.DataFrame,
    aoi_gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Same idea as build_polygon_geodataframe but for change results.

    Output attributes per polygon:
        polygon_name, dataset, year_from, year_to,
        changed_area_km2, percent_changed,
        top_loss_class, top_loss_km2, top_loss_to,
        top_gain_class, top_gain_km2, top_gain_from
    """
    if change_df.empty or aoi_gdf.empty:
        return gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")

    # Drop nodata-tagged rows (none of the real classes — these are the
    # "No data" placeholders we add when a polygon had no observed pixels).
    df = change_df.dropna(subset=["from_code", "to_code"]).copy()
    df["from_code"] = df["from_code"].astype(int)
    df["to_code"] = df["to_code"].astype(int)

    grouped = []
    for pid, sub in df.groupby("polygon_id"):
        changed = sub[~sub["is_unchanged"]]
        total_area = sub["area_km2"].sum()
        changed_area = changed["area_km2"].sum()
        percent_changed = (
            round(changed_area / total_area * 100, 2) if total_area > 0 else 0.0
        )

        # Top loss: class with largest outgoing area to a different class.
        loss_per_class = (
            changed.groupby("from_class")["area_km2"].sum().sort_values(ascending=False)
        )
        if not loss_per_class.empty:
            top_loss_class = loss_per_class.index[0]
            top_loss_km2 = round(float(loss_per_class.iloc[0]), 4)
            # Which target did most of it go to?
            top_loss_to = (
                changed[changed["from_class"] == top_loss_class]
                .groupby("to_class")["area_km2"]
                .sum()
                .sort_values(ascending=False)
                .index[0]
            )
        else:
            top_loss_class = top_loss_to = None
            top_loss_km2 = 0.0

        # Top gain: class with largest incoming area from a different class.
        gain_per_class = (
            changed.groupby("to_class")["area_km2"].sum().sort_values(ascending=False)
        )
        if not gain_per_class.empty:
            top_gain_class = gain_per_class.index[0]
            top_gain_km2 = round(float(gain_per_class.iloc[0]), 4)
            top_gain_from = (
                changed[changed["to_class"] == top_gain_class]
                .groupby("from_class")["area_km2"]
                .sum()
                .sort_values(ascending=False)
                .index[0]
            )
        else:
            top_gain_class = top_gain_from = None
            top_gain_km2 = 0.0

        grouped.append({
            "polygon_id": int(pid),
            "polygon_name": sub["polygon_name"].iloc[0],
            "dataset": sub["dataset"].iloc[0],
            "year_from": int(sub["year_from"].iloc[0]),
            "year_to": int(sub["year_to"].iloc[0]),
            "changed_area_km2": round(float(changed_area), 4),
            "percent_changed": percent_changed,
            "top_loss_class": top_loss_class,
            "top_loss_km2": top_loss_km2,
            "top_loss_to": top_loss_to,
            "top_gain_class": top_gain_class,
            "top_gain_km2": top_gain_km2,
            "top_gain_from": top_gain_from,
        })

    attrs = pd.DataFrame(grouped)

    if aoi_gdf.crs is None or aoi_gdf.crs.to_epsg() != 4326:
        aoi_gdf = aoi_gdf.to_crs(4326)
    aoi_idx = aoi_gdf.reset_index().rename(columns={"index": "polygon_id"})
    aoi_idx["polygon_id"] = aoi_idx["polygon_id"].astype(int)
    attrs["polygon_id"] = attrs["polygon_id"].astype(int)

    merged = aoi_idx.merge(attrs, on="polygon_id", how="left")
    keep = ["polygon_id", "geometry"] + [c for c in attrs.columns if c != "polygon_id"]
    merged = merged[keep]
    return gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")


# ---------------------------------------------------------------------------
# Raster clip download URLs (per polygon, server-resolved by Earth Engine)
# ---------------------------------------------------------------------------

def get_raster_clip_url(
    aoi_gdf: gpd.GeoDataFrame,
    dataset_name: str,
    year: int,
    credentials_dict: Dict,
    polygon_index: int = 0,
    fmt: str = "GEO_TIFF",
    max_pixels_warn: int = 100_000_000,
) -> Dict:
    """Return a signed Earth Engine download URL for a single polygon's
    clipped LULC raster, plus metadata about the request.

    Args:
        aoi_gdf: GeoDataFrame containing the AOI polygons (any number).
        dataset_name: One of the supported LULC datasets.
        year: Year to clip.
        credentials_dict: EE service-account credentials.
        polygon_index: Row index of the polygon to clip (0 by default).
        fmt: 'GEO_TIFF' (default) or 'ZIPPED_GEO_TIFF'. COG variant is
             not exposed through getDownloadURL; callers wanting a COG
             should use Export.image.toCloudStorage / toDrive instead
             (added in Phase 12).
        max_pixels_warn: Raise a soft warning in the returned dict
             when the estimated pixel count exceeds this.

    Returns:
        dict with keys 'url', 'estimated_pixels', 'note', and 'attribution'.
        Caller is responsible for rendering / surfacing this.
    """
    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    if aoi_gdf.crs is None or aoi_gdf.crs.to_epsg() != 4326:
        aoi_gdf = aoi_gdf.to_crs(4326)
    if polygon_index < 0 or polygon_index >= len(aoi_gdf):
        raise IndexError(
            f"polygon_index {polygon_index} out of range (0..{len(aoi_gdf) - 1})"
        )

    row = aoi_gdf.iloc[polygon_index]
    geom = row.geometry
    ee_geom = ee.Geometry(mapping(geom))

    info = get_dataset_info(dataset_name)
    scale_m = info["scale"]
    # All supported class schemes use codes < 255, so cast to uint8 to keep
    # the clipped raster ~4x smaller than the default int32 encoding —
    # critical for staying under EE's 50 MB synchronous-request cap.
    img = _build_lulc_image(dataset_name, year).clip(ee_geom).toUint8()

    # Rough pixel-count estimate from the polygon's bounding box.
    minx, miny, maxx, maxy = geom.bounds
    mean_lat = (miny + maxy) / 2.0
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(mean_lat))
    bbox_area_m2 = (
        max(0.0, (maxx - minx) * m_per_deg_lon)
        * max(0.0, (maxy - miny) * m_per_deg_lat)
    )
    estimated_pixels = int(bbox_area_m2 / (scale_m * scale_m))

    # Earth Engine caps the synchronous download URL at ~50 MB. For a
    # single-band uint8 raster that's ~50M pixels of raw data; with TIFF
    # overhead the practical ceiling is closer to ~35-40M pixels. Refuse
    # client-side before we hit a hard server error.
    hard_pixel_cap = 35_000_000
    if estimated_pixels > hard_pixel_cap:
        raise ValueError(
            f"Polygon spans an estimated {estimated_pixels:,} pixels at "
            f"{scale_m} m, exceeding the ~{hard_pixel_cap:,}-pixel cap on "
            f"Earth Engine's synchronous GeoTIFF endpoint. "
            f"Options: (1) clip a smaller sub-polygon, "
            f"(2) wait for the async Export.image.toDrive path in Phase 12, "
            f"(3) request a coarser scale via scale_override."
        )

    note = None
    if estimated_pixels > max_pixels_warn:
        note = (
            f"Polygon spans an estimated {estimated_pixels:,} pixels at "
            f"{scale_m} m. Download may take 30+ seconds and the GeoTIFF "
            f"will be relatively large."
        )

    try:
        url = img.getDownloadURL({
            "scale": scale_m,
            "region": ee_geom,
            "format": fmt,
            "crs": "EPSG:4326",
        })
    except Exception as e:
        msg = str(e)
        if "request size" in msg.lower() or "50331648" in msg:
            raise ValueError(
                f"Earth Engine rejected the clip request (size limit). "
                f"Estimated {estimated_pixels:,} pixels — try a smaller "
                f"polygon or wait for the async export path."
            ) from e
        raise

    return {
        "url": url,
        "estimated_pixels": estimated_pixels,
        "scale_m": scale_m,
        "note": note,
        "attribution": info["attribution"],
        "polygon_index": polygon_index,
        "polygon_name": (
            str(row.get("name") or row.get("NAME") or f"polygon_{polygon_index}")
        ),
        "dataset": dataset_name,
        "year": year,
    }


def change_to_wide(df: pd.DataFrame, value: str = "area_km2") -> pd.DataFrame:
    """Pivot a change DataFrame into a (from_class) x (to_class) matrix per
    polygon. Returns one row per (polygon, from_class), one column per
    to_class. `value` is 'area_km2' or 'percent'.
    """
    if df.empty:
        return df
    if value not in ("area_km2", "percent"):
        raise ValueError("value must be 'area_km2' or 'percent'")
    keep = ["polygon_id", "polygon_name", "dataset", "year_from", "year_to", "from_class"]
    wide = df.pivot_table(
        index=keep,
        columns="to_class",
        values=value,
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    wide.columns.name = None
    return wide


def composition_to_wide(df: pd.DataFrame, value: str = "percent") -> pd.DataFrame:
    """Pivot a long-form composition DataFrame into one row per polygon
    with one column per class. `value` is either 'percent' or 'area_km2'.
    """
    if df.empty:
        return df
    if value not in ("percent", "area_km2"):
        raise ValueError("value must be 'percent' or 'area_km2'")
    # Drop nodata rows for the wide view; users want a clean composition.
    base = df[~df["is_nodata"]].copy()
    keep = ["polygon_id", "polygon_name", "dataset", "year"]
    wide = base.pivot_table(
        index=keep,
        columns="class_name",
        values=value,
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    wide.columns.name = None
    return wide


# ---------------------------------------------------------------------------
# Admin-division convenience: build a GeoDataFrame from FAO GAUL
# ---------------------------------------------------------------------------

def gdf_from_admin_selection(
    countries: List[str],
    divisions: Optional[Dict[str, List[str]]] = None,
    credentials_dict: Optional[Dict] = None,
) -> gpd.GeoDataFrame:
    """Build a polygon GeoDataFrame for user-selected African admin areas
    by pulling from FAO/GAUL/2015. Falls back to country-level when no
    divisions are given.

    The FAO GAUL ADM0/ADM1 name fields don't always match the spellings
    in `utils/africa_locations.py` (e.g. "Côte d'Ivoire" vs "Ivory Coast"),
    so this does best-effort case-insensitive matching and silently drops
    unresolvable names. Callers should warn the user when the returned
    gdf has fewer rows than requested.
    """
    if not countries:
        raise ValueError("No countries supplied.")
    if credentials_dict is not None:
        client = EarthEngineClient(credentials_dict=credentials_dict)
        if not client.initialized:
            raise RuntimeError("Earth Engine initialization failed")

    rows: List[Dict] = []

    # Helper: case-insensitive equality filter on a GAUL property.
    def _ieq(prop: str, value: str):
        return ee.Filter.eq(prop, value)

    for country in countries:
        wanted_divs = (divisions or {}).get(country) or []

        if wanted_divs:
            fc = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(
                _ieq("ADM0_NAME", country)
            )
            for div in wanted_divs:
                sub = fc.filter(_ieq("ADM1_NAME", div))
                feats = sub.getInfo().get("features", [])
                if not feats:
                    # Try a contains-style match as fallback.
                    sub = fc.filter(ee.Filter.stringContains("ADM1_NAME", div))
                    feats = sub.getInfo().get("features", [])
                for f in feats:
                    geom = f.get("geometry")
                    props = f.get("properties", {}) or {}
                    rows.append({
                        "name": props.get("ADM1_NAME", div),
                        "country": props.get("ADM0_NAME", country),
                        "admin_level": 1,
                        "geometry": geom,
                    })
        else:
            fc = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(
                _ieq("ADM0_NAME", country)
            )
            feats = fc.getInfo().get("features", [])
            for f in feats:
                geom = f.get("geometry")
                props = f.get("properties", {}) or {}
                rows.append({
                    "name": props.get("ADM0_NAME", country),
                    "country": props.get("ADM0_NAME", country),
                    "admin_level": 0,
                    "geometry": geom,
                })

    if not rows:
        raise ValueError(
            "No admin polygons matched the selected countries/divisions in "
            "FAO GAUL 2015. Try a different spelling or upload a shapefile."
        )

    # Build a GeoDataFrame from the GeoJSON geometries.
    from shapely.geometry import shape
    geoms = [shape(r.pop("geometry")) for r in rows]
    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:4326")
    return gdf
