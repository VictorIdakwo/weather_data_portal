"""
Africa-specific data stack.

Phase 8 layers designed specifically for African analysis, where the
global generics (SoilGrids, ESA Land Cover) can miss important
country-level context.

  iSDA-Africa soil properties     30 m, Sept 2021 v2
      pH, organic carbon, nitrogen, sand/clay/silt fractions
      Reference: Hengl et al. 2021 - continentally trained on
      African soil profiles.
  ESA WorldCereal 2021             10 m, crop-type classification
      Temporary cropland, temporary irrigated cropland, active
      cropland masks; per-polygon coverage in km2.
      Reference: van Tricht et al. 2023.

Both produce per-polygon summary rows.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping

from .earth_engine_utils import EarthEngineClient
from .lulc import _to_2d_geometry, best_polygon_name


# ---------------------------------------------------------------------------
# iSDA-Africa soils
# ---------------------------------------------------------------------------

# All iSDA layers share the same 30 m EPSG:4326 grid. Each param name is
# a public column output; the meta gives the ee asset id, the natural-log
# / offset transform iSDA uses in storage, and the physical unit.
_ISDA_PARAMS: Dict[str, Dict] = {
    "SOIL_PH_0_20":     {"asset": "ISDASOIL/Africa_SoilGrids/PhH2o",         "band": "mean_0_20", "unit": "pH",     "transform": "isda_ln"},
    "SOIL_PH_20_50":    {"asset": "ISDASOIL/Africa_SoilGrids/PhH2o",         "band": "mean_20_50","unit": "pH",     "transform": "isda_ln"},
    "SOIL_OC_0_20":     {"asset": "ISDASOIL/Africa_SoilGrids/CarbonOrganic","band": "mean_0_20", "unit": "g/kg",   "transform": "isda_ln"},
    "SOIL_OC_20_50":    {"asset": "ISDASOIL/Africa_SoilGrids/CarbonOrganic","band": "mean_20_50","unit": "g/kg",   "transform": "isda_ln"},
    "SOIL_N_0_20":      {"asset": "ISDASOIL/Africa_SoilGrids/NitrogenTotal","band": "mean_0_20", "unit": "g/kg",   "transform": "isda_ln"},
    "SOIL_SAND_0_20":   {"asset": "ISDASOIL/Africa_SoilGrids/TextureClassSand",  "band": "mean_0_20", "unit": "%",  "transform": "isda_ln"},
    "SOIL_CLAY_0_20":   {"asset": "ISDASOIL/Africa_SoilGrids/TextureClassClay",  "band": "mean_0_20", "unit": "%",  "transform": "isda_ln"},
    "SOIL_SILT_0_20":   {"asset": "ISDASOIL/Africa_SoilGrids/TextureClassSilt",  "band": "mean_0_20", "unit": "%",  "transform": "isda_ln"},
}


AFRICA_PARAMETERS: Dict[str, Dict[str, str]] = {
    "iSDA-Africa soil (0-20 cm)": {
        "SOIL_PH_0_20":   "Soil pH (0-20 cm)",
        "SOIL_OC_0_20":   "Soil organic carbon (g/kg, 0-20 cm)",
        "SOIL_N_0_20":    "Soil total nitrogen (g/kg, 0-20 cm)",
        "SOIL_SAND_0_20": "Soil sand fraction (%, 0-20 cm)",
        "SOIL_CLAY_0_20": "Soil clay fraction (%, 0-20 cm)",
        "SOIL_SILT_0_20": "Soil silt fraction (%, 0-20 cm)",
    },
    "iSDA-Africa soil (20-50 cm subsoil)": {
        "SOIL_PH_20_50":  "Soil pH (20-50 cm)",
        "SOIL_OC_20_50":  "Soil organic carbon (g/kg, 20-50 cm)",
    },
    "ESA WorldCereal 2021 (10 m)": {
        "CROPLAND_KM2":       "Temporary cropland area (km2)",
        "IRR_CROPLAND_KM2":   "Temporary irrigated cropland (km2)",
        "ACTIVE_CROPLAND_KM2":"Active cropland area (km2)",
        "PERCENT_CROPLAND":   "Cropland as percent of polygon",
    },
}


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    return AFRICA_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    # These are static products; a single-fetch is all that's meaningful.
    return ["Snapshot"]


# iSDA transformation: stored = round(log(1 + physical) * 10), so
# physical = exp(stored / 10) - 1. Applied client-side after sampling.
import math


def _isda_decode(v):
    if v is None:
        return float("nan")
    try:
        return float(math.exp(float(v) / 10.0) - 1)
    except Exception:
        return float("nan")


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


def fetch_africa_stack_from_gdf(
    aoi_gdf: gpd.GeoDataFrame,
    parameters: List[str],
    credentials_dict: Dict,
) -> pd.DataFrame:
    """Compute per-polygon summary rows for any mix of iSDA soil params
    and WorldCereal cropland stats."""
    if not parameters:
        raise ValueError("No parameters requested.")

    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise RuntimeError("Earth Engine initialization failed")

    features, meta = _prepare_features(aoi_gdf)
    if not features:
        raise ValueError("No usable polygon geometries in input.")
    fc = ee.FeatureCollection(features)
    meta_by_id = {m["polygon_id"]: m for m in meta}

    output_by_polygon: Dict[int, Dict] = {
        pid: {
            "polygon_id": pid,
            "polygon_name": m["polygon_name"],
        }
        for pid, m in meta_by_id.items()
    }

    # ---- iSDA soils (mean reduce, one call per requested param) -----
    isda_params = [p for p in parameters if p in _ISDA_PARAMS]
    if isda_params:
        print(f"[Africa] iSDA params: {isda_params}")
    for p in isda_params:
        m = _ISDA_PARAMS[p]
        try:
            img = ee.Image(m["asset"]).select(m["band"])
            reduced = img.reduceRegions(
                collection=fc,
                reducer=ee.Reducer.mean().setOutputs([p]),
                scale=30,
                tileScale=4,
            )
            server_feats = reduced.getInfo().get("features", [])
        except Exception as e:
            print(f"  [WARN] {p}: {e}")
            continue
        for feat in server_feats:
            props = feat.get("properties") or {}
            try:
                pid = int(props.get("polygon_id"))
            except (TypeError, ValueError):
                continue
            raw = props.get(p)
            if raw is None:
                output_by_polygon[pid][p] = None
                continue
            if m["transform"] == "isda_ln":
                import math
                try:
                    output_by_polygon[pid][p] = round(math.exp(float(raw) / 10.0) - 1, 3)
                except Exception:
                    output_by_polygon[pid][p] = None
            else:
                output_by_polygon[pid][p] = round(float(raw), 3)

    # ---- WorldCereal (sum masks * pixelArea, one call) --------------
    wc_params = [p for p in parameters if p.endswith("_KM2") or p == "PERCENT_CROPLAND"]
    if wc_params:
        try:
            wc_2021 = ee.ImageCollection(
                "ESA/WorldCereal/2021/MODELS/v100"
            ).filter(ee.Filter.eq("aez_group", "temporarycrops")).mosaic().select("classification")
            pixel_area = ee.Image.pixelArea()
            cropland_mask = wc_2021.gt(0).unmask(0)
            active_mask = wc_2021.eq(100).unmask(0)  # class 100 = active cropland
            irr_mask = wc_2021.eq(200).unmask(0)     # class 200 = irrigated
            combined = ee.Image.cat([
                pixel_area.rename("total_area_m2"),
                pixel_area.multiply(cropland_mask).rename("cropland_m2"),
                pixel_area.multiply(active_mask).rename("active_m2"),
                pixel_area.multiply(irr_mask).rename("irr_m2"),
            ])
            reduced = combined.reduceRegions(
                collection=fc,
                reducer=ee.Reducer.sum(),
                scale=100,
                tileScale=4,
            )
            server_feats = reduced.getInfo().get("features", [])
            for feat in server_feats:
                props = feat.get("properties") or {}
                try:
                    pid = int(props.get("polygon_id"))
                except (TypeError, ValueError):
                    continue
                total_m2 = float(props.get("total_area_m2") or 0.0)
                crop_m2 = float(props.get("cropland_m2") or 0.0)
                if "CROPLAND_KM2" in parameters:
                    output_by_polygon[pid]["CROPLAND_KM2"] = round(crop_m2 / 1_000_000, 4)
                if "IRR_CROPLAND_KM2" in parameters:
                    output_by_polygon[pid]["IRR_CROPLAND_KM2"] = round(
                        float(props.get("irr_m2") or 0.0) / 1_000_000, 4
                    )
                if "ACTIVE_CROPLAND_KM2" in parameters:
                    output_by_polygon[pid]["ACTIVE_CROPLAND_KM2"] = round(
                        float(props.get("active_m2") or 0.0) / 1_000_000, 4
                    )
                if "PERCENT_CROPLAND" in parameters:
                    output_by_polygon[pid]["PERCENT_CROPLAND"] = (
                        round(crop_m2 / total_m2 * 100, 3) if total_m2 > 0 else 0.0
                    )
        except Exception as e:
            print(f"[WARN] WorldCereal failed: {e}")
            print("  (WorldCereal has known EE catalog changes; if all values")
            print("   are missing, catalog path may need updating.)")

    df = pd.DataFrame(list(output_by_polygon.values()))
    # Column ordering: id, name, then requested params in order.
    order = ["polygon_id", "polygon_name"] + [p for p in parameters if p in df.columns]
    df = df[order]
    return df.sort_values("polygon_id").reset_index(drop=True)
