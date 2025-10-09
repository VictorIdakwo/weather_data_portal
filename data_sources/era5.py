import pandas as pd
from datetime import datetime
from typing import List, Tuple, Dict

# Available ERA5 parameters
ERA5_PARAMETERS = {
    "Temperature": {
        "2m_temperature": "2m Temperature (K)",
        "2m_dewpoint_temperature": "2m Dewpoint Temperature (K)",
        "skin_temperature": "Skin Temperature (K)",
    },
    "Precipitation": {
        "total_precipitation": "Total Precipitation (m)",
        "convective_precipitation": "Convective Precipitation (m)",
    },
    "Pressure": {
        "surface_pressure": "Surface Pressure (Pa)",
        "mean_sea_level_pressure": "Mean Sea Level Pressure (Pa)",
    },
    "Wind": {
        "10m_u_component_of_wind": "10m U Wind Component (m/s)",
        "10m_v_component_of_wind": "10m V Wind Component (m/s)",
    },
    "Humidity": {
        "2m_relative_humidity": "2m Relative Humidity (%)",
    },
    "Solar Radiation": {
        "surface_solar_radiation_downwards": "Surface Solar Radiation Downwards (J/m²)",
        "surface_thermal_radiation_downwards": "Surface Thermal Radiation Downwards (J/m²)",
    },
    "Cloud": {
        "total_cloud_cover": "Total Cloud Cover (0-1)",
        "low_cloud_cover": "Low Cloud Cover (0-1)",
        "medium_cloud_cover": "Medium Cloud Cover (0-1)",
        "high_cloud_cover": "High Cloud Cover (0-1)",
    },
    "Evaporation": {
        "evaporation": "Evaporation (m of water)",
        "potential_evaporation": "Potential Evaporation (m)",
    },
}

TEMPORAL_RESOLUTIONS = ["Hourly", "Daily", "Monthly"]


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    """Return available ERA5 parameters grouped by category."""
    return ERA5_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    """Return available temporal resolutions for ERA5."""
    return TEMPORAL_RESOLUTIONS


def fetch_era5_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    cds_api_key: str = None,
    credentials_dict: Dict = None,
) -> pd.DataFrame:
    """
    Fetch ERA5-Land data via Google Earth Engine.
    Much simpler and faster than CDS API - no token/account needed!
    
    Args:
        locations: List of (latitude, longitude) tuples
        parameters: List of parameter codes to fetch
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        temporal_resolution: 'Hourly' or 'Daily'
        cds_api_key: Not used (kept for compatibility)
        credentials_dict: Earth Engine service account credentials
    
    Returns:
        DataFrame with ERA5 hourly data
    """
    
    from .earth_engine_utils import fetch_era5_data as fetch_era5_ee
    
    print("=" * 70)
    print("ERA5-Land via Google Earth Engine")
    print("(No CDS API token needed!)")
    print("=" * 70)
    
    if not credentials_dict:
        raise ValueError("Earth Engine credentials required. Please provide service account credentials.")
    
    try:
        df = fetch_era5_ee(
            locations=locations,
            parameters=parameters,
            start_date=start_date,
            end_date=end_date,
            credentials_dict=credentials_dict
        )
        
        # Aggregate to daily if requested
        if temporal_resolution == "Daily" and not df.empty and 'datetime' in df.columns:
            print("Aggregating hourly data to daily...")
            
            df['date'] = df['datetime'].dt.date
            
            # Group by date and location
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            numeric_cols = [col for col in numeric_cols if col not in ['location_id', 'latitude', 'longitude']]
            
            agg_dict = {col: 'mean' for col in numeric_cols}
            agg_dict.update({
                'latitude': 'first',
                'longitude': 'first',
            })
            
            df = df.groupby(['location_id', 'date']).agg(agg_dict).reset_index()
            df = df.rename(columns={'date': 'datetime'})
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        if not df.empty:
            print(f"\n[SUCCESS] ERA5 fetch complete: {len(df)} records")
            return df
        else:
            print("\n[WARNING] No data retrieved")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"\n[ERROR] Error fetching ERA5 data: {str(e)}")
        raise
