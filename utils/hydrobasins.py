"""
HydroBASINS watershed selector for use as an alternative AOI input.

HydroBASINS (Lehner & Grill 2013) provides a global hierarchy of
watersheds at Pfafstetter levels 1-12. On Earth Engine:

  Level 4: continent-scale major basins (~40 features globally)
  Level 6: sub-basins of major rivers (~1,000)
  Level 8: sub-sub-basins                (~10,000)
  Level 12: smallest hydrologic units    (~1,000,000)

The wrapper fetches basin polygons that intersect an African country
(or the whole continent) and returns them as a GeoDataFrame ready to
drop into `st.session_state.uploaded_geodataframe` — so every
polygon-input source in the app (LULC, hydrology, forest, africa,
population, land_degradation, forest_biomass) can consume the result.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

from data_sources.earth_engine_utils import EarthEngineClient


LEVEL_ASSETS = {
    4:  "WWF/HydroSHEDS/v1/Basins/hybas_4",
    6:  "WWF/HydroSHEDS/v1/Basins/hybas_6",
    8:  "WWF/HydroSHEDS/v1/Basins/hybas_8",
    12: "WWF/HydroSHEDS/v1/Basins/hybas_12",
}


def get_available_levels() -> List[int]:
    return sorted(LEVEL_ASSETS.keys())


def gdf_from_watersheds(
    level: int,
    countries: Optional[List[str]] = None,
    hybas_ids: Optional[List[int]] = None,
    credentials_dict: Optional[Dict] = None,
    max_features: int = 500,
) -> gpd.GeoDataFrame:
    """Fetch HydroBASINS polygons matching the filter and return them as
    a GeoDataFrame.

    Filters supported:
      - `hybas_ids`: exact HYBAS_ID match (fastest, most precise)
      - `countries`: list of ADM0_NAME strings from FAO GAUL 2015.
        Basins whose bounding-box intersects any of those countries'
        polygons are returned.
      - If neither is supplied, we refuse (returning all of level 4 is
        cheap, but level 6+ would spam the caller).
    """
    if level not in LEVEL_ASSETS:
        raise ValueError(f"Unsupported HydroBASINS level: {level}")
    if not (hybas_ids or countries):
        raise ValueError(
            "Provide at least one of hybas_ids or countries to filter with."
        )

    if credentials_dict:
        c = EarthEngineClient(credentials_dict=credentials_dict)
        if not c.initialized:
            raise RuntimeError("EE init failed")

    fc = ee.FeatureCollection(LEVEL_ASSETS[level])

    if hybas_ids:
        fc = fc.filter(ee.Filter.inList("HYBAS_ID", list(hybas_ids)))
    else:
        # Intersect the basin collection with the union of country
        # polygons from GAUL. bounds() first shrinks the intersect cost.
        gaul = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(
            ee.Filter.inList("ADM0_NAME", list(countries))
        )
        fc = fc.filterBounds(gaul.geometry())

    server_feats = fc.limit(max_features).getInfo().get("features", [])
    if not server_feats:
        return gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")

    rows = []
    for feat in server_feats:
        props = feat.get("properties") or {}
        geom_json = feat.get("geometry")
        try:
            geom = shape(geom_json)
        except Exception:
            continue
        rows.append({
            "HYBAS_ID": int(props.get("HYBAS_ID", -1)),
            "NEXT_DOWN": props.get("NEXT_DOWN"),
            "MAIN_BAS":  props.get("MAIN_BAS"),
            "SUB_AREA":  props.get("SUB_AREA"),
            "geometry":  geom,
            "name":      f"HYBAS_{props.get('HYBAS_ID')}",
        })
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
