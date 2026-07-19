"""
Forest structure and biomass extensions.

Phase 7 complements the Hansen forest-loss layer already shipping in
land_degradation.py with three static forest-structure datasets:

  ESA CCI Biomass L4 AGB v6-1      100 m, aboveground biomass (t/ha),
                                     epochs 2010, 2015-2022
  Potapov Global Canopy Height 2020 30 m,  tree-canopy height in metres
  Global Mangrove Watch v3          30 m,  mangrove-extent masks per epoch

Polygon-summary output per AOI: one row per polygon with the mean /
totals / area figures you'd actually cite in a report.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from .earth_engine_utils import EarthEngineClient
from .lulc import _to_2d_geometry, best_polygon_name


BIOMASS_DATASETS: Dict[str, Dict] = {
    "ESA CCI Biomass v6.1 (2022)": {
        "asset": "ESA/CCI/BIOMASS/L4/AGB/v6-1",
        "asset_type": "image_collection",
        "band": "AGB",
        "scale": 100,
        "year": 2022,
        "attribution": "ESA CCI Biomass Project v6.1, Santoro et al. 2024",
    },
    "ESA CCI Biomass v6.1 (2015)": {
        "asset": "ESA/CCI/BIOMASS/L4/AGB/v6-1",
        "asset_type": "image_collection",
        "band": "AGB",
        "scale": 100,
        "year": 2015,
        "attribution": "ESA CCI Biomass Project v6.1",
    },
    "Potapov Global Canopy Height 2020": {
        "asset": "users/potapovpeter/GEDI_V27",
        "asset_type": "image",
        "band": "b1",
        "scale": 30,
        "year": 2020,
        "attribution": "Potapov et al. 2021, GLAD / Univ. Maryland",
    },
    "Global Mangrove Watch v3 (2020)": {
        "asset": "LANDSAT/MANGROVE_FORESTS",
        "asset_type": "image_collection",
        "band": "1",
        "scale": 30,
        "year": 2020,
        "attribution": "Bunting et al. 2018, Global Mangrove Watch",
    },
}


def get_available_datasets() -> List[str]:
    return list(BIOMASS_DATASETS.keys())


def get_dataset_info(name: str) -> Dict:
    if name not in BIOMASS_DATASETS:
        raise ValueError(f"Unknown biomass dataset: {name}")
    return BIOMASS_DATASETS[name]


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


def _load_image(info: Dict) -> ee.Image:
    """Return a single ee.Image for the dataset spec."""
    if info["asset_type"] == "image":
        return ee.Image(info["asset"]).select(info["band"])
    year = info["year"]
    coll = ee.ImageCollection(info["asset"]).filterDate(
        f"{year}-01-01", f"{year + 1}-01-01"
    ).select(info["band"])
    return coll.mosaic()


def fetch_biomass_stats_from_gdf(
    aoi_gdf: gpd.GeoDataFrame,
    dataset_name: str,
    credentials_dict: Dict,
    scale_override: Optional[int] = None,
) -> pd.DataFrame:
    """Compute per-polygon statistics for one biomass / forest-structure
    dataset. Output columns depend on the dataset family:
        biomass    -> AGB_MEAN_T_HA, AGB_TOTAL_MT (megatonnes),
                       AREA_WITH_BIOMASS_KM2, POLYGON_AREA_KM2
        canopy     -> CANOPY_MEAN_M, CANOPY_MAX_M, CANOPY_TREES_KM2
        mangrove   -> MANGROVE_KM2, PERCENT_MANGROVE
    All rows also include polygon_id, polygon_name, dataset, year,
    attribution.
    """
    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    info = get_dataset_info(dataset_name)
    scale = int(scale_override or info["scale"])

    features, meta = _prepare_features(aoi_gdf)
    if not features:
        raise ValueError("No usable polygon geometries in input.")
    fc = ee.FeatureCollection(features)
    meta_by_id = {m["polygon_id"]: m for m in meta}

    image = _load_image(info)
    pixel_area = ee.Image.pixelArea()

    # Family-specific reductions built into a single sum-reducible image so
    # one reduceRegions call covers everything the family needs.
    ds_key = dataset_name.lower()
    is_mangrove = "mangrove" in ds_key
    is_canopy = "canopy" in ds_key
    is_biomass = not (is_mangrove or is_canopy)

    if is_biomass:
        biomass_mask = image.gt(0).unmask(0)
        combined = ee.Image.cat([
            pixel_area.rename("total_area_m2"),
            pixel_area.multiply(biomass_mask).rename("biomass_area_m2"),
            # AGB is in t/ha; converting to t/pixel: agb * (area_ha) =
            # agb * (pixel_area_m2 / 10000). Sum gives total tonnes.
            image.multiply(pixel_area).divide(10000).unmask(0).rename("agb_tonnes"),
        ])
    elif is_canopy:
        tree_mask = image.gt(3).unmask(0)  # >3 m = treed pixel
        combined = ee.Image.cat([
            pixel_area.rename("total_area_m2"),
            pixel_area.multiply(tree_mask).rename("tree_area_m2"),
            image.multiply(pixel_area).multiply(tree_mask).unmask(0).rename(
                "canopy_h_weighted_m2"
            ),
        ])
    else:  # mangrove
        mangrove_mask = image.gt(0).unmask(0)
        combined = ee.Image.cat([
            pixel_area.rename("total_area_m2"),
            pixel_area.multiply(mangrove_mask).rename("mangrove_area_m2"),
        ])

    try:
        reduced = combined.reduceRegions(
            collection=fc,
            reducer=ee.Reducer.sum(),
            scale=scale,
            tileScale=4,
        )
        server_feats = reduced.getInfo().get("features", [])
    except Exception as e:
        raise RuntimeError(
            f"Earth Engine biomass reduction failed: {e}. Try a smaller AOI "
            "or a coarser scale_override."
        ) from e

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

        if is_biomass:
            b_m2 = float(props.get("biomass_area_m2") or 0.0)
            agb_t = float(props.get("agb_tonnes") or 0.0)
            row["AGB_MEAN_T_HA"] = round(agb_t / (b_m2 / 10000), 2) if b_m2 > 0 else None
            row["AGB_TOTAL_MT"] = round(agb_t / 1_000_000, 4)
            row["AREA_WITH_BIOMASS_KM2"] = round(b_m2 / 1_000_000, 4)
        elif is_canopy:
            t_m2 = float(props.get("tree_area_m2") or 0.0)
            h_w = float(props.get("canopy_h_weighted_m2") or 0.0)
            row["CANOPY_MEAN_M"] = round(h_w / t_m2, 2) if t_m2 > 0 else None
            row["CANOPY_TREES_KM2"] = round(t_m2 / 1_000_000, 4)
            row["PERCENT_TREES"] = round(t_m2 / total_m2 * 100, 3) if total_m2 > 0 else 0
        else:  # mangrove
            m2 = float(props.get("mangrove_area_m2") or 0.0)
            row["MANGROVE_KM2"] = round(m2 / 1_000_000, 4)
            row["PERCENT_MANGROVE"] = round(m2 / total_m2 * 100, 3) if total_m2 > 0 else 0

        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("polygon_id").reset_index(drop=True)
    return df
