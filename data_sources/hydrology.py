"""
Hydrology data sources.

Phase 4a: JRC Global Surface Water v1.4 - per-polygon surface-water
statistics. For each user AOI polygon, returns total water extent,
permanent vs seasonal breakdown, mean water occurrence, and the change
in water occurrence between 1984 and the current epoch.

Reference: Pekel et al. (2016), "High-resolution mapping of global
surface water and its long-term changes." Nature 540, 418-422.

Data:
    JRC/GSW1_4/GlobalSurfaceWater  Static image, 30 m, 1984-2021.
        Bands used here:
          occurrence   0-100, % of valid observations that were water
          change_abs   Change in occurrence between two epochs,
                       units of percentage points
          max_extent   Binary mask, ever water 1984-2021

Definitions used in this module:
    Water-ever      pixels with occurrence > 0
    Permanent       pixels with occurrence > 90
    Seasonal        pixels with 5 < occurrence <= 90
    Water percent   water-ever area divided by total polygon area
    Mean occurrence area-weighted mean occurrence over water-ever pixels
    Mean change_abs area-weighted mean change_abs over water-ever pixels

Output schema is polygon-summary style (one row per input polygon)
matching the LULC composition tables, so downstream CSV / JSON /
Excel exports work with no additional branching.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from .earth_engine_utils import EarthEngineClient
# Reuse the helpers already tested against KML / Shapefile input in lulc.py.
from .lulc import _to_2d_geometry, best_polygon_name


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------

GSW_DATASETS: Dict[str, Dict] = {
    "JRC Global Surface Water 1984-2021": {
        "asset": "JRC/GSW1_4/GlobalSurfaceWater",
        "scale": 30,
        "period": "1984-2021",
        "attribution": "Pekel et al. 2016, EC JRC, CC BY 4.0",
        "host_note": "Official GEE Data Catalog",
        "best_for": "Long-term water occurrence and change of lakes, "
                    "reservoirs, wetlands, and river-corridor extents",
    },
}


def get_available_datasets() -> List[str]:
    return list(GSW_DATASETS.keys())


def get_dataset_info(dataset_name: str) -> Dict:
    if dataset_name not in GSW_DATASETS:
        raise ValueError(f"Unknown hydrology dataset: {dataset_name}")
    return GSW_DATASETS[dataset_name]


# ---------------------------------------------------------------------------
# Public fetch entry point
# ---------------------------------------------------------------------------

def fetch_gsw_stats_from_gdf(
    aoi_gdf: gpd.GeoDataFrame,
    dataset_name: str,
    credentials_dict: Dict,
    scale_override: Optional[int] = None,
) -> pd.DataFrame:
    """Compute JRC Global Surface Water statistics per polygon.

    Args:
        aoi_gdf: GeoDataFrame of polygon AOIs.
        dataset_name: key into GSW_DATASETS.
        credentials_dict: EE service-account credentials.
        scale_override: Optional coarser scale (in m). Speed vs precision.

    Returns:
        Long DataFrame with one row per input polygon. Columns:
            polygon_id, polygon_name, dataset, period,
            total_area_km2, water_ever_km2, permanent_water_km2,
            seasonal_water_km2, water_percent, mean_occurrence,
            mean_change_pct, attribution.
    """
    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    info = get_dataset_info(dataset_name)
    asset = info["asset"]
    scale = int(scale_override or info["scale"])
    period = info["period"]
    attribution = info["attribution"]

    if aoi_gdf.crs is None or aoi_gdf.crs.to_epsg() != 4326:
        aoi_gdf = aoi_gdf.to_crs(4326)

    # Build the feature collection from valid polygons, dropping 3D Z and
    # repairing invalid topology using the same helpers as the LULC module.
    features = []
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
        ee_geom = ee.Geometry(mapping(geom))
        features.append(ee.Feature(ee_geom, {"polygon_id": int(idx)}))
        meta.append({"polygon_id": int(idx), "polygon_name": pname})

    if not features:
        raise ValueError("No usable polygon geometries in input.")

    fc = ee.FeatureCollection(features)

    # Multi-band image where every band is designed to be reduced with SUM,
    # so a single reduceRegions call gives us everything we need. Area bands
    # yield square-metre totals; the two "*_weighted" bands accumulate
    # occurrence * area and change * area — dividing them by the water-ever
    # area (also computed here) recovers the area-weighted mean without a
    # second EE round-trip.
    gsw = ee.Image(asset)
    occurrence = gsw.select("occurrence")
    change_abs = gsw.select("change_abs")

    water_ever_mask = occurrence.gt(0)
    permanent_mask = occurrence.gt(90)
    seasonal_mask = occurrence.gt(5).And(occurrence.lte(90))
    pixel_area = ee.Image.pixelArea()

    # For mean_occurrence over water-ever, we compute
    # sum(occurrence * area over water-ever) / sum(area over water-ever).
    occ_weighted = occurrence.updateMask(water_ever_mask).multiply(pixel_area)
    change_weighted = change_abs.updateMask(water_ever_mask).multiply(pixel_area)

    combined = ee.Image.cat([
        pixel_area.rename("total_area_m2"),
        pixel_area.multiply(water_ever_mask).rename("water_ever_m2"),
        pixel_area.multiply(permanent_mask).rename("permanent_m2"),
        pixel_area.multiply(seasonal_mask).rename("seasonal_m2"),
        occ_weighted.rename("occ_weighted"),
        change_weighted.rename("change_weighted"),
    ])

    reduced = combined.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.sum(),
        scale=scale,
        tileScale=4,
    )
    try:
        server_features = reduced.getInfo().get("features", [])
    except Exception as e:
        raise RuntimeError(
            f"Earth Engine could not compute GSW stats: {e}. "
            "Try fewer / smaller polygons, or a coarser scale_override."
        ) from e

    # Index polygon meta by id for the join.
    meta_by_id = {m["polygon_id"]: m for m in meta}

    rows: List[Dict] = []
    for feat in server_features:
        props = feat.get("properties") or {}
        try:
            pid = int(props.get("polygon_id"))
        except (TypeError, ValueError):
            continue
        m = meta_by_id.get(pid)
        if m is None:
            continue

        total_m2 = float(props.get("total_area_m2") or 0.0)
        water_ever_m2 = float(props.get("water_ever_m2") or 0.0)
        perm_m2 = float(props.get("permanent_m2") or 0.0)
        seas_m2 = float(props.get("seasonal_m2") or 0.0)
        occ_w = float(props.get("occ_weighted") or 0.0)
        chg_w = float(props.get("change_weighted") or 0.0)

        # Guard against noise-dominated statistics: when the water-ever area
        # is a rounding error (<0.5 km2 or <0.1% of the polygon), the area-
        # weighted means are dominated by a handful of flagged pixels and
        # aren't meaningful. Blank them out so downstream tables don't
        # display misleading numbers.
        water_pct = (water_ever_m2 / total_m2 * 100) if total_m2 > 0 else 0.0
        stats_reliable = (water_ever_m2 >= 500_000.0) and (water_pct >= 0.1)
        mean_occurrence = (
            occ_w / water_ever_m2 if (water_ever_m2 > 0 and stats_reliable) else None
        )
        mean_change_pct = (
            chg_w / water_ever_m2 if (water_ever_m2 > 0 and stats_reliable) else None
        )

        rows.append({
            "polygon_id": pid,
            "polygon_name": m["polygon_name"],
            "dataset": dataset_name,
            "period": period,
            "total_area_km2": round(total_m2 / 1_000_000, 4),
            "water_ever_km2": round(water_ever_m2 / 1_000_000, 4),
            "permanent_water_km2": round(perm_m2 / 1_000_000, 4),
            "seasonal_water_km2": round(seas_m2 / 1_000_000, 4),
            "water_percent": round(water_pct, 3),
            "mean_occurrence": round(mean_occurrence, 2) if mean_occurrence is not None else None,
            "mean_change_pct": round(mean_change_pct, 2) if mean_change_pct is not None else None,
            "attribution": attribution,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("polygon_id").reset_index(drop=True)
    return df
