import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import tempfile
import json

# Import data source modules
from data_sources import (
    nasa_power, openweather, era5, modis, chirps, lulc, drought_indices, phenology,
    hydrology, soil_moisture, land_degradation, productivity, forest_biomass,
)

# Import utilities
from utils.africa_locations import (
    get_countries, 
    get_admin_division_type,
    get_divisions_for_country,
    get_sub_divisions,
    get_selected_locations as get_africa_locations
)
from utils.shapefile_handler import (
    read_shapefile,
    extract_locations_from_shapefile,
    validate_shapefile_locations,
    extract_shapefile_from_zip,
)
from utils.polygon_sampler import get_sampling_summary
from utils.kml_handler import (
    read_kml_file,
    extract_locations_from_kml,
    validate_kml_locations,
)
from utils.export_handler import (
    export_to_csv,
    export_to_json,
    export_to_geojson,
    export_to_shapefile,
    export_to_excel,
    get_export_filename,
    get_export_mime_type,
)
from utils.analytics import init_analytics
from utils.earth_globe import (
    create_earth_globe,
    create_animated_earth_globe,
    create_location_zoom_globe,
)
from utils.satellite_view import create_satellite_map
from utils.glassmorphism_theme import get_glassmorphism_css

# Load Earth Engine credentials (for MODIS and CHIRPS)
def load_ee_credentials():
    """Load Earth Engine service account credentials from Streamlit secrets or local file"""
    try:
        # First, try Streamlit Cloud secrets (for deployment)
        try:
            if hasattr(st, 'secrets') and 'gee_credentials' in st.secrets:
                return dict(st.secrets['gee_credentials'])
        except Exception:
            # Silently continue if secrets not available (expected for local dev)
            pass
        
        # Fallback to local file (for development)
        creds_path = "ee_credentials.json"
        if os.path.exists(creds_path):
            with open(creds_path, 'r') as f:
                return json.load(f)
        
        return None
    except Exception as e:
        # Only show warning for actual errors, not missing secrets
        if "secrets" not in str(e).lower():
            st.sidebar.warning(f"Could not load Earth Engine credentials: {str(e)}")
        return None

ee_credentials = load_ee_credentials()

# Initialize analytics
analytics = init_analytics()

# Page configuration
st.set_page_config(
    page_title="Weather Data Portal",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Glassmorphism Theme
st.markdown(get_glassmorphism_css(), unsafe_allow_html=True)

# Mobile-friendly sidebar toggle - simple JavaScript
st.markdown("""
<!-- Mobile menu button with simple toggle -->
<div class="mobile-menu-btn" onclick="
    const sidebar = document.querySelector('[data-testid=stSidebar]');
    if (sidebar) {
        const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
        sidebar.setAttribute('aria-expanded', !isExpanded);
    }
">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z"/>
    </svg>
</div>
""", unsafe_allow_html=True)

# Compact Header with Glassmorphism Design
st.markdown("""
<div style='text-align: center; padding: 1rem 0 0.5rem 0; margin-bottom: 1rem;'>
    <h1 style='font-size: 2.2rem; margin-bottom: 0.3rem; line-height: 1.2;'>🌦️ Weather Data Portal for Africa</h1>
    <p style='font-size: 0.95rem; color: #9ca3af; font-weight: 400; margin: 0.3rem 0;'>
        Download historical weather data from NASA POWER, OpenWeather, ERA5, MODIS & CHIRPS for African locations
    </p>
    <p style='font-size: 0.85rem; color: #6b7280; margin: 0.2rem 0;'>
        <strong style='color: #9ca3af;'>Coverage:</strong> 54 African countries • All administrative divisions • 
        <em>By Victor Iko-ojo Idakwo (RTP, MNITP, MGEOSON)</em>
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "fetched_data" not in st.session_state:
    st.session_state.fetched_data = None
if "selected_locations" not in st.session_state:
    st.session_state.selected_locations = None
if "current_data_source" not in st.session_state:
    st.session_state.current_data_source = None
if "uploaded_geodataframe" not in st.session_state:
    st.session_state.uploaded_geodataframe = None
if "lulc_change_long" not in st.session_state:
    st.session_state.lulc_change_long = None
if "lulc_composition_long" not in st.session_state:
    st.session_state.lulc_composition_long = None
if "lulc_aoi_gdf" not in st.session_state:
    st.session_state.lulc_aoi_gdf = None
if "lulc_last_dataset" not in st.session_state:
    st.session_state.lulc_last_dataset = None
if "lulc_last_year" not in st.session_state:
    st.session_state.lulc_last_year = None
if "lulc_last_year_to" not in st.session_state:
    st.session_state.lulc_last_year_to = None

# Track page visit (once per session)
analytics.track_visit()

# Sidebar for data source and parameters
st.sidebar.header("📊 Data Source Selection")

# Data source selection
data_sources = {
    "NASA POWER": "nasa_power",
    "OpenWeather API": "openweather",
    "ERA5 (Copernicus)": "era5",
    "MODIS": "modis",
    "CHIRPS": "chirps",
    "Land Cover (LULC)": "lulc",
    "Drought & Vegetation Indices": "drought_indices",
    "Vegetation Phenology (annual)": "phenology",
    "Hydrology (Global Surface Water)": "hydrology",
    "Soil Moisture (SMAP)": "soil_moisture",
    "Fire + Forest Loss (MODIS + FIRMS + Hansen)": "land_degradation",
    "Vegetation Productivity (LAI/FAPAR/ET/GPP)": "productivity",
    "Forest Biomass & Structure": "forest_biomass",
}

selected_source = st.sidebar.selectbox(
    "Select Data Source",
    options=list(data_sources.keys()),
    help="Choose the weather data source to query"
)

source_key = data_sources[selected_source]

# Show data source information
if source_key == "nasa_power":
    st.sidebar.info("📡 **NASA POWER**: Historical data with ~7 day latency. Data available from 1981 to ~7 days ago.")
elif source_key == "openweather":
    st.sidebar.warning("""
    🌤️ **OpenWeather Free Tier**:
    - ✅ Current weather
    - ✅ 7-day forecast
    - ❌ Historical data (requires paid subscription)
    
    **For historical weather data**, use **NASA POWER** instead (free, no API key needed).
    """)
elif source_key == "era5":
    st.sidebar.success("""
    🌍 **ERA5-Land via Google Earth Engine**
    
    ✅ Now using Earth Engine (No CDS token needed!)
    
    **Available Data:**
    - Temperature, precipitation, wind
    - Hourly resolution (aggregates to daily)
    - Global coverage at ~11km resolution
    
    **Benefits:**
    - No CDS account/token required
    - Faster than CDS API (seconds vs minutes)
    - Uses same Earth Engine credentials as MODIS/CHIRPS
    """)
elif source_key == "modis":
    st.sidebar.success("""
    🛰️ **MODIS via Google Earth Engine**
    
    ✅ Now functional!
    
    **Available Data:**
    - Land Surface Temperature (LST)
    - Vegetation Indices (NDVI, EVI)
    - Real satellite data from Earth Engine
    
    **Requirements:**
    Earth Engine service account credentials (provided)
    """)
elif source_key == "chirps":
    st.sidebar.success("""
    🌧️ **CHIRPS via Google Earth Engine**

    ✅ Now functional!

    **Available Data:**
    - Daily precipitation (mm)
    - Global coverage
    - Real CHIRPS data from Earth Engine

    **Requirements:**
    Earth Engine service account credentials (provided)
    """)
elif source_key == "phenology":
    st.sidebar.success("""
    🌱 **Vegetation Phenology (annual)**

    For each location and year, extracts seasonal timing and magnitude
    from the MODIS 16-day NDVI series:

    - **SOS_DOY / EOS_DOY** — Start / End of Season, day-of-year of the
      NDVI ascending / descending crossing at 20 % of amplitude.
    - **LOS_DAYS** — Length of Season (EOS − SOS).
    - **PEAK_NDVI / PEAK_DOY** — annual maximum NDVI and its day-of-year.
    - **NDVI_INTEGRAL** — sum of NDVI over the growing season
      (proxy for total productivity).

    **Source:** MODIS MOD13A1 (500 m, 16-day, 2000-present).

    **Note:** single-season detection. Bimodal regimes (East African
    long / short rains) collapse to the strongest peak. First fetch
    for a location can take a minute per year of data.
    """)
elif source_key == "drought_indices":
    st.sidebar.success("""
    💧 **Drought & Vegetation Indices**

    **SPI** (1 / 3 / 6 / 12 month, CHIRPS) — precipitation-only
    drought / wetness. Gamma-fit vs. 1991–2020 baseline.

    **SPEI** (1 / 3 / 6 / 12 month, CHIRPS + TerraClimate PET) —
    drought accounting for evaporative demand (P − PET). Catches
    heat-driven drought that SPI misses. Normal-fit vs. 1991–2020.
    Both indices: ≤ −1.5 = drought, ≥ +1.5 = very wet.

    **VCI / TCI / VHI** (0–100, MODIS) — vegetation-health composites
    from NDVI and daytime LST vs. 2001–2020 climatology. VHI < 40 =
    drought / vegetation stress.

    **Raw inputs:** precipitation, PET, water balance, NDVI, LST.

    **Requires:** Earth Engine credentials (already configured).
    **First fetch is slow** — 20–30 year baselines mean hundreds of
    Earth Engine calls per index family.
    """)
elif source_key == "productivity":
    st.sidebar.success("""
    🌿 **Vegetation Productivity (LAI / FAPAR / ET / GPP)**

    Monthly per-location time series from three complementary MODIS
    products, requestable together or independently.

    **MOD15A2H (structure):**
    - `LAI_M2M2` — Leaf Area Index (m²/m², monthly mean)
    - `FAPAR` — Fraction of Absorbed PAR (0–1, monthly mean)

    **MOD16A2 gap-filled (water flux):**
    - `ET_MM` — actual evapotranspiration (mm/month)
    - `PET_MM_MODIS` — potential evapotranspiration (mm/month)

    **PML_V2 (carbon flux):**
    - `GPP_GC_M2` — Gross Primary Productivity (gC/m²/month)

    **Coverage:** 2000–present, 500 m native, monthly aggregate.
    """)
elif source_key == "land_degradation":
    st.sidebar.success("""
    🔥 **Fire + Forest Loss (MODIS + FIRMS + Hansen)**

    Three complementary products, requestable together or
    independently. All emit one row per polygon per time step.

    **MODIS MCD64A1 (monthly burned area, ~60–90 day latency):**
    - `BURNED_AREA_KM2`, `PERCENT_BURNED`

    **FIRMS active fires (monthly aggregate, ~3-hour latency):**
    - `FIRE_DETECTIONS`, `MEAN_BRIGHTNESS_K`, `MEAN_CONFIDENCE`

    **Hansen Global Forest Change (annual, 30 m):**
    - `TREE_LOSS_KM2`, `PERCENT_LOSS`
    - `FOREST_2000_KM2`, `PERCENT_FOREST_2000` (year-2000 baseline
      at >30 % canopy cover)
    - Coverage: 2001–2025 loss years, refreshed annually.

    **Input:** upload a shapefile / KML polygon, or pick an African
    country / division. Point-only input is not supported for this
    source — these statistics need a real polygon.
    """)
elif source_key == "soil_moisture":
    st.sidebar.success("""
    🌊 **Soil Moisture (SMAP L4)**

    Monthly-mean **surface (0–5 cm)** and **root-zone (0–100 cm)**
    soil moisture at each point, plus anomalies against the 2015–2024
    per-calendar-month climatology.

    **Source:** SMAP L4 Global 9 km 3-hourly Soil Moisture (SPL4SMGP v7),
    aggregated to monthly means server-side.

    **Coverage:** 2015-04 → present, global.

    **Requires:** Earth Engine credentials.
    """)
elif source_key == "forest_biomass":
    st.sidebar.success("""
    🌳 **Forest Biomass & Structure**

    Static per-polygon statistics from three global forest datasets:

    - **ESA CCI Biomass v6.1** (100 m, 2015 or 2022 epoch) — mean AGB
      in t/ha, total biomass in megatonnes, area with biomass.
    - **Potapov Canopy Height 2020** (30 m) — mean tree-canopy height
      in metres, area with trees > 3 m.
    - **Global Mangrove Watch v3** (30 m, 2020) — mangrove area (km²)
      and percent of polygon.

    Input: upload a shapefile / KML polygon, or pick an African
    country / division.
    """)
elif source_key == "hydrology":
    st.sidebar.success("""
    💦 **Hydrology (Global Surface Water)**

    Per-polygon water statistics from **JRC Global Surface Water v1.4**
    (Pekel et al. 2016, 30 m, 1984–2021).

    **Outputs per AOI:**
    - Total polygon area (km²)
    - Water-ever area (any pixel with water history)
    - **Permanent water** (occurrence > 90 %)
    - **Seasonal water** (5 % < occurrence ≤ 90 %)
    - Water percent of polygon
    - Area-weighted mean occurrence and change in occurrence

    Great for reservoirs, lakes, wetlands, and river-corridor
    monitoring at national or watershed scale.
    """)
elif source_key == "lulc":
    st.sidebar.success("""
    🗺️ **Land Cover (LULC) via Google Earth Engine**

    **Available datasets:**
    - **ESRI Sentinel-2 LULC** (10 m, 2017–2024) — best for annual change
    - **ESA WorldCover** (10 m, 2020 / 2021) — single-year accuracy benchmark
    - **Dynamic World** (10 m, 2015–present) — newest data, sub-annual

    **Output:** per-polygon class composition (area & percent per class)
    on uploaded shapefile / KML or African admin divisions.
    """)

# Sidebar: LULC-specific controls OR weather-style parameter + date controls
# ---------------------------------------------------------------------------
# LULC uses a fundamentally different schema (categorical, annual snapshot,
# per-polygon area summary), so we branch the sidebar instead of forcing
# LULC into the weather-data widgets.

selected_params: list = []
temporal_resolution = None
start_date = None
end_date = None
date_range_days = 0
data_latency_days = 0
max_date = datetime.now()
lulc_dataset = None
lulc_year = None
lulc_year_to = None
lulc_analysis_mode = None
lulc_output_mode = None
lulc_show_sankey = False
lulc_drop_unchanged = False
hydro_dataset = None
forest_dataset = None

if source_key == "forest_biomass":
    st.sidebar.subheader("🌳 Forest Biomass & Structure")
    forest_dataset = st.sidebar.selectbox(
        "Dataset",
        options=forest_biomass.get_available_datasets(),
        index=0,
        help="Biomass: ESA CCI 2015/2022. Canopy: Potapov 2020. Mangroves: GMW v3 2020.",
    )
    ds_info_f = forest_biomass.get_dataset_info(forest_dataset)
    st.sidebar.caption(
        f"**Scale:** {ds_info_f['scale']} m  •  "
        f"**Year:** {ds_info_f['year']}  •  "
        f"{ds_info_f['attribution']}"
    )
elif source_key == "hydrology":
    st.sidebar.subheader("💦 Global Surface Water")
    hydro_dataset = st.sidebar.selectbox(
        "Dataset",
        options=hydrology.get_available_datasets(),
        index=0,
        help="JRC Global Surface Water v1.4 (Pekel et al. 2016)",
    )
    ds_info_h = hydrology.get_dataset_info(hydro_dataset)
    st.sidebar.caption(
        f"**Period:** {ds_info_h['period']}  •  "
        f"**Scale:** {ds_info_h['scale']} m  •  "
        f"**Attribution:** {ds_info_h['attribution']}"
    )
    st.sidebar.info(
        "**Input:** upload a shapefile / KML polygon, or pick an African "
        "country / division. Output: one row per polygon with water "
        "statistics."
    )
elif source_key == "lulc":
    st.sidebar.subheader("🗺️ LULC Dataset")
    lulc_dataset = st.sidebar.selectbox(
        "Dataset",
        options=lulc.get_available_datasets(),
        index=0,  # ESRI Sentinel-2 LULC is the default
        help="ESRI = best for annual change. WorldCover = best single-year. Dynamic World = newest.",
    )
    ds_info = lulc.get_dataset_info(lulc_dataset)
    years = ds_info["years_available"]
    default_year = ds_info["default_year"]

    lulc_analysis_mode = st.sidebar.radio(
        "Analysis mode",
        options=["Composition (single year)", "Change (two years)"],
        index=0,
        help="Composition = land-cover breakdown at one point in time. Change = transition matrix between two years.",
    )

    if lulc_analysis_mode == "Composition (single year)":
        lulc_year = st.sidebar.selectbox(
            "Year",
            options=years,
            index=years.index(default_year) if default_year in years else len(years) - 1,
            help="Year to compute land-cover composition for.",
        )
        lulc_output_mode = st.sidebar.selectbox(
            "Output format",
            options=["Composition (long)", "Composition (wide pivot)"],
            index=0,
            help="Long: one row per polygon × class. Wide: one row per polygon, one column per class.",
        )
    else:
        # Change mode. Requires at least two years available.
        if len(years) < 2:
            st.sidebar.error(
                f"{lulc_dataset} only has one year ({years[0]}) available — "
                "switch to ESRI Sentinel-2 or Dynamic World for change analysis."
            )
            lulc_year = years[0]
            lulc_year_to = years[0]
        else:
            col_a, col_b = st.sidebar.columns(2)
            with col_a:
                lulc_year = st.selectbox(
                    "From",
                    options=years,
                    index=0,
                    key="lulc_year_from",
                    help="Earlier year (baseline).",
                )
            with col_b:
                later_years = [y for y in years if y > lulc_year]
                if not later_years:
                    later_years = [years[-1]]
                lulc_year_to = st.selectbox(
                    "To",
                    options=later_years,
                    index=len(later_years) - 1,
                    key="lulc_year_to",
                    help="Later year (comparison).",
                )
        lulc_output_mode = st.sidebar.selectbox(
            "Output format",
            options=[
                "Change (long: every transition)",
                "Change (wide pivot: from x to matrix)",
            ],
            index=0,
        )
        lulc_show_sankey = st.sidebar.checkbox(
            "Show Sankey diagram of transitions",
            value=True,
            help="Visualize the flows between classes for the first polygon (or a polygon you pick).",
        )
        lulc_drop_unchanged = st.sidebar.checkbox(
            "Exclude unchanged pixels",
            value=False,
            help="Useful when you only care about *what changed* and want a smaller table.",
        )

    st.sidebar.caption(
        f"**Resolution:** {ds_info['scale']} m  •  "
        f"**Host:** {ds_info['host_note']}  •  "
        f"**License:** {ds_info['license']}"
    )

else:
    # ----- Weather-data sidebar (NASA POWER / OpenWeather / ERA5 / MODIS / CHIRPS) -----
    if source_key == "nasa_power":
        available_params = nasa_power.get_available_parameters()
        temporal_options = nasa_power.get_temporal_resolutions()
    elif source_key == "openweather":
        available_params = openweather.get_available_parameters()
        temporal_options = openweather.get_temporal_resolutions()
    elif source_key == "era5":
        available_params = era5.get_available_parameters()
        temporal_options = era5.get_temporal_resolutions()
    elif source_key == "modis":
        available_params = modis.get_available_parameters()
        temporal_options = modis.get_temporal_resolutions()
    elif source_key == "drought_indices":
        available_params = drought_indices.get_available_parameters()
        temporal_options = drought_indices.get_temporal_resolutions()
    elif source_key == "phenology":
        available_params = phenology.get_available_parameters()
        temporal_options = phenology.get_temporal_resolutions()
    elif source_key == "soil_moisture":
        available_params = soil_moisture.get_available_parameters()
        temporal_options = soil_moisture.get_temporal_resolutions()
    elif source_key == "land_degradation":
        available_params = land_degradation.get_available_parameters()
        temporal_options = land_degradation.get_temporal_resolutions()
    elif source_key == "productivity":
        available_params = productivity.get_available_parameters()
        temporal_options = productivity.get_temporal_resolutions()
    else:  # chirps
        available_params = chirps.get_available_parameters()
        temporal_options = chirps.get_temporal_resolutions()

    # Display available parameters by category
    st.sidebar.subheader("📋 Available Parameters")

    for category, params in available_params.items():
        # Use markdown header instead of expander to avoid keyboard arrow text
        st.sidebar.markdown(f"**📁 {category}**")
        for param_code, param_desc in params.items():
            # Create unique key by combining source, category, and param_code
            unique_key = f"param_{source_key}_{category.replace(' ', '_').replace('/', '_')}_{param_code}"
            if st.sidebar.checkbox(param_desc, key=unique_key):
                selected_params.append(param_code)
        st.sidebar.markdown("---")  # Separator between categories

    # Remove duplicates while preserving order
    selected_params = list(dict.fromkeys(selected_params))

    # Temporal resolution
    st.sidebar.subheader("⏰ Temporal Resolution")
    temporal_resolution = st.sidebar.selectbox(
        "Select Resolution",
        options=temporal_options,
        help="Choose the time interval for data aggregation"
    )

    # Date range selection
    st.sidebar.subheader("📅 Date Range")

    # Set date ranges based on data source and their latency
    if source_key == "openweather":
        # OpenWeather allows forecasts up to 7 days
        max_date = datetime.now() + timedelta(days=7)
        default_start = datetime.now() - timedelta(days=7)
        default_end = datetime.now() + timedelta(days=2)
        data_latency_days = 0
    elif source_key == "nasa_power":
        # NASA POWER has ~3-7 day data latency
        data_latency_days = 7
        max_date = datetime.now() - timedelta(days=data_latency_days)
        default_start = datetime.now() - timedelta(days=60)  # 2 months ago
        default_end = datetime.now() - timedelta(days=data_latency_days)
    elif source_key == "era5":
        # ERA5 has ~5 day latency
        data_latency_days = 5
        max_date = datetime.now() - timedelta(days=data_latency_days)
        default_start = datetime.now() - timedelta(days=60)
        default_end = datetime.now() - timedelta(days=data_latency_days)
    elif source_key == "drought_indices":
        # CHIRPS monthly settles about a month after the month ends.
        data_latency_days = 45
        max_date = datetime.now() - timedelta(days=data_latency_days)
        # Default to a 3-year window so SPI-12 has enough context to show trends.
        default_start = datetime.now().replace(month=1, day=1) - timedelta(days=365 * 3)
        default_end = max_date
    elif source_key == "phenology":
        # MOD13A1 composites have ~30-day latency; a full-season summary
        # needs a completed calendar year.
        data_latency_days = 30
        max_date = datetime.now() - timedelta(days=data_latency_days)
        default_start = datetime(datetime.now().year - 5, 1, 1)
        default_end = datetime(datetime.now().year - 1, 12, 31)
    elif source_key == "soil_moisture":
        # SMAP L4 has ~7-day latency; default to a 3-year window.
        data_latency_days = 7
        max_date = datetime.now() - timedelta(days=data_latency_days)
        default_start = datetime(datetime.now().year - 3, 1, 1)
        default_end = max_date
    elif source_key == "land_degradation":
        # MCD64A1 typically has ~60-90 day latency.
        data_latency_days = 90
        max_date = datetime.now() - timedelta(days=data_latency_days)
        default_start = datetime(datetime.now().year - 2, 1, 1)
        default_end = max_date
    elif source_key == "productivity":
        # MOD15A2H / MOD16A2 latency ~30-60 days.
        data_latency_days = 45
        max_date = datetime.now() - timedelta(days=data_latency_days)
        default_start = datetime(datetime.now().year - 3, 1, 1)
        default_end = max_date
    else:
        # Other sources - historical data with some latency
        data_latency_days = 3
        max_date = datetime.now() - timedelta(days=data_latency_days)
        default_start = datetime.now() - timedelta(days=30)
        default_end = datetime.now() - timedelta(days=data_latency_days)

    col1, col2 = st.sidebar.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            min_value=datetime(1990, 1, 1),
            max_value=max_date,
            help="Select the start date for data retrieval"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=default_end,
            min_value=datetime(1990, 1, 1),
            max_value=max_date,
            help="Select the end date for data retrieval"
        )

    # Validate date range
    if start_date > end_date:
        st.sidebar.error("⚠️ Start date must be before end date")
    else:
        date_range_days = (end_date - start_date).days
        st.sidebar.info(f"📅 Date range: {date_range_days + 1} days")

        # Show data latency warning
        if source_key != "openweather" and data_latency_days > 0:
            days_from_today = (datetime.now().date() - end_date).days
            if days_from_today < data_latency_days:
                st.sidebar.warning(f"⏱️ {selected_source} has ~{data_latency_days} day data latency. Latest available data is from {max_date.strftime('%Y-%m-%d')}.")

    # API Keys (if needed)
    if source_key == "openweather":
        st.sidebar.subheader("🔑 API Configuration")
        api_key = st.sidebar.text_input(
            "OpenWeather API Key",
            type="password",
            help="Enter your OpenWeather API key"
        )
    elif source_key == "era5":
        st.sidebar.info("""
        ℹ️ **No API Key Required!**

        ERA5 now uses the same Earth Engine credentials as MODIS/CHIRPS.
        No separate CDS account or token needed.
        """)

# Location selection with glassmorphism header
st.markdown("""
<div style='background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin: 1rem 0 0.75rem 0;
            box-shadow: 0 4px 20px 0 rgba(59, 130, 246, 0.15);'>
    <h2 style='margin: 0; font-size: 1.5rem; line-height: 1.3;'>📍 Select Locations</h2>
    <p style='margin: 0.25rem 0 0 0; color: #9ca3af; font-size: 0.9rem;'>Choose your data collection points</p>
</div>
""", unsafe_allow_html=True)

# Location selection method
location_method = st.radio(
    "Choose location selection method:",
    options=["African Countries/Divisions", "Upload Shapefile", "Upload KML/KMZ"],
    horizontal=True,
)

locations_list = []

# Create two-column layout: Location Selection (left) and Satellite View (right)
left_col, right_col = st.columns([1, 1], gap="medium")

with left_col:
    if location_method == "African Countries/Divisions":
        # Clear uploaded GeoDataFrame when using African Countries
        st.session_state.uploaded_geodataframe = None
        
        # Get all countries
        countries = get_countries()
        
        # Country selection
        st.subheader("🌍 Select Countries")
        selected_countries = st.multiselect(
            "Choose African countries",
            options=countries,
            default=["Nigeria"],
            help="Select one or more African countries"
        )
        
        if selected_countries:
            # Division selection for each country
            st.subheader("📌 Select Administrative Divisions")
            
            selected_divisions = {}
            selected_sub_divisions = {}
            
            for country in selected_countries:
                # Get division type for this country
                division_type = get_admin_division_type(country)
                divisions = get_divisions_for_country(country)
                
                if divisions:
                    st.markdown(f"**{country}** ({division_type}s)")
                    selected = st.multiselect(
                        f"Select {division_type}s",
                        options=divisions,
                        key=f"div_{country}",
                        help=f"Select specific {division_type}s in {country}, or leave empty to use capital"
                    )
                    if selected:
                        selected_divisions[country] = selected
                        
                        # Show sub-division selection for all countries with available data
                        st.markdown("**🏘️ Select Sub-divisions (Optional)**")
                        
                        # Define sub-division labels for each country
                        sub_div_labels = {
                            "Nigeria": "LGA",
                            "Kenya": "Sub-county",
                            "South Africa": "Municipality",
                            "Ghana": "District",
                            "Egypt": "District",
                        }
                        
                        sub_div_label = sub_div_labels.get(country, "Sub-division")
                        
                        country_sub_divs = {}
                        has_sub_divs = False
                        
                        for division in selected:
                            sub_divs = get_sub_divisions(country, division)
                            if sub_divs:
                                has_sub_divs = True
                                selected_subs = st.multiselect(
                                    f"{sub_div_label}s in {division}",
                                    options=sub_divs,
                                    key=f"sub_{country}_{division}",
                                    help=f"Select specific {sub_div_label}s, or leave empty to use {division} centroid"
                                )
                                if selected_subs:
                                    country_sub_divs[division] = selected_subs
                        
                        if country_sub_divs:
                            selected_sub_divisions[country] = country_sub_divs
                        elif not has_sub_divs:
                            st.caption(f"ℹ️ No {sub_div_label}s available for selected {division_type}s")
                else:
                    st.info(f"ℹ️ {country}: Using capital city (detailed {division_type}s not yet available)")
            
            # Get locations based on selection priority: LGAs > States > Capitals
            if selected_sub_divisions:
                # User selected specific LGAs
                locations_list = get_africa_locations(sub_divisions=selected_sub_divisions)
            elif selected_divisions:
                # User selected specific divisions (states/regions)
                locations_list = get_africa_locations(divisions=selected_divisions)
            else:
                # Use capital cities for all selected countries
                locations_list = get_africa_locations(countries=selected_countries)

    elif location_method == "Upload Shapefile":
        st.subheader("Upload Shapefile")
        st.markdown("""
        Upload a ZIP file containing your shapefile (.shp, .shx, .dbf, .prj files).
        - For **polygon** geometries: centroid will be extracted
        - For **point** geometries: points will be used directly
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a ZIP file",
            type=["zip"],
            help="Upload a ZIP file containing all shapefile components"
        )
        
        if uploaded_file is not None:
            try:
                # Extract shapefile from ZIP
                shp_path = extract_shapefile_from_zip(uploaded_file)
                
                # Read shapefile
                gdf = read_shapefile(shp_path)
                
                # Store GeoDataFrame in session state
                st.session_state.uploaded_geodataframe = gdf
                
                # Display shapefile info
                st.success(f"✅ Shapefile loaded successfully! Found {len(gdf)} features.")
                
                # Show preview
                if st.checkbox("📋 Preview Shapefile Data", key="preview_shp"):
                    st.dataframe(gdf.head(10))
                
                # Extract locations with polygon sampling
                locations_dict = extract_locations_from_shapefile(gdf, use_polygon_sampling=True)

                # Sampling summary is only meaningful for weather sources that
                # actually query per-point. LULC uses the polygon directly.
                if source_key not in ("lulc", "hydrology", "land_degradation"):
                    summary = get_sampling_summary(locations_dict)
                    if summary['sampling_points'] > 0:
                        st.info(f"""
                        📊 **Polygon Sampling Active**
                        - **{summary['num_polygons']}** polygon(s) detected
                        - **{summary['sampling_points']}** sampling points generated
                        - **{summary['avg_points_per_polygon']:.1f}** points per polygon (average)
                        - Weather data will be downloaded for all sampling points
                        """)
                else:
                    kind_map = {
                        "hydrology": "surface-water",
                        "land_degradation": "burned-area",
                        "lulc": "LULC",
                    }
                    kind = kind_map.get(source_key, "LULC")
                    st.info(
                        f"🗺️ **{len(gdf)} polygon(s) ready for {kind} analysis.** "
                        "Statistics are computed on the polygon directly — "
                        "no point sampling is used."
                    )

                # Validate locations
                is_valid, error_msg = validate_shapefile_locations(locations_dict)
                if not is_valid:
                    st.warning(f"⚠️ Warning: {error_msg}")

                # Convert to expected tuple format: (lat, lon, name)
                locations_list = [(loc["lat"], loc["lon"], loc["name"]) for loc in locations_dict]

            except Exception as e:
                st.error(f"❌ Error processing shapefile: {str(e)}")
                st.session_state.uploaded_geodataframe = None

    else:  # Upload KML/KMZ
        st.subheader("Upload KML/KMZ")
        st.markdown("""
        Upload a KML or KMZ file containing location data.
        - **KML**: Direct XML file with location data
        - **KMZ**: Zipped KML file (Google Earth format)
        - For **polygon** geometries: centroid will be extracted
        - For **point** geometries: points will be used directly
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a KML or KMZ file",
            type=["kml", "kmz"],
            help="Upload a KML or KMZ file with location data"
        )
        
        if uploaded_file is not None:
            try:
                # Save uploaded file to temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    kml_path = tmp_file.name
                
                # Read KML/KMZ file
                gdf = read_kml_file(kml_path)
                
                # Store GeoDataFrame in session state
                st.session_state.uploaded_geodataframe = gdf
                
                # Display file info
                st.success(f"✅ KML/KMZ loaded successfully! Found {len(gdf)} features.")
                
                # Show preview
                if st.checkbox("📋 Preview KML/KMZ Data", key="preview_kml"):
                    st.dataframe(gdf.head(10))
                
                # Extract locations with polygon sampling
                locations_dict = extract_locations_from_kml(gdf, use_polygon_sampling=True)

                # Sampling summary is only meaningful for weather sources that
                # actually query per-point. LULC uses the polygon directly.
                if source_key not in ("lulc", "hydrology", "land_degradation"):
                    summary = get_sampling_summary(locations_dict)
                    if summary['sampling_points'] > 0:
                        st.info(f"""
                        📊 **Polygon Sampling Active**
                        - **{summary['num_polygons']}** polygon(s) detected
                        - **{summary['sampling_points']}** sampling points generated
                        - **{summary['avg_points_per_polygon']:.1f}** points per polygon (average)
                        - Weather data will be downloaded for all sampling points
                        """)
                else:
                    kind_map = {
                        "hydrology": "surface-water",
                        "land_degradation": "burned-area",
                        "lulc": "LULC",
                    }
                    kind = kind_map.get(source_key, "LULC")
                    st.info(
                        f"🗺️ **{len(gdf)} polygon(s) ready for {kind} analysis.** "
                        "Statistics are computed on the polygon directly — "
                        "no point sampling is used."
                    )
                
                # Validate locations
                is_valid, error_msg = validate_kml_locations(locations_dict)
                if not is_valid:
                    st.warning(f"⚠️ Warning: {error_msg}")
                
                # Convert to expected tuple format: (lat, lon, name)
                locations_list = [(loc["lat"], loc["lon"], loc["name"]) for loc in locations_dict]
                
                # Clean up temporary file
                os.unlink(kml_path)
                
            except Exception as e:
                st.error(f"❌ Error processing KML/KMZ file: {str(e)}")
                st.session_state.uploaded_geodataframe = None
                # Clean up temporary file if it exists
                if 'kml_path' in locals() and os.path.exists(kml_path):
                    os.unlink(kml_path)

# Add satellite view in the right column
with right_col:
    st.subheader("🛰️ Google Satellite View")
    
    if locations_list:
        try:
            # Create satellite map with Google imagery
            # Pass GeoDataFrame if available (for polygons/actual geometries)
            satellite_map = create_satellite_map(
                locations_list, 
                height=600,
                gdf=st.session_state.uploaded_geodataframe
            )
            
            # Display the map
            from streamlit_folium import st_folium
            st_folium(satellite_map, width=None, height=600)
            
        except Exception as e:
            st.warning(f"⚠️ Satellite view unavailable: {str(e)}")
            st.info("💡 Select locations on the left to view satellite imagery")
    else:
        st.info("💡 Select locations on the left to view satellite imagery")
        # Show placeholder map of Africa
        try:
            placeholder_map = create_satellite_map([], height=600)
            from streamlit_folium import st_folium
            st_folium(placeholder_map, width=None, height=600)
        except:
            pass

# Display selected locations
if locations_list:
    if (
        source_key in ("lulc", "hydrology", "land_degradation")
        and st.session_state.uploaded_geodataframe is not None
    ):
        n_poly = len(st.session_state.uploaded_geodataframe)
        analysis_label = {
            "lulc": "LULC analysis",
            "hydrology": "surface-water analysis",
            "land_degradation": "burned-area analysis",
        }.get(source_key, "polygon analysis")
        st.success(f"✅ {n_poly} polygon(s) ready for {analysis_label}")
    else:
        st.success(f"✅ {len(locations_list)} location(s) selected")

    if st.checkbox("📍 View Selected Locations", key="view_locations"):
        # locations_list format: [(lat, lon, name), ...]
        df_locations = pd.DataFrame(locations_list, columns=["Latitude", "Longitude", "Location Name"])
        st.dataframe(df_locations)

    st.session_state.selected_locations = locations_list

# Fetch Data section with glassmorphism header
st.markdown("""
<div style='background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin: 1rem 0 0.75rem 0;
            box-shadow: 0 4px 20px 0 rgba(34, 197, 94, 0.15);'>
    <h2 style='margin: 0; font-size: 1.5rem; line-height: 1.3;'>🚀 Fetch Data</h2>
    <p style='margin: 0.25rem 0 0 0; color: #9ca3af; font-size: 0.9rem;'>Download weather data for selected locations</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Fetch summary + dispatch
# ---------------------------------------------------------------------------
# Branches by source. LULC is a separate flow because the input shape
# (polygons, not points) and the output schema (per-polygon class composition,
# no time axis) differ from the weather sources.

if source_key == "forest_biomass":
    have_uploaded_gdf = st.session_state.uploaded_geodataframe is not None
    have_admin_selection = (
        location_method == "African Countries/Divisions"
        and bool(locations_list)
    )
    fb_ready = bool(forest_dataset and (have_uploaded_gdf or have_admin_selection))
    if fb_ready:
        n_polys = (
            len(st.session_state.uploaded_geodataframe)
            if have_uploaded_gdf
            else len({(loc[2].split('_point_')[0] if '_point_' in loc[2] else loc[2]) for loc in locations_list})
        )
        st.info(f"""
        **Ready to fetch:**
        - 🌳 Data Source: {selected_source}
        - 📚 Dataset: {forest_dataset}
        - 🧭 AOI: {n_polys} polygon(s)
        """)
    if st.button("Fetch Forest Statistics", type="primary", disabled=not fb_ready, key="fetch_fb_btn"):
        if not ee_credentials:
            st.error("❌ Earth Engine credentials not found.")
        else:
            with st.spinner(f"Computing {forest_dataset} statistics..."):
                try:
                    if have_uploaded_gdf:
                        aoi_gdf = st.session_state.uploaded_geodataframe.copy()
                    else:
                        admin_countries = list(selected_countries) if 'selected_countries' in dir() else []
                        admin_divisions = (
                            dict(selected_divisions) if 'selected_divisions' in dir() and selected_divisions else None
                        )
                        st.info("Resolving admin polygons via FAO GAUL 2015...")
                        aoi_gdf = lulc.gdf_from_admin_selection(
                            countries=admin_countries,
                            divisions=admin_divisions,
                            credentials_dict=ee_credentials,
                        )
                    df = forest_biomass.fetch_biomass_stats_from_gdf(
                        aoi_gdf=aoi_gdf,
                        dataset_name=forest_dataset,
                        credentials_dict=ee_credentials,
                    )
                    if df is not None and not df.empty:
                        st.session_state.fetched_data = df
                        st.session_state.current_data_source = f"{selected_source} | {forest_dataset}"
                        st.session_state.lulc_change_long = None
                        st.session_state.lulc_composition_long = None
                        st.session_state.lulc_aoi_gdf = None
                        st.success(f"✅ Forest statistics for {len(df)} polygon(s).")
                        st.caption(f"📜 {forest_biomass.get_dataset_info(forest_dataset)['attribution']}")
                        st.balloons()
                    else:
                        st.warning("⚠️ No polygons produced results.")
                except Exception as e:
                    st.error(f"❌ Forest-biomass fetch failed: {e}")

elif source_key == "hydrology":
    have_uploaded_gdf = st.session_state.uploaded_geodataframe is not None
    have_admin_selection = (
        location_method == "African Countries/Divisions"
        and bool(locations_list)
    )
    hydro_ready = bool(hydro_dataset and (have_uploaded_gdf or have_admin_selection))

    if hydro_ready:
        if have_uploaded_gdf:
            n_polys = len(st.session_state.uploaded_geodataframe)
            aoi_desc = f"{n_polys} polygon(s) from upload"
        else:
            n_polys = len(set(
                loc[2].split('_point_')[0] if '_point_' in loc[2] else loc[2]
                for loc in locations_list
            ))
            aoi_desc = f"{n_polys} admin division(s) (will resolve via FAO GAUL)"
        st.info(f"""
        **Ready to fetch:**
        - 💦 Data Source: {selected_source}
        - 📚 Dataset: {hydro_dataset}
        - 🧭 AOI: {aoi_desc}
        """)

    fetch_hydro = st.button(
        "Fetch Water Statistics",
        type="primary",
        disabled=not hydro_ready,
        key="fetch_hydro_btn",
    )
    if fetch_hydro:
        if not ee_credentials:
            st.error("❌ Earth Engine credentials not found.")
        else:
            with st.spinner(f"Computing Global Surface Water statistics..."):
                try:
                    if have_uploaded_gdf:
                        aoi_gdf = st.session_state.uploaded_geodataframe.copy()
                    else:
                        admin_countries = list(selected_countries) if 'selected_countries' in dir() else []
                        admin_divisions = (
                            dict(selected_divisions) if 'selected_divisions' in dir() and selected_divisions else None
                        )
                        st.info("Resolving admin polygons via FAO GAUL 2015...")
                        aoi_gdf = lulc.gdf_from_admin_selection(
                            countries=admin_countries,
                            divisions=admin_divisions,
                            credentials_dict=ee_credentials,
                        )

                    df = hydrology.fetch_gsw_stats_from_gdf(
                        aoi_gdf=aoi_gdf,
                        dataset_name=hydro_dataset,
                        credentials_dict=ee_credentials,
                    )
                    if df is not None and not df.empty:
                        st.session_state.fetched_data = df
                        st.session_state.current_data_source = (
                            f"{selected_source} | {hydro_dataset}"
                        )
                        # These session-state keys are checked by the LULC-family
                        # export gating; clear them so hydrology output goes down
                        # the plain CSV/JSON/Excel path.
                        st.session_state.lulc_change_long = None
                        st.session_state.lulc_composition_long = None
                        st.session_state.lulc_aoi_gdf = None
                        analytics.track_data_source_usage(
                            data_source=f"{selected_source} | {hydro_dataset}",
                            parameters=["gsw_stats"],
                            locations_count=len(aoi_gdf),
                            date_range=hydrology.get_dataset_info(hydro_dataset)["period"],
                        )
                        st.success(
                            f"✅ Surface-water statistics computed for {len(df)} polygon(s)."
                        )
                        st.caption(
                            f"📜 **Attribution:** "
                            f"{hydrology.get_dataset_info(hydro_dataset)['attribution']}"
                        )
                        st.balloons()
                    else:
                        st.warning("⚠️ No polygons produced results.")
                except Exception as e:
                    st.error(f"❌ Hydrology fetch failed: {e}")
                    if st.checkbox("🔍 View Error Details", key="hydro_err"):
                        st.code(str(e))

elif source_key == "lulc":
    # Determine if we have a usable polygon AOI
    have_uploaded_gdf = st.session_state.uploaded_geodataframe is not None
    have_admin_selection = (
        location_method == "African Countries/Divisions"
        and bool(locations_list)  # locations_list non-empty implies countries chosen
    )
    is_change_mode = lulc_analysis_mode == "Change (two years)"
    years_ok = (
        (not is_change_mode and lulc_year is not None)
        or (is_change_mode and lulc_year is not None and lulc_year_to is not None and lulc_year != lulc_year_to)
    )
    lulc_ready = bool(
        lulc_dataset and years_ok and (have_uploaded_gdf or have_admin_selection)
    )

    if lulc_ready:
        ds_info = lulc.get_dataset_info(lulc_dataset)
        if have_uploaded_gdf:
            n_polys = len(st.session_state.uploaded_geodataframe)
            aoi_desc = f"{n_polys} polygon(s) from upload"
        else:
            n_polys = len(set(
                loc[2].split('_point_')[0] if '_point_' in loc[2] else loc[2]
                for loc in locations_list
            ))
            aoi_desc = f"{n_polys} admin division(s) (will resolve via FAO GAUL)"
        if is_change_mode:
            year_desc = f"{lulc_year} → {lulc_year_to}"
        else:
            year_desc = str(lulc_year)
        st.info(f"""
        **Ready to fetch:**
        - 🗺️ Data Source: {selected_source}
        - 📚 Dataset: {lulc_dataset}
        - 📅 Year(s): {year_desc}
        - 🧭 AOI: {aoi_desc}
        - 📐 Output: {lulc_output_mode}
        - 📏 Resolution: {ds_info['scale']} m
        """)

    fetch_clicked = st.button(
        "Fetch Land Cover Data",
        type="primary",
        disabled=not lulc_ready,
        key="fetch_lulc_btn",
    )
    if fetch_clicked:
        if not ee_credentials:
            st.error("❌ Earth Engine credentials not found. Add ee_credentials.json or configure Streamlit secrets.")
        else:
            spinner_msg = (
                f"Computing {lulc_dataset} change {lulc_year} → {lulc_year_to}..."
                if is_change_mode else
                f"Fetching {lulc_dataset} for {lulc_year}..."
            )
            with st.spinner(spinner_msg):
                try:
                    # Resolve AOI: uploaded gdf takes precedence over admin selection.
                    if have_uploaded_gdf:
                        aoi_gdf = st.session_state.uploaded_geodataframe.copy()
                    else:
                        admin_countries = list(selected_countries) if 'selected_countries' in dir() else []
                        admin_divisions = (
                            dict(selected_divisions) if 'selected_divisions' in dir() and selected_divisions else None
                        )
                        st.info("Resolving admin polygons via FAO GAUL 2015...")
                        aoi_gdf = lulc.gdf_from_admin_selection(
                            countries=admin_countries,
                            divisions=admin_divisions,
                            credentials_dict=ee_credentials,
                        )

                    if is_change_mode:
                        df_long = lulc.fetch_lulc_change_from_gdf(
                            gdf=aoi_gdf,
                            dataset_name=lulc_dataset,
                            year_from=int(lulc_year),
                            year_to=int(lulc_year_to),
                            credentials_dict=ee_credentials,
                            drop_unchanged=lulc_drop_unchanged,
                        )
                        # Keep long form around for Sankey; pivot for display if asked.
                        if (
                            lulc_output_mode == "Change (wide pivot: from x to matrix)"
                            and not df_long.empty
                        ):
                            df = lulc.change_to_wide(df_long, value="area_km2")
                        else:
                            df = df_long
                        st.session_state.lulc_change_long = df_long  # for Sankey + spatial exports
                        st.session_state.lulc_composition_long = None
                    else:
                        df_long = lulc.fetch_lulc_composition_from_gdf(
                            gdf=aoi_gdf,
                            dataset_name=lulc_dataset,
                            year=int(lulc_year),
                            credentials_dict=ee_credentials,
                        )
                        if lulc_output_mode == "Composition (wide pivot)" and not df_long.empty:
                            df = lulc.composition_to_wide(df_long, value="percent")
                        else:
                            df = df_long
                        st.session_state.lulc_change_long = None
                        st.session_state.lulc_composition_long = df_long  # for spatial exports

                    # Cache AOI + dataset/year for downstream spatial exports and raster clips.
                    st.session_state.lulc_aoi_gdf = aoi_gdf
                    st.session_state.lulc_last_dataset = lulc_dataset
                    st.session_state.lulc_last_year = int(lulc_year)
                    st.session_state.lulc_last_year_to = (
                        int(lulc_year_to) if is_change_mode else None
                    )

                    if df is not None and not df.empty:
                        st.session_state.fetched_data = df
                        st.session_state.current_data_source = (
                            f"{selected_source} | {lulc_dataset} | {year_desc}"
                        )
                        analytics.track_data_source_usage(
                            data_source=f"{selected_source} | {lulc_dataset}",
                            parameters=[year_desc, lulc_output_mode],
                            locations_count=len(aoi_gdf),
                            date_range=year_desc,
                        )
                        st.success(
                            f"✅ {'Change' if is_change_mode else 'Composition'} retrieved: "
                            f"{len(df)} rows across {len(aoi_gdf)} polygon(s)."
                        )
                        st.caption(f"📜 **Attribution:** {lulc.get_dataset_info(lulc_dataset)['attribution']}")
                        st.balloons()
                    else:
                        st.warning("⚠️ No data returned. Polygon may be outside dataset coverage.")
                except Exception as e:
                    st.error(f"❌ Error fetching LULC data: {e}")
                    if st.checkbox("🔍 View Error Details", key="lulc_err"):
                        st.code(str(e))

    # --- Sankey diagram for the most recent change result, if requested ---
    if (
        lulc_analysis_mode == "Change (two years)"
        and lulc_show_sankey
        and st.session_state.get("lulc_change_long") is not None
        and not st.session_state.lulc_change_long.empty
    ):
        change_long = st.session_state.lulc_change_long
        polygon_names = sorted(change_long["polygon_name"].dropna().unique().tolist())
        sankey_polygon = st.selectbox(
            "Sankey: pick a polygon to visualize transitions for",
            options=polygon_names,
            index=0,
            key="lulc_sankey_polygon",
        )
        top_n = st.slider(
            "Show top N transitions by area",
            min_value=5, max_value=40, value=15, step=5,
            key="lulc_sankey_topn",
        )
        try:
            import plotly.graph_objects as go
            sub = change_long[change_long["polygon_name"] == sankey_polygon]
            sub = sub[~sub["is_unchanged"]].sort_values(
                "area_km2", ascending=False
            ).head(top_n)
            if sub.empty:
                st.info("No class transitions to display for this polygon.")
            else:
                yfrom = int(sub["year_from"].iloc[0])
                yto = int(sub["year_to"].iloc[0])
                from_classes = sub["from_class"].unique().tolist()
                to_classes = sub["to_class"].unique().tolist()
                labels = (
                    [f"{c} ({yfrom})" for c in from_classes]
                    + [f"{c} ({yto})" for c in to_classes]
                )
                src = [from_classes.index(r) for r in sub["from_class"]]
                tgt = [
                    len(from_classes) + to_classes.index(r)
                    for r in sub["to_class"]
                ]
                vals = sub["area_km2"].astype(float).tolist()
                fig = go.Figure(go.Sankey(
                    node=dict(label=labels, pad=15, thickness=18),
                    link=dict(source=src, target=tgt, value=vals),
                ))
                fig.update_layout(
                    title=f"{sankey_polygon}: {yfrom} → {yto} (top {len(sub)} transitions, km²)",
                    height=520,
                    margin=dict(l=10, r=10, t=50, b=10),
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info(f"Sankey unavailable: {e}")

# --- Weather-data preflight + fetch button (existing flow, gated) ----------
elif selected_params and locations_list and start_date <= end_date:
    date_range_days = (end_date - start_date).days + 1

    # Check for OpenWeather historical data limitation
    if source_key == "openweather":
        if end_date < datetime.now().date():
            st.error(f"""
            ❌ **OpenWeather Free Tier Does Not Support Historical Data**

            You selected dates in the past: {start_date} to {end_date}

            **OpenWeather Free Tier Only Provides:**
            - ✅ Current weather (today)
            - ✅ 7-day forecast (future dates)
            - ❌ Historical data (requires paid subscription)

            **Solutions:**
            1. **Use NASA POWER instead** (recommended):
               - Switch Data Source to "NASA POWER"
               - Free historical data from 1981 to ~7 days ago
               - No API key required

            2. **Use OpenWeather for current/forecast only**:
               - Select today's date or future dates (up to 7 days)
               - Keep your current API key

            3. **Upgrade to OpenWeather One Call API 3.0**:
               - Paid subscription required
               - Visit: https://openweathermap.org/api/one-call-3
            """)

    # Check for parameter compatibility with temporal resolution
    if source_key == "nasa_power" and temporal_resolution == "Hourly":
        non_hourly_params = ["T2M_MAX", "T2M_MIN"]
        incompatible = [p for p in selected_params if p in non_hourly_params]

        if incompatible:
            st.error(f"""
            ❌ **Incompatible Parameters for Hourly Data**

            The following parameters are NOT available for hourly resolution:
            - {', '.join(incompatible)}

            **These parameters are only available for Daily resolution.**

            **Options:**
            1. Change resolution to **Daily**
            2. Deselect these parameters and use hourly-compatible ones like:
               - T2M (Temperature)
               - T2MDEW (Dew Point)
               - RH2M (Humidity)
               - WS2M (Wind Speed)
               - PRECTOTCORR (Precipitation)
            """)

    # Warn about large requests
    if source_key == "nasa_power":
        if temporal_resolution == "Hourly" and date_range_days > 90:
            st.warning(f"""
            ⚠️ **Large Data Request Warning**

            You're requesting hourly data for {date_range_days} days ({date_range_days * 24:,} hours).

            **Recommendations:**
            - For long periods (>3 months), use **Daily** or **Monthly** resolution
            - Hourly data works best for periods up to 30-90 days
            - Large requests may timeout or take several minutes

            **Alternative:** Try Daily resolution which will be much faster!
            """)
        elif temporal_resolution == "Daily" and date_range_days > 365:
            st.info(f"""
            ℹ️ Requesting daily data for {date_range_days} days (~{date_range_days/365:.1f} years).
            This may take 1-2 minutes to fetch.
            """)

    st.info(f"""
    **Ready to fetch:**
    - 📊 Data Source: {selected_source}
    - 📋 Parameters: {len(selected_params)} selected
    - 📍 Locations: {len(locations_list)} selected
    - ⏰ Resolution: {temporal_resolution}
    - 📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({date_range_days} days)
    """)

# Weather Fetch button (only renders for non-LULC sources)
if source_key != "lulc" and st.button("Fetch Weather Data", type="primary", disabled=not (selected_params and locations_list)):
    if not selected_params:
        st.error("❌ Please select at least one parameter")
    elif not locations_list:
        st.error("❌ Please select at least one location")
    else:
        # Prepare location tuples (lat, lon)
        # locations_list format: [(lat, lon, name), ...]
        location_coords = [(loc[0], loc[1]) for loc in locations_list]
        
        # Show progress
        with st.spinner(f"Fetching data from {selected_source}..."):
            try:
                # Debug information
                st.info(f"""
                **Fetching:**
                - {len(selected_params)} parameter(s): {', '.join(selected_params[:3])}{'...' if len(selected_params) > 3 else ''}
                - {len(location_coords)} location(s)
                - From {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
                """)
                
                # Fetch data based on source
                df = None
                if source_key == "nasa_power":
                    df = nasa_power.fetch_nasa_power_data(
                        locations=location_coords,
                        parameters=selected_params,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        temporal_resolution=temporal_resolution,
                    )
                
                elif source_key == "openweather":
                    if not api_key:
                        st.error("❌ OpenWeather API key is required")
                    else:
                        df = openweather.fetch_openweather_data(
                            locations=location_coords,
                            parameters=selected_params,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            temporal_resolution=temporal_resolution,
                            api_key=api_key,
                        )
                
                elif source_key == "era5":
                    if not ee_credentials:
                        st.error("❌ Earth Engine credentials not found. Please add ee_credentials.json file.")
                        df = pd.DataFrame()
                    else:
                        df = era5.fetch_era5_data(
                            locations=location_coords,
                            parameters=selected_params,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            temporal_resolution=temporal_resolution,
                            credentials_dict=ee_credentials,
                        )
                
                elif source_key == "modis":
                    if not ee_credentials:
                        st.error("❌ Earth Engine credentials not found. Please add ee_credentials.json file.")
                        df = pd.DataFrame()
                    else:
                        df = modis.fetch_modis_data(
                            locations=location_coords,
                            parameters=selected_params,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            temporal_resolution=temporal_resolution,
                            credentials_dict=ee_credentials,
                        )
                
                elif source_key == "chirps":
                    if not ee_credentials:
                        st.error("❌ Earth Engine credentials not found. Please add ee_credentials.json file.")
                        df = pd.DataFrame()
                    else:
                        df = chirps.fetch_chirps_data(
                            locations=location_coords,
                            parameters=selected_params,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            temporal_resolution=temporal_resolution,
                            credentials_dict=ee_credentials,
                        )

                elif source_key == "drought_indices":
                    if not ee_credentials:
                        st.error("❌ Earth Engine credentials not found. Please add ee_credentials.json file.")
                        df = pd.DataFrame()
                    else:
                        df = drought_indices.fetch_drought_data(
                            locations=location_coords,
                            parameters=selected_params,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            temporal_resolution=temporal_resolution,
                            credentials_dict=ee_credentials,
                        )

                elif source_key == "phenology":
                    if not ee_credentials:
                        st.error("❌ Earth Engine credentials not found. Please add ee_credentials.json file.")
                        df = pd.DataFrame()
                    else:
                        df = phenology.fetch_phenology_data(
                            locations=location_coords,
                            parameters=selected_params,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            temporal_resolution=temporal_resolution,
                            credentials_dict=ee_credentials,
                        )

                elif source_key == "soil_moisture":
                    if not ee_credentials:
                        st.error("❌ Earth Engine credentials not found. Please add ee_credentials.json file.")
                        df = pd.DataFrame()
                    else:
                        df = soil_moisture.fetch_smap_data(
                            locations=location_coords,
                            parameters=selected_params,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            temporal_resolution=temporal_resolution,
                            credentials_dict=ee_credentials,
                        )

                elif source_key == "productivity":
                    if not ee_credentials:
                        st.error("❌ Earth Engine credentials not found.")
                        df = pd.DataFrame()
                    else:
                        df = productivity.fetch_productivity_data(
                            locations=location_coords,
                            parameters=selected_params,
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            temporal_resolution=temporal_resolution,
                            credentials_dict=ee_credentials,
                        )

                else:  # land_degradation (burned area) — polygon input required
                    if not ee_credentials:
                        st.error("❌ Earth Engine credentials not found.")
                        df = pd.DataFrame()
                    else:
                        have_uploaded_gdf_ld = (
                            st.session_state.uploaded_geodataframe is not None
                        )
                        have_admin_ld = (
                            location_method == "African Countries/Divisions"
                            and bool(locations_list)
                        )
                        if not (have_uploaded_gdf_ld or have_admin_ld):
                            st.error(
                                "❌ Burned Area needs polygon input. "
                                "Upload a shapefile / KML, or pick an African "
                                "country / division."
                            )
                            df = pd.DataFrame()
                        else:
                            if have_uploaded_gdf_ld:
                                aoi_gdf_ld = st.session_state.uploaded_geodataframe.copy()
                            else:
                                admin_countries_ld = (
                                    list(selected_countries)
                                    if 'selected_countries' in dir() else []
                                )
                                admin_divisions_ld = (
                                    dict(selected_divisions)
                                    if 'selected_divisions' in dir() and selected_divisions
                                    else None
                                )
                                st.info("Resolving admin polygons via FAO GAUL 2015...")
                                aoi_gdf_ld = lulc.gdf_from_admin_selection(
                                    countries=admin_countries_ld,
                                    divisions=admin_divisions_ld,
                                    credentials_dict=ee_credentials,
                                )
                            df = land_degradation.fetch_burned_area_from_gdf(
                                aoi_gdf=aoi_gdf_ld,
                                parameters=selected_params,
                                start_date=start_date.strftime("%Y-%m-%d"),
                                end_date=end_date.strftime("%Y-%m-%d"),
                                credentials_dict=ee_credentials,
                            )
                
                if df is not None and not df.empty:
                    # Add location names to the dataframe
                    # locations_list format: [(lat, lon, name), ...]
                    location_map = {i: loc[2] for i, loc in enumerate(locations_list)}
                    if "location_id" in df.columns:
                        df["location_name"] = df["location_id"].map(location_map)
                    
                    st.session_state.fetched_data = df
                    st.session_state.current_data_source = selected_source
                    
                    # Track data source usage
                    date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                    analytics.track_data_source_usage(
                        data_source=selected_source,
                        parameters=selected_params,
                        locations_count=len(locations_list),
                        date_range=date_range
                    )
                    
                    st.success(f"✅ Data fetched successfully! {len(df)} records retrieved.")
                    st.balloons()
                else:
                    st.warning("⚠️ No data retrieved. Please check your parameters and try again.")
                    
                    # Source-specific guidance
                    if source_key == "nasa_power":
                        latest_available = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                        st.info(f"""
                        **NASA POWER Data Availability:**
                        - ⏱️ Data has ~7 day latency
                        - 📅 Latest available data: {latest_available}
                        - 🔄 Try selecting dates at least 7 days in the past
                        - ✅ Recommended: Use dates from last month or earlier
                        
                        **Example:** Select dates from 2024-09-01 to 2024-09-30
                        """)
                    elif source_key == "openweather":
                        st.error("""
                        **OpenWeather Free Tier Limitation:**
                        - ❌ Historical data NOT available on free tier
                        - ✅ Only current weather + 7-day forecast available
                        
                        **Solution:**
                        Switch to **NASA POWER** for free historical weather data!
                        
                        **Steps:**
                        1. In the sidebar, change "Data Source" to **NASA POWER**
                        2. Select your dates (at least 7 days in the past)
                        3. No API key needed!
                        4. Click "Fetch Weather Data"
                        """)
                    elif source_key == "era5":
                        st.info("""
                        **ERA5 Data Availability:**
                        - Data has ~5 day latency
                        - Requests can take 5-30 minutes to process
                        - Try dates at least 5 days in the past
                        """)
                    else:
                        st.info("""
                        **Possible reasons:**
                        - Selected parameters may not be available for the chosen date range
                        - Data source might be temporarily unavailable
                        - Try selecting different parameters or a different date range
                        """)
            
            except Exception as e:
                st.error(f"❌ Error fetching data: {str(e)}")
                if st.checkbox("🔍 View Error Details", key="error_details"):
                    st.code(str(e))

# --- Cached export builders ---------------------------------------------------
# Streamlit reruns the script on every interaction. Without caching, the
# shapefile / Excel / GeoJSON byte payloads (and a fresh temp directory for the
# shapefile) would be rebuilt on every checkbox toggle. We key the cache on a
# hash of the dataframe so it invalidates whenever new data is fetched.

def _df_fingerprint(df: pd.DataFrame) -> str:
    """Stable, cheap-ish fingerprint of a DataFrame for cache keying."""
    return f"{df.shape}-{int(pd.util.hash_pandas_object(df, index=True).sum())}"


@st.cache_data(show_spinner=False)
def _build_csv(_df, _fp):
    return export_to_csv(_df)


@st.cache_data(show_spinner=False)
def _build_json(_df, _fp):
    return export_to_json(_df)


@st.cache_data(show_spinner=False)
def _build_geojson(_df, _fp):
    return export_to_geojson(_df)


@st.cache_data(show_spinner=False)
def _build_excel(_df, _fp):
    return export_to_excel(_df)


@st.cache_data(show_spinner=False)
def _build_shapefile_bytes(_df, _fp):
    """Build shapefile ZIP and return bytes (so the temp dir can be cleaned up)."""
    zip_path = export_to_shapefile(_df)
    try:
        with open(zip_path, "rb") as f:
            return f.read()
    finally:
        # Best-effort cleanup of the temp ZIP and its parent dir.
        try:
            parent = os.path.dirname(zip_path)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if parent and os.path.isdir(parent):
                # Remove parent only if empty after ZIP removal.
                try:
                    os.rmdir(parent)
                except OSError:
                    pass
        except Exception:
            pass


# --- LULC spatial export builders (polygon-attributed) -------------------
# These take a long-form composition or change DataFrame plus the AOI gdf
# from session state and emit a real polygon GeoDataFrame, which is then
# written out to Shapefile/GeoJSON. The output preserves the input
# polygon geometry and decorates each feature with the LULC attributes.

def _lulc_gdf_fingerprint(long_df, aoi_gdf):
    """Fingerprint covers both the LULC values and the AOI geometry so the
    cache invalidates if either the AOI or the data changes."""
    a = _df_fingerprint(long_df) if long_df is not None else "none"
    b = (
        int(pd.util.hash_pandas_object(aoi_gdf.drop(columns="geometry"), index=True).sum())
        if aoi_gdf is not None and not aoi_gdf.empty else 0
    )
    c = len(aoi_gdf) if aoi_gdf is not None else 0
    return f"{a}-{b}-{c}"


@st.cache_data(show_spinner=False)
def _build_lulc_polygon_gdf(_long_df, _aoi_gdf, _is_change, _fp):
    """Polygon summary GDF: ONE feature per input AOI with attributes
    describing dominant class / change statistics. Used in change mode."""
    if _is_change:
        return lulc.build_change_geodataframe(_long_df, _aoi_gdf)
    return lulc.build_polygon_geodataframe(_long_df, _aoi_gdf)


# Cache the vectorized land-cover GDF separately — different inputs and a
# different runtime cost. Keyed on (aoi fingerprint, dataset, year).

def _lulc_vector_fingerprint(aoi_gdf, dataset, year):
    a = (
        int(pd.util.hash_pandas_object(aoi_gdf.drop(columns="geometry"), index=True).sum())
        if aoi_gdf is not None and not aoi_gdf.empty else 0
    )
    return f"{a}-{len(aoi_gdf) if aoi_gdf is not None else 0}-{dataset}-{year}"


@st.cache_data(show_spinner=False)
def _build_lulc_vector_gdf(_aoi_gdf, _dataset, _year, _scale, _creds_token, _fp):
    """Vectorize the LULC raster inside each AOI into many class polygons.
    `_creds_token` is included so the cache invalidates if credentials change.
    `_scale` is an explicit override (None = use dataset's native scale)."""
    gdf, meta = lulc.build_lulc_vector_polygons_gdf(
        aoi_gdf=_aoi_gdf,
        dataset_name=_dataset,
        year=int(_year),
        credentials_dict=ee_credentials,
        scale_override=_scale,
    )
    return gdf, meta


@st.cache_data(show_spinner=False)
def _build_lulc_geojson_bytes(_long_df, _aoi_gdf, _is_change, _fp):
    gdf = _build_lulc_polygon_gdf(_long_df, _aoi_gdf, _is_change, _fp)
    return gdf.to_json().encode("utf-8")


@st.cache_data(show_spinner=False)
def _build_lulc_vector_geojson_bytes(_aoi_gdf, _dataset, _year, _scale, _creds_token, _fp):
    gdf, meta = _build_lulc_vector_gdf(_aoi_gdf, _dataset, _year, _scale, _creds_token, _fp)
    return gdf.to_json().encode("utf-8"), meta


@st.cache_data(show_spinner=False)
def _build_lulc_shapefile_bytes(_long_df, _aoi_gdf, _is_change, _fp):
    """Write the polygon-summary GDF to a zipped shapefile (change mode)."""
    from utils.shapefile_handler import create_shapefile_zip
    gdf = _build_lulc_polygon_gdf(_long_df, _aoi_gdf, _is_change, _fp)
    # Truncate + dedupe columns to obey the .dbf 10-char limit (same
    # algorithm as the weather Shapefile export in utils/export_handler.py).
    new_cols = []
    seen = {}
    for col in gdf.columns:
        if col == "geometry":
            new_cols.append(col)
            continue
        base = col[:10]
        if base not in seen:
            seen[base] = 0
            new_cols.append(base)
        else:
            seen[base] += 1
            suffix = f"_{seen[base]}"
            trimmed = base[: 10 - len(suffix)] + suffix
            while trimmed in new_cols:
                seen[base] += 1
                suffix = f"_{seen[base]}"
                trimmed = base[: 10 - len(suffix)] + suffix
            new_cols.append(trimmed)
    gdf.columns = new_cols
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "lulc_export")
    gdf.to_file(f"{output_path}.shp")
    zip_path = create_shapefile_zip(output_path)
    try:
        with open(zip_path, "rb") as f:
            return f.read()
    finally:
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg", ".zip"):
            try:
                p = f"{output_path}{ext}"
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass


@st.cache_data(show_spinner=False)
def _build_lulc_vector_shapefile_bytes(_aoi_gdf, _dataset, _year, _scale, _creds_token, _fp):
    """Write the *vectorized* land-cover GDF (many class polygons per AOI)
    to a zipped shapefile suitable for QGIS/ArcGIS styling."""
    from utils.shapefile_handler import create_shapefile_zip
    gdf, meta = _build_lulc_vector_gdf(_aoi_gdf, _dataset, _year, _scale, _creds_token, _fp)
    if gdf.empty:
        raise RuntimeError("Vectorize returned no polygons — AOI may not intersect dataset coverage.")
    # 10-char column-dedup, same algorithm used in utils/export_handler.py
    new_cols = []
    seen = {}
    for col in gdf.columns:
        if col == "geometry":
            new_cols.append(col)
            continue
        base = col[:10]
        if base not in seen:
            seen[base] = 0
            new_cols.append(base)
        else:
            seen[base] += 1
            suffix = f"_{seen[base]}"
            trimmed = base[: 10 - len(suffix)] + suffix
            while trimmed in new_cols:
                seen[base] += 1
                suffix = f"_{seen[base]}"
                trimmed = base[: 10 - len(suffix)] + suffix
            new_cols.append(trimmed)
    gdf = gdf.copy()
    gdf.columns = new_cols
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "lulc_vector")
    gdf.to_file(f"{output_path}.shp")
    zip_path = create_shapefile_zip(output_path)
    try:
        with open(zip_path, "rb") as f:
            return f.read(), meta
    finally:
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg", ".zip"):
            try:
                p = f"{output_path}{ext}"
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass


def _track_download_cb(fmt: str, rows: int, locs: int):
    """on_click callback for download buttons — only fires on actual click."""
    analytics.track_download(
        data_source=st.session_state.get("current_data_source", "Unknown"),
        export_format=fmt,
        rows_count=rows,
        locations_count=locs,
    )


# Display fetched data
if st.session_state.fetched_data is not None:
    st.header("📊 Retrieved Data")

    df = st.session_state.fetched_data.copy()
    
    # Fix datetime columns for Streamlit display (PyArrow compatibility)
    for col in df.columns:
        if col in ['date', 'datetime'] or 'date' in col.lower():
            if df[col].dtype == 'object':
                try:
                    # Convert to consistent datetime format
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    # Convert to string for display to avoid PyArrow issues
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    df[col] = df[col].str.replace(' 00:00:00', '')  # Remove time if midnight
                except:
                    # If conversion fails, convert to string
                    df[col] = df[col].astype(str)
    
    # Data preview
    st.subheader("Data Preview")
    st.dataframe(df.head(20))
    
    # Data summary (use original data for accurate metrics). Branch on schema:
    # weather tables have location_id + date/datetime columns; LULC tables
    # have polygon_id + class_name/class_code; hydrology tables have
    # polygon_id + water_ever_km2 (no class column).
    original_df = st.session_state.fetched_data
    is_hydrology_result = "water_ever_km2" in original_df.columns
    is_forest_result = any(
        c in original_df.columns
        for c in ("AGB_MEAN_T_HA", "CANOPY_MEAN_M", "MANGROVE_KM2")
    )
    is_lulc_result = (
        not is_hydrology_result and not is_forest_result
    ) and (
        "polygon_id" in original_df.columns
        or "class_name" in original_df.columns
        or any(c in original_df.columns for c in ("class_code", "polygon_name"))
    )
    col1, col2, col3, col4 = st.columns(4)
    if is_hydrology_result:
        with col1:
            st.metric("Polygons", int(original_df["polygon_id"].nunique()))
        with col2:
            st.metric(
                "Total water (km²)",
                f"{float(original_df['water_ever_km2'].sum()):,.1f}",
            )
        with col3:
            st.metric(
                "Permanent (km²)",
                f"{float(original_df['permanent_water_km2'].sum()):,.1f}",
            )
        with col4:
            periods = original_df["period"].dropna().unique() if "period" in original_df.columns else []
            st.metric("Period", periods[0] if len(periods) else "—")
    elif is_lulc_result:
        with col1:
            st.metric("Total Rows", len(original_df))
        with col2:
            n_polys = (
                original_df["polygon_id"].nunique()
                if "polygon_id" in original_df.columns
                else (original_df["polygon_name"].nunique()
                      if "polygon_name" in original_df.columns else 0)
            )
            st.metric("Polygons", n_polys)
        with col3:
            n_classes = (
                original_df["class_name"].nunique()
                if "class_name" in original_df.columns
                else max(0, len([c for c in original_df.columns
                                 if c not in ("polygon_id", "polygon_name", "dataset", "year")]))
            )
            st.metric("Classes", n_classes)
        with col4:
            if "year" in original_df.columns:
                yrs = sorted(set(original_df["year"].dropna().unique()))
                st.metric("Year", str(yrs[0]) if len(yrs) == 1 else f"{yrs[0]}–{yrs[-1]}")
            else:
                st.metric("Year", "—")
    else:
        with col1:
            st.metric("Total Records", len(original_df))
        with col2:
            st.metric("Locations", original_df["location_id"].nunique() if "location_id" in original_df.columns else 0)
        with col3:
            st.metric("Parameters", len([col for col in original_df.columns if col not in ["date", "datetime", "latitude", "longitude", "location_id", "location_name"]]))
        with col4:
            # Display actual date range from data
            date_col = "datetime" if "datetime" in original_df.columns else "date"
            if date_col in original_df.columns:
                min_date = pd.to_datetime(original_df[date_col]).min()
                max_date = pd.to_datetime(original_df[date_col]).max()
                date_span = (max_date - min_date).days + 1
                st.metric("Date Span", f"{date_span} days")
    
    # Data statistics (use original data)
    if st.checkbox("📈 View Data Statistics", key="view_stats"):
        st.dataframe(original_df.describe())
    
    # Export section
    st.header("💾 Export Data")
    
    st.markdown("**Choose your preferred format to download:**")
    
    # Generate base filename. Weather uses the requested date range;
    # LULC uses dataset+year (no date range applies).
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if is_hydrology_result:
        ds_tag = (hydro_dataset or "gsw").replace(" ", "_").replace("/", "_")
        base_filename = f"gsw_stats_{ds_tag}_{timestamp}"
    elif is_lulc_result:
        ds_tag = (lulc_dataset or "lulc").replace(" ", "_").replace("/", "_")
        yr_tag = str(lulc_year or "year")
        base_filename = f"landcover_{ds_tag}_{yr_tag}_{timestamp}"
    else:
        date_range_str = (
            f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
            if start_date and end_date else timestamp
        )
        base_filename = f"weather_data_{selected_source.replace(' ', '_')}_{date_range_str}"

    # Use original (unformatted) data for all exports; compute counts once.
    original_df = st.session_state.fetched_data
    _fp = _df_fingerprint(original_df)
    _rows = len(original_df)
    if is_lulc_result:
        _locs = (
            original_df["polygon_id"].nunique()
            if "polygon_id" in original_df.columns
            else (original_df["polygon_name"].nunique()
                  if "polygon_name" in original_df.columns else 0)
        )
    else:
        _locs = (
            original_df["location_id"].nunique()
            if "location_id" in original_df.columns else 0
        )

    # Create three columns for the main export formats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📊 CSV")
        st.caption("Tabular format for Excel/Python/R")
        try:
            csv_data = _build_csv(original_df, _fp)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{base_filename}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_csv",
                on_click=_track_download_cb,
                kwargs={"fmt": "CSV", "rows": _rows, "locs": _locs},
            )
        except Exception as e:
            st.error(f"Error: {str(e)}")

    with col2:
        st.subheader("🗺️ Shapefile")
        st.caption("For GIS applications (QGIS/ArcGIS)")
        if is_hydrology_result:
            st.info(
                "ℹ️ Hydrology results are per-polygon numeric summaries with no "
                "geometry attached. Use CSV / JSON / Excel for the values, or "
                "join them back to your original AOI shapefile on `polygon_id` "
                "in QGIS."
            )
        elif is_lulc_result:
            lulc_aoi = st.session_state.get("lulc_aoi_gdf")
            is_change_res = st.session_state.get("lulc_change_long") is not None
            long_df = (
                st.session_state.lulc_change_long
                if is_change_res
                else st.session_state.lulc_composition_long
            )
            if lulc_aoi is None or long_df is None or long_df.empty:
                st.info("ℹ️ Spatial export requires a successful LULC fetch first.")
            elif is_change_res:
                # Change mode: polygon-attributed summary (one feature per AOI).
                st.caption(
                    "One feature per AOI with `percent_changed`, top loss / top gain attributes."
                )
                try:
                    fp_lulc = _lulc_gdf_fingerprint(long_df, lulc_aoi)
                    shapefile_data = _build_lulc_shapefile_bytes(
                        long_df, lulc_aoi, True, fp_lulc
                    )
                    st.download_button(
                        label="📥 Download Shapefile",
                        data=shapefile_data,
                        file_name=f"{base_filename}_change_summary.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="download_lulc_shapefile_change",
                        on_click=_track_download_cb,
                        kwargs={"fmt": "Shapefile (LULC change summary)", "rows": _rows, "locs": _locs},
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                # Composition mode: VECTORIZED land cover — many polygons,
                # one per class patch. Loads into QGIS as a real LULC map.
                st.caption(
                    "Vectorized land cover — many polygons, one per class patch. "
                    "Style by `class_name` or `color` in QGIS/ArcGIS. "
                    "**CSV/JSON composition is computed over the entire AOI** — only "
                    "this vectorized export is subject to a per-AOI polygon cap."
                )
                ds_native = lulc.get_dataset_info(
                    st.session_state.lulc_last_dataset
                )["scale"]
                scale_choices = [ds_native, 30, 100, 250]
                scale_choices = sorted({s for s in scale_choices if s >= ds_native})
                vec_scale = st.selectbox(
                    "Vectorize scale (m/pixel)",
                    options=scale_choices,
                    index=0,
                    key="lulc_vec_shp_scale",
                    help=(
                        f"Native is {ds_native} m. Coarser scales (30 / 100 / 250 m) "
                        "produce far fewer polygons — use them for large AOIs so "
                        "the output fits in the 50,000-polygons-per-AOI cap."
                    ),
                )
                if st.button(
                    "🧩 Build & download vectorized Shapefile",
                    key="lulc_build_vector_shp",
                    use_container_width=True,
                    help="Calls Earth Engine to vectorize the LULC raster inside your AOI(s). Can take 10–60 s.",
                ):
                    try:
                        with st.spinner(f"Vectorizing land cover at {vec_scale} m via Earth Engine…"):
                            fp_v = _lulc_vector_fingerprint(
                                lulc_aoi,
                                st.session_state.lulc_last_dataset,
                                st.session_state.lulc_last_year,
                            ) + f"-s{vec_scale}"
                            shp_bytes, shp_meta = _build_lulc_vector_shapefile_bytes(
                                lulc_aoi,
                                st.session_state.lulc_last_dataset,
                                int(st.session_state.lulc_last_year),
                                int(vec_scale),
                                "v1",  # creds token
                                fp_v,
                            )
                        st.session_state["_lulc_vec_shp_bytes"] = shp_bytes
                        st.session_state["_lulc_vec_shp_meta"] = shp_meta
                    except Exception as e:
                        st.error(f"Vectorize failed: {e}")
                if st.session_state.get("_lulc_vec_shp_meta"):
                    m = st.session_state["_lulc_vec_shp_meta"]
                    st.caption(
                        f"📊 {m['total_polygons']:,} polygons at {m['scale_m']} m"
                    )
                    if m["truncated"]:
                        st.warning(
                            f"⚠️ {m['truncated_count']} AOI(s) hit the "
                            f"{m['max_polygons_per_aoi']:,}-polygon cap — visible "
                            "coverage in QGIS is partial. **The CSV composition is "
                            "still correct over the entire AOI.** To export a "
                            "complete vectorized map, rebuild at a coarser scale "
                            "(30, 100, or 250 m) — accuracy of class assignment "
                            "is preserved; only the polygon count drops."
                        )
                if st.session_state.get("_lulc_vec_shp_bytes"):
                    st.download_button(
                        label="📥 Download Shapefile (ready)",
                        data=st.session_state["_lulc_vec_shp_bytes"],
                        file_name=f"{base_filename}_vector_{vec_scale}m.zip",
                        mime="application/zip",
                        use_container_width=True,
                        key="download_lulc_vector_shp",
                        on_click=_track_download_cb,
                        kwargs={"fmt": f"Shapefile (vectorized LULC {vec_scale}m)", "rows": _rows, "locs": _locs},
                    )
        else:
            try:
                shapefile_data = _build_shapefile_bytes(original_df, _fp)
                st.download_button(
                    label="📥 Download Shapefile",
                    data=shapefile_data,
                    file_name=f"{base_filename}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="download_shapefile",
                    on_click=_track_download_cb,
                    kwargs={"fmt": "Shapefile", "rows": _rows, "locs": _locs},
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col3:
        st.subheader("📝 JSON")
        st.caption("For web apps and APIs")
        try:
            json_data = _build_json(original_df, _fp)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"{base_filename}.json",
                mime="application/json",
                use_container_width=True,
                key="download_json",
                on_click=_track_download_cb,
                kwargs={"fmt": "JSON", "rows": _rows, "locs": _locs},
            )
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Additional formats
    if st.checkbox("📦 More Export Formats", key="more_formats"):
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**GeoJSON** (Geographic JSON)")
            if is_hydrology_result:
                st.info(
                    "ℹ️ Hydrology results are per-polygon numeric summaries. "
                    "Use CSV / JSON / Excel."
                )
            elif is_lulc_result:
                lulc_aoi = st.session_state.get("lulc_aoi_gdf")
                is_change_res = st.session_state.get("lulc_change_long") is not None
                long_df = (
                    st.session_state.lulc_change_long
                    if is_change_res
                    else st.session_state.lulc_composition_long
                )
                if lulc_aoi is None or long_df is None or long_df.empty:
                    st.info("ℹ️ Spatial export requires a successful LULC fetch first.")
                elif is_change_res:
                    st.caption("One feature per AOI with change-summary attributes.")
                    try:
                        fp_lulc = _lulc_gdf_fingerprint(long_df, lulc_aoi)
                        geojson_data = _build_lulc_geojson_bytes(
                            long_df, lulc_aoi, True, fp_lulc
                        )
                        st.download_button(
                            label="📥 Download GeoJSON",
                            data=geojson_data,
                            file_name=f"{base_filename}_change_summary.geojson",
                            mime="application/geo+json",
                            use_container_width=True,
                            key="download_lulc_geojson_change",
                            on_click=_track_download_cb,
                            kwargs={"fmt": "GeoJSON (LULC change summary)", "rows": _rows, "locs": _locs},
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.caption(
                        "Vectorized land cover — many polygons per AOI, one per class patch. "
                        "**CSV/JSON composition is over the entire AOI**; only this "
                        "export is subject to the per-AOI polygon cap."
                    )
                    ds_native_gj = lulc.get_dataset_info(
                        st.session_state.lulc_last_dataset
                    )["scale"]
                    scale_choices_gj = sorted({ds_native_gj, 30, 100, 250})
                    scale_choices_gj = [s for s in scale_choices_gj if s >= ds_native_gj]
                    vec_scale_gj = st.selectbox(
                        "Vectorize scale (m/pixel)",
                        options=scale_choices_gj,
                        index=0,
                        key="lulc_vec_gj_scale",
                        help=(
                            f"Native is {ds_native_gj} m. Use 30/100/250 m for large "
                            "AOIs that exceed the 50,000-polygon cap."
                        ),
                    )
                    if st.button(
                        "🧩 Build & download vectorized GeoJSON",
                        key="lulc_build_vector_gj",
                        use_container_width=True,
                        help="Calls Earth Engine to vectorize the LULC raster inside your AOI(s). Can take 10–60 s.",
                    ):
                        try:
                            with st.spinner(f"Vectorizing land cover at {vec_scale_gj} m via Earth Engine…"):
                                fp_v = _lulc_vector_fingerprint(
                                    lulc_aoi,
                                    st.session_state.lulc_last_dataset,
                                    st.session_state.lulc_last_year,
                                ) + f"-s{vec_scale_gj}"
                                gj_bytes, gj_meta = _build_lulc_vector_geojson_bytes(
                                    lulc_aoi,
                                    st.session_state.lulc_last_dataset,
                                    int(st.session_state.lulc_last_year),
                                    int(vec_scale_gj),
                                    "v1",
                                    fp_v,
                                )
                            st.session_state["_lulc_vec_gj_bytes"] = gj_bytes
                            st.session_state["_lulc_vec_gj_meta"] = gj_meta
                        except Exception as e:
                            st.error(f"Vectorize failed: {e}")
                    if st.session_state.get("_lulc_vec_gj_meta"):
                        m = st.session_state["_lulc_vec_gj_meta"]
                        st.caption(f"📊 {m['total_polygons']:,} polygons at {m['scale_m']} m")
                        if m["truncated"]:
                            st.warning(
                                f"⚠️ {m['truncated_count']} AOI(s) hit the "
                                f"{m['max_polygons_per_aoi']:,}-polygon cap. "
                                "**CSV composition is unaffected.** Rebuild at a "
                                "coarser scale (30/100/250 m) for full coverage."
                            )
                    if st.session_state.get("_lulc_vec_gj_bytes"):
                        st.download_button(
                            label="📥 Download GeoJSON (ready)",
                            data=st.session_state["_lulc_vec_gj_bytes"],
                            file_name=f"{base_filename}_vector_{vec_scale_gj}m.geojson",
                            mime="application/geo+json",
                            use_container_width=True,
                            key="download_lulc_vector_gj",
                            on_click=_track_download_cb,
                            kwargs={"fmt": f"GeoJSON (vectorized LULC {vec_scale_gj}m)", "rows": _rows, "locs": _locs},
                        )
            else:
                try:
                    geojson_data = _build_geojson(original_df, _fp)
                    st.download_button(
                        label="📥 Download GeoJSON",
                        data=geojson_data,
                        file_name=f"{base_filename}.geojson",
                        mime="application/geo+json",
                        use_container_width=True,
                        key="download_geojson",
                        on_click=_track_download_cb,
                        kwargs={"fmt": "GeoJSON", "rows": _rows, "locs": _locs},
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        with col_b:
            st.markdown("**Excel** (XLSX)")
            try:
                excel_data = _build_excel(original_df, _fp)
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"{base_filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_excel",
                    on_click=_track_download_cb,
                    kwargs={"fmt": "Excel", "rows": _rows, "locs": _locs},
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # -------- LULC: raster clip (per-polygon GeoTIFF) ----------------------
    # Only renders for LULC results. Streams the clip from Earth Engine via
    # a signed download URL — synchronous, capped at ~33 MP. For very large
    # AOIs we surface a warning and recommend the async export (Phase 12).
    if (
        is_lulc_result
        and st.session_state.get("lulc_aoi_gdf") is not None
        and st.session_state.get("lulc_last_dataset")
    ):
        st.subheader("🛰️ Raster clip (GeoTIFF)")
        st.caption(
            "Download the underlying classified raster clipped to a polygon. "
            "Earth Engine returns a single-band GeoTIFF with the class code "
            "at each pixel; use the dataset's class palette to symbolize."
        )
        aoi_gdf_state = st.session_state.lulc_aoi_gdf
        n = len(aoi_gdf_state)
        # Case-insensitive name lookup (KML's "Name", Shapefile "NAME", etc.)
        polygon_labels = [
            lulc.best_polygon_name(row, i)
            for i, row in aoi_gdf_state.iterrows()
        ]
        def _fmt_polygon(i):
            name = polygon_labels[i]
            # Replace auto-generated placeholders with friendlier indexing.
            if name.startswith("polygon_"):
                return f"Polygon {i + 1}"
            return name if n == 1 else f"{i + 1}. {name}"
        sel_idx = st.selectbox(
            "Polygon to clip",
            options=list(range(n)),
            format_func=_fmt_polygon,
            key="lulc_clip_polygon_idx",
        )
        clip_year_options = [st.session_state.lulc_last_year]
        if st.session_state.lulc_last_year_to:
            clip_year_options.append(st.session_state.lulc_last_year_to)
        clip_year = st.selectbox(
            "Year",
            options=clip_year_options,
            key="lulc_clip_year",
        )
        if st.button("Generate Raster Clip URL", key="lulc_gen_clip_url"):
            if not ee_credentials:
                st.error("❌ Earth Engine credentials not found.")
            else:
                try:
                    with st.spinner("Requesting clipped raster from Earth Engine..."):
                        info = lulc.get_raster_clip_url(
                            aoi_gdf=aoi_gdf_state,
                            dataset_name=st.session_state.lulc_last_dataset,
                            year=int(clip_year),
                            credentials_dict=ee_credentials,
                            polygon_index=int(sel_idx),
                        )
                    st.success(
                        f"✅ Clip ready for **{info['polygon_name']}** "
                        f"({info['dataset']} {info['year']}, {info['scale_m']} m)."
                    )
                    if info.get("note"):
                        st.warning(info["note"])
                    st.markdown(
                        f"[⬇️ Download GeoTIFF clip]({info['url']})  •  "
                        f"Estimated ~{info['estimated_pixels']:,} pixels"
                    )
                    st.caption(f"📜 Attribution: {info['attribution']}")
                except Exception as e:
                    st.error(f"Raster clip failed: {e}")
                    if st.checkbox("🔍 Show error", key="lulc_clip_err"):
                        st.code(str(e))

# Footer
st.markdown("---")
st.markdown("""
### 📖 Data Source Information

- **NASA POWER**: Provides global meteorological and solar energy data
- **OpenWeather API**: Real-time and historical weather data (requires API key)
- **ERA5**: ECMWF Reanalysis v5 - comprehensive climate reanalysis (requires CDS API key)
- **MODIS**: Satellite-based land surface and vegetation data
- **CHIRPS**: Climate Hazards Group InfraRed Precipitation with Station data

### ℹ️ Notes

- Some data sources require API keys or authentication
- Large date ranges may take longer to process
- MODIS and CHIRPS implementations are simplified and may require full setup for production use
- Data availability varies by source and temporal resolution

### 🔗 Useful Links

- [NASA POWER Documentation](https://power.larc.nasa.gov/docs/)
- [OpenWeather API](https://openweathermap.org/api)
- [Copernicus CDS](https://cds.climate.copernicus.eu/)
- [MODIS Data](https://modis.gsfc.nasa.gov/)
- [CHIRPS Data](https://www.chc.ucsb.edu/data/chirps)
""")

# Footer with creator information
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin-top: 30px;'>
    <h4 style='color: #000000 !important; margin: 0 0 10px 0; font-weight: 600;'>👨‍💻 Created by</h4>
    <h3 style='color: #000000 !important; margin: 5px 0; font-weight: 700;'>Victor Iko-ojo Idakwo</h3>
    <p style='color: #000000 !important; margin: 5px 0;'><strong style='color: #000000 !important;'>RTP, MNITP, MGEOSON</strong></p>
    <p style='margin: 15px 0;'>
        <a href="https://www.linkedin.com/in/victor-idakwo-8a838a12a/" target="_blank" 
           style="margin: 0 10px; text-decoration: none; color: #3b82f6 !important; font-weight: 500;">
            🔗 LinkedIn
        </a>
        <span style='color: #000000 !important;'>|</span>
        <a href="https://github.com/VictorIdakwo" target="_blank" 
           style="margin: 0 10px; text-decoration: none; color: #3b82f6 !important; font-weight: 500;">
            💻 GitHub
        </a>
    </p>
    <p style="font-size: 0.9em; color: #000000 !important; margin-top: 10px;">
        Weather Data Portal • Powered by Google Earth Engine
    </p>
</div>
""", unsafe_allow_html=True)
