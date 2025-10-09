import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import tempfile
import os

# Available CHIRPS parameters
CHIRPS_PARAMETERS = {
    "Precipitation": {
        "precipitation": "Precipitation (mm)",
    },
}

TEMPORAL_RESOLUTIONS = ["Daily", "Pentadal", "Dekadal", "Monthly"]


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    """Return available CHIRPS parameters grouped by category."""
    return CHIRPS_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    """Return available temporal resolutions for CHIRPS."""
    return TEMPORAL_RESOLUTIONS


def fetch_chirps_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    credentials_dict: Dict = None,
) -> pd.DataFrame:
    """
    Fetch CHIRPS precipitation data via Google Earth Engine.
    
    Args:
        locations: List of (latitude, longitude) tuples
        parameters: List of parameter codes to fetch (only 'precipitation' available)
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        temporal_resolution: 'Daily', 'Pentadal', 'Dekadal', or 'Monthly'
        credentials_dict: Earth Engine service account credentials
    
    Returns:
        DataFrame with fetched data
    """
    
    from .earth_engine_utils import fetch_chirps_precipitation
    
    print("=" * 70)
    print("CHIRPS via Google Earth Engine")
    print("=" * 70)
    
    if not credentials_dict:
        raise ValueError("Earth Engine credentials required. Please provide service account credentials.")
    
    try:
        # Fetch CHIRPS precipitation
        df = fetch_chirps_precipitation(
            locations=locations,
            start_date=start_date,
            end_date=end_date,
            credentials_dict=credentials_dict
        )
        
        if not df.empty:
            print(f"\n[SUCCESS] CHIRPS fetch complete: {len(df)} records")
            return df
        else:
            print("\n[WARNING] No data retrieved")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"\n[ERROR] Error fetching CHIRPS data: {str(e)}")
        raise


def download_chirps_geotiff(year: int, month: int, day: int = None, temporal_resolution: str = "Daily") -> str:
    """
    Download a CHIRPS GeoTIFF file.
    
    Args:
        year: Year
        month: Month
        day: Day (only for daily data)
        temporal_resolution: 'Daily' or 'Monthly'
    
    Returns:
        Path to downloaded file
    """
    base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0"
    
    if temporal_resolution == "Daily":
        temporal_path = "global_daily/tifs/p05"
        filename = f"chirps-v2.0.{year}.{month:02d}.{day:02d}.tif.gz"
    else:  # Monthly
        temporal_path = "global_monthly/tifs"
        filename = f"chirps-v2.0.{year}.{month:02d}.tif.gz"
    
    url = f"{base_url}/{temporal_path}/{year}/{filename}"
    
    # Download file
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tif.gz") as tmp_file:
        tmp_file.write(response.content)
        return tmp_file.name


def extract_chirps_values(geotiff_path: str, locations: List[Tuple[float, float]]) -> List[float]:
    """
    Extract CHIRPS values at specific locations from a GeoTIFF file.
    
    Args:
        geotiff_path: Path to GeoTIFF file
        locations: List of (latitude, longitude) tuples
    
    Returns:
        List of precipitation values
    """
    try:
        import rasterio
        from rasterio.transform import rowcol
        
        values = []
        
        with rasterio.open(geotiff_path) as src:
            for lat, lon in locations:
                # Get row, col for the coordinate
                row, col = rowcol(src.transform, lon, lat)
                
                # Read value at that location
                if 0 <= row < src.height and 0 <= col < src.width:
                    value = src.read(1)[row, col]
                    
                    # Handle no-data values
                    if value == src.nodata or value < -9000:
                        value = None
                    
                    values.append(value)
                else:
                    values.append(None)
        
        return values
    
    except Exception as e:
        print(f"Error extracting CHIRPS values: {str(e)}")
        return [None] * len(locations)
