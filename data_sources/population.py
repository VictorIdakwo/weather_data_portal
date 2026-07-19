"""
Population & built-up per-polygon summary.

Phase 9: three gridded human-footprint datasets aggregated per polygon.
Open Buildings v3 vector footprints are deferred - they need a
different download pattern (vector export, potentially very large).

  WorldPop 2020 (100 m, unconstrained)
    Gridded population per 100 m cell.
  GHS-BUILT-S R2023A epoch (100 m)
    Global Human Settlement built-up surface fraction. Values 0-10000
    are m^2 of built-up per pixel; sum-reduce gives built-up area (km2).
  VIIRS nighttime lights (500 m monthly composite)
    Radiance in nanoWatts / cm^2 / sr. Mean value over polygon is a
    proxy for electrification / economic activity.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from .earth_engine_utils import EarthEngineClient
from .lulc import _to_2d_geometry, best_polygon_name


POPULATION_DATASETS: Dict[str, Dict] = {
    "WorldPop 2020 (unconstrained, 100 m)": {
        "asset": "WorldPop/GP/100m/pop",
        "asset_type": "image_collection",
        "band": "population",
        "scale": 100,
        "year": 2020,
        "attribution": "WorldPop 2020, University of Southampton",
        "family": "population",
    },
    "GHS-BUILT-S R2023A (2020, 100 m)": {
        "asset": "JRC/GHSL/P2023A/GHS_BUILT_S/2020",
        "asset_type": "image",
        "band": "built_surface",
        "scale": 100,
        "year": 2020,
        "attribution": "JRC GHSL P2023A",
        "family": "built",
    },
    "GHS-BUILT-S R2023A (2000, 100 m)": {
        "asset": "JRC/GHSL/P2023A/GHS_BUILT_S/2000",
        "asset_type": "image",
        "band": "built_surface",
        "scale": 100,
        "year": 2000,
        "attribution": "JRC GHSL P2023A",
        "family": "built",
    },
    "VIIRS nighttime lights (monthly, 500 m)": {
        "asset": "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG",
        "asset_type": "image_collection",
        "band": "avg_rad",
        "scale": 500,
        "year": None,  # Requires a date-range roll-up
        "attribution": "NOAA VIIRS DNB Monthly V1",
        "family": "lights",
    },
}


def get_available_datasets() -> List[str]:
    return list(POPULATION_DATASETS.keys())


def get_dataset_info(name: str) -> Dict:
    if name not in POPULATION_DATASETS:
        raise ValueError(f"Unknown population dataset: {name}")
    return POPULATION_DATASETS[name]


def _prepare_features(aoi_gdf: gpd.GeoDataFrame):
    if aoi_gdf.crs is None or aoi_gdf.crs.to_epsg() != 4326:
        aoi_gdf = aoi_gdf.to_crs(4326)
    features, meta = [], []
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
            if geom.is_empty:
                continue
        pname = best_polygon_name(row, idx)
        features.append(
            ee.Feature(ee.Geometry(mapping(geom)), {"polygon_id": int(idx)})
        )
        meta.append({"polygon_id": int(idx), "polygon_name": pname})
    return features, meta


def _load_image(info: Dict, date_range: Optional[tuple] = None) -> ee.Image:
    """Return the image, filtered when the family needs a date range."""
    if info["asset_type"] == "image":
        return ee.Image(info["asset"]).select(info["band"])
    coll = ee.ImageCollection(info["asset"]).select(info["band"])
    if info["family"] == "lights" and date_range:
        s, e = date_range
        return coll.filterDate(s, e).mean()
    if info["family"] == "population":
        year = info["year"]
        return coll.filterDate(f"{year}-01-01", f"{year + 1}-01-01").mosaic()
    return coll.mosaic()


def fetch_population_stats_from_gdf(
    aoi_gdf: gpd.GeoDataFrame,
    dataset_name: str,
    credentials_dict: Dict,
    scale_override: Optional[int] = None,
    date_range: Optional[tuple] = None,
) -> pd.DataFrame:
    """Compute per-polygon summary for one population / built-up dataset.

    Output columns depend on the family:
        population -> POPULATION_TOTAL, POPULATION_DENSITY_PER_KM2,
                      POLYGON_AREA_KM2
        built      -> BUILT_UP_KM2, PERCENT_BUILT, POLYGON_AREA_KM2
        lights     -> MEAN_RADIANCE, SUM_RADIANCE, POLYGON_AREA_KM2
    """
    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    info = get_dataset_info(dataset_name)
    scale = int(scale_override or info["scale"])
    family = info["family"]

    features, meta = _prepare_features(aoi_gdf)
    if not features:
        raise ValueError("No usable polygon geometries in input.")
    fc = ee.FeatureCollection(features)
    meta_by_id = {m["polygon_id"]: m for m in meta}

    image = _load_image(info, date_range=date_range)
    pixel_area = ee.Image.pixelArea()

    if family == "population":
        # WorldPop stores per-pixel population count. Sum gives polygon
        # total.
        combined = ee.Image.cat([
            pixel_area.rename("total_area_m2"),
            image.unmask(0).rename("pop_count"),
        ])
        reducer = ee.Reducer.sum()
    elif family == "built":
        # GHS-BUILT-S stores built-up m^2 per pixel. Sum gives total.
        combined = ee.Image.cat([
            pixel_area.rename("total_area_m2"),
            image.unmask(0).rename("built_m2"),
        ])
        reducer = ee.Reducer.sum()
    else:  # lights
        # Reduce mean AND count separately - EE Reducer.mean gives us
        # the mean already; also sum for total-radiance.
        combined = ee.Image.cat([
            pixel_area.rename("total_area_m2"),
            image.unmask(0).rename("rad_sum"),
            image.rename("rad_mean_input"),
        ])
        reducer = (
            ee.Reducer.sum().setOutputs(["total_area_m2", "rad_sum", "rad_unused"])
            .combine(
                ee.Reducer.mean().setOutputs(["ta_m", "rs_m", "rad_mean"]),
                sharedInputs=True,
            )
        )

    try:
        reduced = combined.reduceRegions(
            collection=fc,
            reducer=reducer,
            scale=scale,
            tileScale=4,
        )
        server_feats = reduced.getInfo().get("features", [])
    except Exception as e:
        raise RuntimeError(f"EE population reduction failed: {e}") from e

    rows: List[Dict] = []
    for feat in server_feats:
        props = feat.get("properties") or {}
        try:
            pid = int(props.get("polygon_id"))
        except (TypeError, ValueError):
            continue
        m = meta_by_id.get(pid)
        if m is None:
            continue
        total_m2 = float(props.get("total_area_m2") or 0.0)
        row = {
            "polygon_id": pid,
            "polygon_name": m["polygon_name"],
            "dataset": dataset_name,
            "year": info["year"],
            "attribution": info["attribution"],
            "POLYGON_AREA_KM2": round(total_m2 / 1_000_000, 4),
        }
        area_km2 = total_m2 / 1_000_000 if total_m2 > 0 else 0.0

        if family == "population":
            pop = float(props.get("pop_count") or 0.0)
            row["POPULATION_TOTAL"] = round(pop, 0)
            row["POPULATION_DENSITY_PER_KM2"] = round(pop / area_km2, 1) if area_km2 > 0 else 0
        elif family == "built":
            b_m2 = float(props.get("built_m2") or 0.0)
            row["BUILT_UP_KM2"] = round(b_m2 / 1_000_000, 4)
            row["PERCENT_BUILT"] = round(b_m2 / total_m2 * 100, 3) if total_m2 > 0 else 0
        else:  # lights
            row["MEAN_RADIANCE"] = round(float(props.get("rad_mean") or 0.0), 3)
            row["SUM_RADIANCE"] = round(float(props.get("rad_sum") or 0.0), 3)

        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("polygon_id").reset_index(drop=True)
    return df
