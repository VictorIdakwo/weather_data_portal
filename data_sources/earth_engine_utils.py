"""
Google Earth Engine utilities for MODIS and CHIRPS data
"""
import ee
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import json
import os


class EarthEngineClient:
    """Client for Google Earth Engine API"""
    
    def __init__(self, credentials_path: str = None, credentials_dict: Dict = None):
        """
        Initialize Earth Engine client.
        
        Args:
            credentials_path: Path to service account JSON file
            credentials_dict: Service account credentials as dictionary
        """
        self.initialized = False
        
        try:
            if credentials_dict:
                # Use provided credentials dictionary
                credentials = ee.ServiceAccountCredentials(
                    email=credentials_dict['client_email'],
                    key_data=credentials_dict['private_key']
                )
                ee.Initialize(credentials)
            elif credentials_path and os.path.exists(credentials_path):
                # Use credentials file
                credentials = ee.ServiceAccountCredentials(
                    email=None,
                    key_file=credentials_path
                )
                ee.Initialize(credentials)
            else:
                # Try default authentication
                ee.Initialize()
            
            self.initialized = True
            print("[SUCCESS] Earth Engine initialized successfully")
            
        except Exception as e:
            print(f"[ERROR] Earth Engine initialization failed: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test Earth Engine connection"""
        try:
            # Try a simple operation
            image = ee.Image('USGS/SRTMGL1_003')
            info = image.getInfo()
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False


def fetch_modis_lst(
    locations: List[Tuple[float, float]],
    start_date: str,
    end_date: str,
    product: str = "day",
    credentials_dict: Dict = None
) -> pd.DataFrame:
    """
    Fetch MODIS Land Surface Temperature via Earth Engine.
    
    Args:
        locations: List of (latitude, longitude) tuples
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD'
        product: 'day' or 'night'
        credentials_dict: Earth Engine credentials
    
    Returns:
        DataFrame with LST data
    """
    
    # Initialize Earth Engine
    client = EarthEngineClient(credentials_dict=credentials_dict)
    
    if not client.initialized:
        raise Exception("Earth Engine initialization failed")
    
    # Warn about large date ranges
    from datetime import datetime
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end_dt - start_dt).days
    
    if days > 90:
        print(f"[WARNING] Large date range ({days} days) may take several minutes or timeout.")
        print(f"[TIP] For faster results, try <90 days at a time.")
    
    print(f"Fetching MODIS LST ({product}) from {start_date} to {end_date}...")
    
    # Select appropriate band
    band_name = 'LST_Day_1km' if product == "day" else 'LST_Night_1km'
    
    # Get MODIS LST collection (using latest version)
    dataset = ee.ImageCollection('MODIS/061/MOD11A1') \
        .filterDate(start_date, end_date) \
        .select(band_name)
    
    all_data = []
    
    # Extract data for each location
    for idx, (lat, lon) in enumerate(locations):
        print(f"  Processing location {idx + 1}/{len(locations)}: ({lat}, {lon})")
        
        # Create point geometry
        point = ee.Geometry.Point([lon, lat])
        
        # Get time series for this point
        try:
            # Extract values using reduceRegion
            def extract_values(image):
                # Get value at point
                value = image.reduceRegion(
                    reducer=ee.Reducer.first(),
                    geometry=point,
                    scale=1000  # 1km resolution
                ).get(band_name)
                
                # Get date
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                
                return ee.Feature(None, {
                    'date': date,
                    'LST': value,
                    'latitude': lat,
                    'longitude': lon,
                    'location_id': idx
                })
            
            # Map over collection
            features = dataset.map(extract_values)
            
            # Convert to list and get info
            # Limit to reasonable size to avoid timeout
            count = dataset.size().getInfo()
            if count > 1000:
                print(f"  [WARNING] {count} images found. This may take a while...")
            
            feature_list = features.toList(count if count < 5000 else 5000).getInfo()
            
            # Parse features into records
            for feature in feature_list:
                props = feature['properties']
                if props['LST'] is not None:
                    # Convert from Kelvin * 0.02 to Celsius
                    lst_celsius = (props['LST'] * 0.02) - 273.15
                    
                    all_data.append({
                        'datetime': props['date'],
                        'latitude': props['latitude'],
                        'longitude': props['longitude'],
                        'location_id': props['location_id'],
                        f'LST_{product}': round(lst_celsius, 2)
                    })
        
        except Exception as e:
            print(f"  Error processing location {idx}: {str(e)}")
            continue
    
    if all_data:
        df = pd.DataFrame(all_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"[SUCCESS] Retrieved {len(df)} records")
        return df
    else:
        print("[WARNING] No data retrieved")
        return pd.DataFrame()


def fetch_modis_ndvi(
    locations: List[Tuple[float, float]],
    start_date: str,
    end_date: str,
    credentials_dict: Dict = None
) -> pd.DataFrame:
    """
    Fetch MODIS NDVI via Earth Engine.
    
    Args:
        locations: List of (latitude, longitude) tuples
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD'
        credentials_dict: Earth Engine credentials
    
    Returns:
        DataFrame with NDVI data
    """
    
    # Initialize Earth Engine
    client = EarthEngineClient(credentials_dict=credentials_dict)
    
    print(f"Fetching MODIS NDVI from {start_date} to {end_date}...")
    
    # Get MODIS NDVI collection (16-day composite, using latest version)
    dataset = ee.ImageCollection('MODIS/061/MOD13Q1') \
        .filterDate(start_date, end_date) \
        .select('NDVI')
    
    all_data = []
    
    for idx, (lat, lon) in enumerate(locations):
        print(f"  Processing location {idx + 1}/{len(locations)}: ({lat}, {lon})")
        
        point = ee.Geometry.Point([lon, lat])
        
        try:
            def extract_values(image):
                value = image.reduceRegion(
                    reducer=ee.Reducer.first(),
                    geometry=point,
                    scale=250  # 250m resolution
                ).get('NDVI')
                
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                
                return ee.Feature(None, {
                    'date': date,
                    'NDVI': value,
                    'latitude': lat,
                    'longitude': lon,
                    'location_id': idx
                })
            
            features = dataset.map(extract_values)
            feature_list = features.toList(1000).getInfo()
            
            for feature in feature_list:
                props = feature['properties']
                if props['NDVI'] is not None:
                    # Scale NDVI (stored as int * 10000)
                    ndvi = props['NDVI'] / 10000.0
                    
                    all_data.append({
                        'datetime': props['date'],
                        'latitude': props['latitude'],
                        'longitude': props['longitude'],
                        'location_id': props['location_id'],
                        'NDVI': round(ndvi, 4)
                    })
        
        except Exception as e:
            print(f"  Error processing location {idx}: {str(e)}")
            continue
    
    if all_data:
        df = pd.DataFrame(all_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"[SUCCESS] Retrieved {len(df)} records")
        return df
    else:
        return pd.DataFrame()


def fetch_chirps_precipitation(
    locations: List[Tuple[float, float]],
    start_date: str,
    end_date: str,
    credentials_dict: Dict = None
) -> pd.DataFrame:
    """
    Fetch CHIRPS precipitation via Earth Engine.
    
    Args:
        locations: List of (latitude, longitude) tuples
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD'
        credentials_dict: Earth Engine credentials
    
    Returns:
        DataFrame with precipitation data
    """
    
    # Initialize Earth Engine
    client = EarthEngineClient(credentials_dict=credentials_dict)
    
    print(f"Fetching CHIRPS precipitation from {start_date} to {end_date}...")
    
    # Get CHIRPS daily precipitation
    dataset = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
        .filterDate(start_date, end_date) \
        .select('precipitation')
    
    all_data = []
    
    for idx, (lat, lon) in enumerate(locations):
        print(f"  Processing location {idx + 1}/{len(locations)}: ({lat}, {lon})")
        
        point = ee.Geometry.Point([lon, lat])
        
        try:
            def extract_values(image):
                value = image.reduceRegion(
                    reducer=ee.Reducer.first(),
                    geometry=point,
                    scale=5566  # ~5km resolution
                ).get('precipitation')
                
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                
                return ee.Feature(None, {
                    'date': date,
                    'precipitation': value,
                    'latitude': lat,
                    'longitude': lon,
                    'location_id': idx
                })
            
            features = dataset.map(extract_values)
            feature_list = features.toList(10000).getInfo()
            
            for feature in feature_list:
                props = feature['properties']
                if props['precipitation'] is not None:
                    all_data.append({
                        'datetime': props['date'],
                        'latitude': props['latitude'],
                        'longitude': props['longitude'],
                        'location_id': props['location_id'],
                        'precipitation_mm': round(props['precipitation'], 2)
                    })
        
        except Exception as e:
            print(f"  Error processing location {idx}: {str(e)}")
            continue
    
    if all_data:
        df = pd.DataFrame(all_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"[SUCCESS] Retrieved {len(df)} records")
        return df
    else:
        return pd.DataFrame()


def fetch_era5_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    credentials_dict: Dict = None
) -> pd.DataFrame:
    """
    Fetch ERA5-Land data via Google Earth Engine.
    Simpler and faster than CDS API - no token needed!
    
    Args:
        locations: List of (latitude, longitude) tuples
        parameters: List of parameter names
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD'
        credentials_dict: Earth Engine credentials
    
    Returns:
        DataFrame with ERA5 hourly data
    """
    
    # Initialize Earth Engine
    client = EarthEngineClient(credentials_dict=credentials_dict)
    
    print(f"Fetching ERA5-Land data from {start_date} to {end_date}...")
    
    # ERA5-Land parameter mapping to EE band names
    param_map = {
        '2m_temperature': 'temperature_2m',
        'temperature_2m': 'temperature_2m',
        '2m_dewpoint_temperature': 'dewpoint_temperature_2m',
        'dewpoint_temperature_2m': 'dewpoint_temperature_2m',
        'total_precipitation': 'total_precipitation',  # Hourly accumulation
        'surface_pressure': 'surface_pressure',
        '10m_u_component_of_wind': 'u_component_of_wind_10m',
        '10m_v_component_of_wind': 'v_component_of_wind_10m',
        'u_component_of_wind_10m': 'u_component_of_wind_10m',
        'v_component_of_wind_10m': 'v_component_of_wind_10m',
    }
    
    # Get ERA5-Land hourly collection  
    dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
    
    all_data = []
    
    for idx, (lat, lon) in enumerate(locations):
        print(f"  Processing location {idx + 1}/{len(locations)}: ({lat}, {lon})")
        
        point = ee.Geometry.Point([lon, lat])
        
        try:
            # Filter by date
            filtered = dataset.filterDate(start_date, end_date)
            count = filtered.size().getInfo()
            
            print(f"    Found {count} hourly records")
            
            if count == 0:
                continue
            
            # Limit to avoid timeout (1000 records = ~42 days hourly)
            limit = min(count, 1000)
            if count > limit:
                print(f"    [WARNING] Limiting to {limit} of {count} records")
            
            for param in parameters:
                band_name = param_map.get(param, param)
                
                try:
                    def extract_values(image):
                        value = image.select(band_name).reduceRegion(
                            reducer=ee.Reducer.first(),
                            geometry=point,
                            scale=11132  # ~11km
                        ).get(band_name)
                        
                        timestamp = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd HH:mm')
                        
                        return ee.Feature(None, {
                            'datetime': timestamp,
                            'value': value,
                            'latitude': lat,
                            'longitude': lon,
                            'location_id': idx
                        })
                    
                    features = filtered.map(extract_values)
                    feature_list = features.toList(limit).getInfo()
                    
                    for feature in feature_list:
                        props = feature['properties']
                        if props.get('value') is not None:
                            value = props['value']
                            
                            # Unit conversions
                            if 'temperature' in band_name:
                                value = value - 273.15  # K to C
                            elif 'precipitation' in band_name:
                                value = value * 1000  # m to mm
                            elif 'pressure' in band_name:
                                value = value / 100  # Pa to hPa
                            
                            all_data.append({
                                'datetime': props['datetime'],
                                'latitude': props['latitude'],
                                'longitude': props['longitude'],
                                'location_id': props['location_id'],
                                param: round(value, 2)
                            })
                
                except Exception as e:
                    print(f"    [ERROR] {param}: {str(e)}")
        
        except Exception as e:
            print(f"  [ERROR] Location failed: {str(e)}")
    
    if all_data:
        df = pd.DataFrame(all_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"[SUCCESS] Retrieved {len(df)} ERA5 records")
        return df
    else:
        print("[WARNING] No ERA5 data retrieved")
        return pd.DataFrame()
