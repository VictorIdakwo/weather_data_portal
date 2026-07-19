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
    credentials_dict: Dict = None,
    chunk_days: int = 30,
    use_daily_aggregate: bool = False,
) -> pd.DataFrame:
    """
    Fetch ERA5-Land hourly data via Google Earth Engine.

    Key correctness properties:
      * Date range is chunked (default 30 days = ~720 hourly images) so we
        never silently truncate at GEE's element-list limits.
      * All requested bands are sampled in a single reduceRegion call per
        image, yielding one *wide* row per (timestamp, location_id) with one
        column per user-facing parameter — not one row per (timestamp, param).

    Args:
        locations: list of (lat, lon) tuples
        parameters: user-facing ERA5 parameter codes
        start_date / end_date: 'YYYY-MM-DD'
        credentials_dict: EE service account credentials
        chunk_days: window size in days per GEE request
    """

    # Initialize Earth Engine
    client = EarthEngineClient(credentials_dict=credentials_dict)
    if not client.initialized:
        raise Exception("Earth Engine initialization failed")

    # Two backing assets: HOURLY for hourly requests, DAILY_AGGR for daily.
    # DAILY_AGGR gives ~24x smaller payload than sampling HOURLY and
    # aggregating client-side. Precipitation band is named differently on
    # each collection so the mapping needs a branch.
    if use_daily_aggregate:
        asset_id = 'ECMWF/ERA5_LAND/DAILY_AGGR'
        param_map = {
            '2m_temperature': 'temperature_2m',
            'temperature_2m': 'temperature_2m',
            '2m_dewpoint_temperature': 'dewpoint_temperature_2m',
            'dewpoint_temperature_2m': 'dewpoint_temperature_2m',
            'total_precipitation': 'total_precipitation_sum',
            'surface_pressure': 'surface_pressure',
            '10m_u_component_of_wind': 'u_component_of_wind_10m',
            '10m_v_component_of_wind': 'v_component_of_wind_10m',
            'u_component_of_wind_10m': 'u_component_of_wind_10m',
            'v_component_of_wind_10m': 'v_component_of_wind_10m',
        }
        ts_fmt = 'YYYY-MM-dd'
    else:
        asset_id = 'ECMWF/ERA5_LAND/HOURLY'
        param_map = {
            '2m_temperature': 'temperature_2m',
            'temperature_2m': 'temperature_2m',
            '2m_dewpoint_temperature': 'dewpoint_temperature_2m',
            'dewpoint_temperature_2m': 'dewpoint_temperature_2m',
            'total_precipitation': 'total_precipitation',
            'surface_pressure': 'surface_pressure',
            '10m_u_component_of_wind': 'u_component_of_wind_10m',
            '10m_v_component_of_wind': 'v_component_of_wind_10m',
            'u_component_of_wind_10m': 'u_component_of_wind_10m',
            'v_component_of_wind_10m': 'v_component_of_wind_10m',
        }
        ts_fmt = 'YYYY-MM-dd HH:mm'

    print(f"Fetching ERA5-Land from {asset_id}  {start_date}..{end_date}  ({len(locations)} pts)")

    # 2m relative humidity is not an ERA5-Land band but can be derived from
    # temperature and dewpoint via the Magnus formula. Silently upgrade the
    # fetch list so the raw T + Td come back too, then compute RH after
    # the download.
    need_rh = '2m_relative_humidity' in parameters
    fetch_params = list(parameters)
    if need_rh:
        for req in ('2m_temperature', '2m_dewpoint_temperature'):
            if req not in fetch_params:
                fetch_params.append(req)
        fetch_params = [p for p in fetch_params if p != '2m_relative_humidity']

    # Resolve bands (one entry per unique EE band).
    band_names = []
    band_to_user_param = {}
    skipped = []
    for p in fetch_params:
        b = param_map.get(p)
        if b is None:
            skipped.append(p)
            continue
        if b not in band_to_user_param:
            band_names.append(b)
            band_to_user_param[b] = p
    if skipped:
        print(f"  [WARN] ERA5 params not available on this EE asset and skipped: {', '.join(skipped)}")
    if not band_names:
        print("[WARNING] No supported ERA5 bands selected; nothing to fetch.")
        return pd.DataFrame()

    collection = ee.ImageCollection(asset_id).select(band_names)

    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    if end_dt <= start_dt:
        return pd.DataFrame()

    # Batch points to stay under Earth Engine's 5,000-elements-per-getInfo
    # limit. Every reduceRegions call now samples ALL points in a batch
    # in one round-trip. If a chunk's expected feature count (batch_size
    # * images_per_chunk) would exceed the limit we shrink batch_size
    # accordingly. Effective throughput: one HTTP round-trip per
    # (batch, chunk) pair.
    EE_GETINFO_MAX = 5000
    # For DAILY_AGGR: images per chunk == chunk_days.
    # For HOURLY: images per chunk == chunk_days * 24.
    images_per_chunk = chunk_days * (1 if use_daily_aggregate else 24)
    # Leave a small headroom so borderline cases don't hit the wall.
    max_batch_size = max(1, (EE_GETINFO_MAX - 200) // max(images_per_chunk, 1))
    batch_size = min(len(locations), max_batch_size)
    if batch_size < len(locations):
        print(
            f"  [BATCHING] {len(locations)} points split into batches of "
            f"{batch_size} (images/chunk={images_per_chunk}, "
            f"batch*images={batch_size * images_per_chunk} < {EE_GETINFO_MAX})"
        )

    def _batch_fc(offset, batch_locs):
        feats = []
        for j, (lat, lon) in enumerate(batch_locs):
            pt = ee.Geometry.Point([lon, lat])
            feats.append(ee.Feature(pt, {
                'location_id': int(offset + j),
                'lat': float(lat),
                'lon': float(lon),
            }))
        return ee.FeatureCollection(feats)

    def _sample_image_factory(fc):
        def _sample_image(image):
            sampled = image.reduceRegions(
                collection=fc,
                reducer=ee.Reducer.first(),
                scale=11132,
                tileScale=4,
            )
            ts = ee.Date(image.get('system:time_start')).format(ts_fmt)
            return sampled.map(lambda f: f.set('datetime', ts))
        return _sample_image

    all_records = []
    n_batches = (len(locations) + batch_size - 1) // batch_size
    for batch_idx in range(n_batches):
        offset = batch_idx * batch_size
        batch = locations[offset:offset + batch_size]
        fc = _batch_fc(offset, batch)
        sample_fn = _sample_image_factory(fc)

        if n_batches > 1:
            print(f"  batch {batch_idx + 1}/{n_batches}  points {offset}..{offset + len(batch) - 1}")

        cur = start_dt
        while cur < end_dt:
            chunk_end = min(cur + timedelta(days=chunk_days), end_dt)
            cs, ce = cur.strftime('%Y-%m-%d'), chunk_end.strftime('%Y-%m-%d')

            try:
                filtered = collection.filterDate(cs, ce)
                all_samples = filtered.map(sample_fn).flatten()
                server_features = all_samples.getInfo().get('features', [])
                print(f"    chunk {cs}..{ce}: {len(server_features):,} records")
            except Exception as e:
                print(f"    [ERROR] chunk {cs}..{ce}: {e}")
                cur = chunk_end
                continue

            for feat in server_features:
                props = feat.get('properties') or {}
                if not props:
                    continue
                record = {
                    'datetime': props.get('datetime'),
                    'latitude': props.get('lat'),
                    'longitude': props.get('lon'),
                    'location_id': int(props.get('location_id', -1)),
                }
                has_data = False
                for band in band_names:
                    v = props.get(band)
                    out_col = band_to_user_param[band]
                    if v is None:
                        record[out_col] = None
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        record[out_col] = None
                        continue
                    # Unit conversions
                    if 'temperature' in band:
                        v = v - 273.15
                    elif 'precipitation' in band:
                        v = v * 1000
                    elif 'pressure' in band:
                        v = v / 100
                    record[out_col] = round(v, 3)
                    has_data = True
                if has_data:
                    all_records.append(record)

            cur = chunk_end

    if not all_records:
        print("[WARNING] No ERA5 data retrieved")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Derived: 2m relative humidity from Magnus-formula (Buck 1981), given
    # T and Td already in degC after unit conversion above.
    if need_rh and ('2m_temperature' in df.columns) and ('2m_dewpoint_temperature' in df.columns):
        t_c = df['2m_temperature'].astype(float)
        td_c = df['2m_dewpoint_temperature'].astype(float)
        import numpy as np
        e_s = 6.112 * np.exp((17.67 * t_c) / (t_c + 243.5))
        e_a = 6.112 * np.exp((17.67 * td_c) / (td_c + 243.5))
        rh = (100.0 * e_a / e_s).clip(0, 100)
        df['2m_relative_humidity'] = rh.round(1)

    df = df.sort_values(['location_id', 'datetime']).reset_index(drop=True)
    print(f"[SUCCESS] ERA5: {len(df):,} rows across {len(locations)} location(s)")
    return df
