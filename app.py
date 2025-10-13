import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import tempfile
import json

# Import data source modules
from data_sources import nasa_power, openweather, era5, modis, chirps

# Import utilities
from utils.africa_locations import (
    get_countries, 
    get_admin_division_type,
    get_divisions_for_country,
    get_sub_divisions,
    get_selected_locations as get_africa_locations
)
from utils.shapefile_handler import (
    extract_shapefile_from_zip,
    read_shapefile,
    extract_locations_from_shapefile,
    validate_shapefile_locations,
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
    initial_sidebar_state="expanded",
)

# Title and description
st.markdown("<h1 style='text-align: center;'>🌍 Weather Data Portal for Africa</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center;'>
<p>Download weather and climate data from multiple sources including NASA POWER, OpenWeather API, 
ERA5-Land, MODIS, and CHIRPS for locations across Africa.</p>

<p><strong>Coverage:</strong> All 54 African countries with their administrative divisions (States, Regions, Provinces, Counties, etc.)</p>

<p><em>Created by <strong>Victor Iko-ojo Idakwo</strong> (RTP, MNITP, MGEOSON)</em></p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "fetched_data" not in st.session_state:
    st.session_state.fetched_data = None
if "selected_locations" not in st.session_state:
    st.session_state.selected_locations = None
if "current_data_source" not in st.session_state:
    st.session_state.current_data_source = None

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

# Get available parameters for selected source
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
else:  # chirps
    available_params = chirps.get_available_parameters()
    temporal_options = chirps.get_temporal_resolutions()

# Display available parameters by category
st.sidebar.subheader("📋 Available Parameters")
selected_params = []

for category, params in available_params.items():
    with st.sidebar.expander(f"📁 {category}"):
        for param_code, param_desc in params.items():
            # Create unique key by combining source, category, and param_code
            unique_key = f"param_{source_key}_{category.replace(' ', '_').replace('/', '_')}_{param_code}"
            if st.checkbox(param_desc, key=unique_key):
                selected_params.append(param_code)

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
        min_value=datetime(2000, 1, 1),
        max_value=max_date,
        help="Select the start date for data retrieval"
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=default_end,
        min_value=datetime(2000, 1, 1),
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

# Main content area
st.markdown("<h2 style='text-align: center;'>📍 Location Selection</h2>", unsafe_allow_html=True)

# Location selection method
location_method = st.radio(
    "Choose location selection method:",
    options=["African Countries/Divisions", "Upload Shapefile"],
    horizontal=True,
)

locations_list = []

if location_method == "African Countries/Divisions":
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
        
        # Create columns for better layout
        cols = st.columns(2)
        
        for idx, country in enumerate(selected_countries):
            col = cols[idx % 2]
            
            with col:
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

else:  # Upload Shapefile
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
            
            # Display shapefile info
            st.success(f"✅ Shapefile loaded successfully! Found {len(gdf)} features.")
            
            # Show preview
            with st.expander("Preview Shapefile Data"):
                st.dataframe(gdf.head(10))
            
            # Extract locations
            locations_list = extract_locations_from_shapefile(gdf)
            
            # Validate locations
            is_valid, error_msg = validate_shapefile_locations(locations_list)
            if not is_valid:
                st.warning(f"⚠️ Warning: {error_msg}")
            
        except Exception as e:
            st.error(f"❌ Error processing shapefile: {str(e)}")

# Display selected locations
if locations_list:
    st.success(f"✅ {len(locations_list)} location(s) selected")
    
    with st.expander("View Selected Locations"):
        # locations_list format: [(lat, lon, name), ...]
        df_locations = pd.DataFrame(locations_list, columns=["Latitude", "Longitude", "Location Name"])
        st.dataframe(df_locations)
    
    st.session_state.selected_locations = locations_list

# Fetch Data button
st.header("🚀 Fetch Data")

# Display fetch summary
if selected_params and locations_list and start_date <= end_date:
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

if st.button("Fetch Weather Data", type="primary", disabled=not (selected_params and locations_list)):
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
                
                else:  # chirps
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
                with st.expander("View Error Details"):
                    st.code(str(e))

# Display fetched data
if st.session_state.fetched_data is not None:
    st.header("📊 Retrieved Data")
    
    df = st.session_state.fetched_data
    
    # Data preview
    st.subheader("Data Preview")
    st.dataframe(df.head(20))
    
    # Data summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        st.metric("Locations", df["location_id"].nunique())
    with col3:
        st.metric("Parameters", len([col for col in df.columns if col not in ["date", "datetime", "latitude", "longitude", "location_id", "location_name"]]))
    with col4:
        # Display actual date range from data
        date_col = "datetime" if "datetime" in df.columns else "date"
        if date_col in df.columns:
            min_date = pd.to_datetime(df[date_col]).min()
            max_date = pd.to_datetime(df[date_col]).max()
            date_span = (max_date - min_date).days + 1
            st.metric("Date Span", f"{date_span} days")
    
    # Data statistics
    with st.expander("View Data Statistics"):
        st.dataframe(df.describe())
    
    # Export section
    st.header("💾 Export Data")
    
    st.markdown("**Choose your preferred format to download:**")
    
    # Generate base filename with date range
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_range_str = f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
    base_filename = f"weather_data_{selected_source.replace(' ', '_')}_{date_range_str}"
    
    # Create three columns for the main export formats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 CSV")
        st.caption("Tabular format for Excel/Python/R")
        try:
            csv_data = export_to_csv(df)
            if st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{base_filename}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_csv",
            ):
                # Track download
                analytics.track_download(
                    data_source=st.session_state.get('current_data_source', 'Unknown'),
                    export_format='CSV',
                    rows_count=len(df),
                    locations_count=df['location_id'].nunique() if 'location_id' in df.columns else 0
                )
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("🗺️ Shapefile")
        st.caption("For GIS applications (QGIS/ArcGIS)")
        try:
            zip_path = export_to_shapefile(df)
            with open(zip_path, "rb") as f:
                shapefile_data = f.read()
            if st.download_button(
                label="📥 Download Shapefile",
                data=shapefile_data,
                file_name=f"{base_filename}.zip",
                mime="application/zip",
                use_container_width=True,
                key="download_shapefile",
            ):
                analytics.track_download(
                    data_source=st.session_state.get('current_data_source', 'Unknown'),
                    export_format='Shapefile',
                    rows_count=len(df),
                    locations_count=df['location_id'].nunique() if 'location_id' in df.columns else 0
                )
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with col3:
        st.subheader("📝 JSON")
        st.caption("For web apps and APIs")
        try:
            json_data = export_to_json(df)
            if st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"{base_filename}.json",
                mime="application/json",
                use_container_width=True,
                key="download_json",
            ):
                analytics.track_download(
                    data_source=st.session_state.get('current_data_source', 'Unknown'),
                    export_format='JSON',
                    rows_count=len(df),
                    locations_count=df['location_id'].nunique() if 'location_id' in df.columns else 0
                )
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Additional formats in expander
    with st.expander("📦 More Export Formats"):
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("**GeoJSON** (Geographic JSON)")
            try:
                geojson_data = export_to_geojson(df)
                if st.download_button(
                    label="📥 Download GeoJSON",
                    data=geojson_data,
                    file_name=f"{base_filename}.geojson",
                    mime="application/geo+json",
                    use_container_width=True,
                    key="download_geojson",
                ):
                    analytics.track_download(
                        data_source=st.session_state.get('current_data_source', 'Unknown'),
                        export_format='GeoJSON',
                        rows_count=len(df),
                        locations_count=df['location_id'].nunique() if 'location_id' in df.columns else 0
                    )
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with col_b:
            st.markdown("**Excel** (XLSX)")
            try:
                excel_data = export_to_excel(df)
                if st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"{base_filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_excel",
                ):
                    analytics.track_download(
                        data_source=st.session_state.get('current_data_source', 'Unknown'),
                        export_format='Excel',
                        rows_count=len(df),
                        locations_count=df['location_id'].nunique() if 'location_id' in df.columns else 0
                    )
            except Exception as e:
                st.error(f"Error: {str(e)}")

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
    <h4>👨‍💻 Created by</h4>
    <h3>Victor Iko-ojo Idakwo</h3>
    <p><strong>RTP, MNITP, MGEOSON</strong></p>
    <p>
        <a href="https://www.linkedin.com/in/victor-idakwo-8a838a12a/" target="_blank" style="margin: 0 10px; text-decoration: none;">
            🔗 LinkedIn
        </a>
        |
        <a href="https://github.com/VictorIdakwo" target="_blank" style="margin: 0 10px; text-decoration: none;">
            💻 GitHub
        </a>
    </p>
    <p style="font-size: 0.9em; color: #666; margin-top: 10px;">
        Weather Data Portal • Powered by Google Earth Engine
    </p>
</div>
""", unsafe_allow_html=True)
