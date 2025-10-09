import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import json

# Available MODIS parameters via AppEEARS API
MODIS_PARAMETERS = {
    "Land Surface Temperature": {
        "MOD11A1.061_LST_Day_1km": "MODIS Terra LST Day (Kelvin)",
        "MOD11A1.061_LST_Night_1km": "MODIS Terra LST Night (Kelvin)",
        "MYD11A1.061_LST_Day_1km": "MODIS Aqua LST Day (Kelvin)",
        "MYD11A1.061_LST_Night_1km": "MODIS Aqua LST Night (Kelvin)",
    },
    "Vegetation Indices": {
        "MOD13Q1.061_250m_16_days_NDVI": "MODIS Terra NDVI 16-day",
        "MOD13Q1.061_250m_16_days_EVI": "MODIS Terra EVI 16-day",
        "MYD13Q1.061_250m_16_days_NDVI": "MODIS Aqua NDVI 16-day",
        "MYD13Q1.061_250m_16_days_EVI": "MODIS Aqua EVI 16-day",
    },
    "Evapotranspiration": {
        "MOD16A2.061_ET_500m": "MODIS Terra ET 8-day (kg/m²/8day)",
        "MOD16A2.061_PET_500m": "MODIS Terra Potential ET 8-day (kg/m²/8day)",
    },
    "Gross Primary Productivity": {
        "MOD17A2H.061_Gpp_500m": "MODIS Terra GPP 8-day (kg C/m²/8day)",
    },
    "Snow Cover": {
        "MOD10A1.061_NDSI_Snow_Cover": "MODIS Terra Snow Cover Daily",
    },
}

TEMPORAL_RESOLUTIONS = ["Daily", "8-day", "16-day"]


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    """Return available MODIS parameters grouped by category."""
    return MODIS_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    """Return available temporal resolutions for MODIS."""
    return TEMPORAL_RESOLUTIONS


def fetch_modis_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    credentials_dict: Dict = None,
) -> pd.DataFrame:
    """
    Fetch MODIS data via Google Earth Engine.
    
    Args:
        locations: List of (latitude, longitude) tuples
        parameters: List of parameter codes to fetch
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        temporal_resolution: 'Daily', '8-day', or '16-day'
        credentials_dict: Earth Engine service account credentials
    
    Returns:
        DataFrame with fetched data
    """
    
    from .earth_engine_utils import fetch_modis_lst, fetch_modis_ndvi
    
    print("=" * 70)
    print("MODIS via Google Earth Engine")
    print("=" * 70)
    
    if not credentials_dict:
        raise ValueError("Earth Engine credentials required. Please provide service account credentials.")
    
    all_dfs = []
    
    try:
        # Process each parameter
        for param in parameters:
            print(f"\nFetching {param}...")
            
            if "LST_Day" in param:
                # Land Surface Temperature - Day
                df = fetch_modis_lst(
                    locations=locations,
                    start_date=start_date,
                    end_date=end_date,
                    product="day",
                    credentials_dict=credentials_dict
                )
                if not df.empty:
                    all_dfs.append(df)
            
            elif "LST_Night" in param:
                # Land Surface Temperature - Night
                df = fetch_modis_lst(
                    locations=locations,
                    start_date=start_date,
                    end_date=end_date,
                    product="night",
                    credentials_dict=credentials_dict
                )
                if not df.empty:
                    all_dfs.append(df)
            
            elif "NDVI" in param or "EVI" in param:
                # Vegetation indices
                df = fetch_modis_ndvi(
                    locations=locations,
                    start_date=start_date,
                    end_date=end_date,
                    credentials_dict=credentials_dict
                )
                if not df.empty:
                    all_dfs.append(df)
            
            else:
                print(f"  [WARNING] Parameter {param} not yet implemented")
                continue
        
        # Merge all dataframes
        if all_dfs:
            # Merge on common columns
            final_df = all_dfs[0]
            for df in all_dfs[1:]:
                final_df = final_df.merge(
                    df,
                    on=['datetime', 'latitude', 'longitude', 'location_id'],
                    how='outer'
                )
            
            print("\n" + "=" * 70)
            print(f"[SUCCESS] MODIS fetch complete: {len(final_df)} total records")
            print("=" * 70)
            return final_df
        else:
            print("\n[WARNING] No data retrieved")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"\n[ERROR] Error fetching MODIS data: {str(e)}")
        raise


def submit_appeears_task(
    task_name: str,
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    username: str,
    password: str,
) -> str:
    """
    Submit a task to NASA AppEEARS API.
    
    Returns:
        Task ID if successful
    """
    # Authentication endpoint
    auth_url = "https://appeears.earthdatacloud.nasa.gov/api/login"
    
    # Authenticate
    response = requests.post(
        auth_url,
        auth=(username, password),
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"Authentication failed: {response.text}")
    
    token = response.json()["token"]
    
    # Prepare task submission
    task_url = "https://appeears.earthdatacloud.nasa.gov/api/task"
    
    # Format coordinates for task
    coordinates = []
    for idx, (lat, lon) in enumerate(locations):
        coordinates.append({
            "id": str(idx),
            "latitude": lat,
            "longitude": lon,
            "category": f"location_{idx}"
        })
    
    # Prepare task parameters
    task = {
        "task_type": "point",
        "task_name": task_name,
        "params": {
            "dates": [
                {
                    "startDate": start_date,
                    "endDate": end_date
                }
            ],
            "layers": [{"product": param.split("_")[0], "layer": param} for param in parameters],
            "coordinates": coordinates,
        }
    }
    
    # Submit task
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(task_url, json=task, headers=headers, timeout=30)
    
    if response.status_code != 202:
        raise Exception(f"Task submission failed: {response.text}")
    
    task_id = response.json()["task_id"]
    return task_id
