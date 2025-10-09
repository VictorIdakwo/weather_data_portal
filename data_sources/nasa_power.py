import requests
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Dict

# Available NASA POWER parameters organized by category
# Note: Not all parameters are available for all temporal resolutions
NASA_POWER_PARAMETERS = {
    "Temperature": {
        "T2M": "Temperature at 2 Meters (°C)",
        "T2M_MAX": "Maximum Temperature at 2 Meters (°C) [Daily only]",
        "T2M_MIN": "Minimum Temperature at 2 Meters (°C) [Daily only]",
        "T2MDEW": "Dew Point Temperature at 2 Meters (°C)",
        "T2MWET": "Wet Bulb Temperature at 2 Meters (°C)",
    },
    "Precipitation": {
        "PRECTOTCORR": "Precipitation Corrected (mm/day) [All]",
    },
    "Humidity": {
        "RH2M": "Relative Humidity at 2 Meters (%)",
        "QV2M": "Specific Humidity at 2 Meters (g/kg)",
    },
    "Wind": {
        "WS2M": "Wind Speed at 2 Meters (m/s)",
        "WS10M": "Wind Speed at 10 Meters (m/s)",
        "WS50M": "Wind Speed at 50 Meters (m/s)",
        "WD2M": "Wind Direction at 2 Meters (Degrees)",
        "WD10M": "Wind Direction at 10 Meters (Degrees)",
    },
    "Solar Radiation": {
        "ALLSKY_SFC_SW_DWN": "All Sky Surface Shortwave Downward Irradiance (kW-hr/m^2/day)",
        "ALLSKY_SFC_LW_DWN": "All Sky Surface Longwave Downward Irradiance (kW-hr/m^2/day)",
        "ALLSKY_SFC_SW_DNI": "All Sky Surface Shortwave Direct Normal Irradiance (kW-hr/m^2/day)",
    },
    "Pressure": {
        "PS": "Surface Pressure (kPa)",
    },
    "Evapotranspiration": {
        "EVPTRNS": "Evapotranspiration Energy Flux (MJ/m^2/day)",
    },
}

TEMPORAL_RESOLUTIONS = ["Hourly", "Daily"]  # Monthly removed - not supported by API


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    """Return available NASA POWER parameters grouped by category."""
    return NASA_POWER_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    """Return available temporal resolutions for NASA POWER."""
    return TEMPORAL_RESOLUTIONS


def fetch_nasa_power_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
) -> pd.DataFrame:
    """
    Fetch data from NASA POWER API for multiple locations.
    
    Args:
        locations: List of (latitude, longitude) tuples
        parameters: List of parameter codes to fetch
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        temporal_resolution: 'Hourly', 'Daily', or 'Monthly'
    
    Returns:
        DataFrame with fetched data
    """
    all_data = []
    
    # Map temporal resolution to API format
    temporal_map = {
        "Hourly": "hourly",
        "Daily": "daily",
    }
    temporal_api = temporal_map.get(temporal_resolution, "daily")
    
    # Parameters that are NOT available for hourly data
    non_hourly_params = ["T2M_MAX", "T2M_MIN"]
    
    # Filter parameters based on temporal resolution
    if temporal_api == "hourly":
        original_params = parameters.copy()
        parameters = [p for p in parameters if p not in non_hourly_params]
        
        removed = set(original_params) - set(parameters)
        if removed:
            print(f"Note: Removed parameters not available for hourly data: {', '.join(removed)}")
            print(f"Using parameters: {', '.join(parameters)}")
        
        if not parameters:
            raise ValueError(f"No valid parameters for hourly data. Parameters like {', '.join(non_hourly_params)} are only available for Daily resolution.")
    
    # Convert date format for API (YYYYMMDD format for both daily and hourly)
    start_date_api = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y%m%d")
    end_date_api = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")
    
    for idx, (lat, lon) in enumerate(locations):
        try:
            # Build API URL
            base_url = "https://power.larc.nasa.gov/api/temporal/"
            params_str = ",".join(parameters)
            
            url = (
                f"{base_url}{temporal_api}/point?"
                f"parameters={params_str}&"
                f"community=AG&"
                f"longitude={lon}&"
                f"latitude={lat}&"
                f"start={start_date_api}&"
                f"end={end_date_api}&"
                f"format=JSON"
            )
            
            print(f"Fetching NASA POWER data for location {idx} ({lat}, {lon})...")
            print(f"URL: {url}")
            
            response = requests.get(url, timeout=120)  # Increased timeout for large requests
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"Error for location {idx}: {error_msg}")
                raise Exception(error_msg)
            
            data = response.json()
            
            # Check for API errors in response
            if "errors" in data:
                error_msg = f"API Error: {data['errors']}"
                print(error_msg)
                raise Exception(error_msg)
            
            if "properties" in data and "parameter" in data["properties"]:
                param_data = data["properties"]["parameter"]
                
                if not param_data:
                    print(f"No parameter data returned for location {idx}")
                    continue
                
                # Convert to DataFrame
                df_list = []
                for param, values in param_data.items():
                    if isinstance(values, dict) and len(values) > 0:
                        param_df = pd.DataFrame(list(values.items()), columns=["date", param])
                        df_list.append(param_df)
                        print(f"Location {idx}: Got {len(values)} records for {param}")
                
                if df_list:
                    # Merge all parameters
                    result_df = df_list[0]
                    for df in df_list[1:]:
                        result_df = result_df.merge(df, on="date", how="outer")
                    
                    # Add location information
                    result_df["latitude"] = lat
                    result_df["longitude"] = lon
                    result_df["location_id"] = idx
                    
                    all_data.append(result_df)
                    print(f"Location {idx}: Successfully processed {len(result_df)} total records")
                else:
                    print(f"Location {idx}: No valid data frames created")
            else:
                print(f"Location {idx}: Unexpected API response structure")
                print(f"Response keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        
        except requests.exceptions.Timeout:
            error_msg = f"Timeout fetching data for location {idx} ({lat}, {lon}). Try a smaller date range or daily/monthly resolution."
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error fetching data for location {idx} ({lat}, {lon}): {str(e)}"
            print(error_msg)
            # Re-raise if it's the first location so user sees the error
            if idx == 0 and len(locations) == 1:
                raise
            continue
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # Convert date column to datetime
        if temporal_api == "hourly":
            final_df["date"] = pd.to_datetime(final_df["date"], format="%Y%m%d%H")
        else:  # daily
            final_df["date"] = pd.to_datetime(final_df["date"], format="%Y%m%d")
        
        # Replace fill values (-999) with NaN
        final_df = final_df.replace(-999, pd.NA)
        
        return final_df
    else:
        return pd.DataFrame()
