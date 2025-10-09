# 🛠️ MODIS & CHIRPS Implementation Guide

## Overview

This guide explains how to implement functional MODIS and CHIRPS data sources. Both require significant work beyond the current placeholder implementations.

---

## 🛰️ MODIS Implementation

### What is MODIS?
MODIS (Moderate Resolution Imaging Spectroradiometer) provides satellite data for:
- Land Surface Temperature (LST)
- Vegetation Indices (NDVI, EVI)
- Evapotranspiration (ET)
- Gross Primary Productivity (GPP)
- Snow Cover

### Current Status
- ❌ Placeholder that returns empty data
- ✅ Data structure defined
- ❌ No API integration

---

## 📋 MODIS Implementation Steps

### Option 1: NASA AppEEARS API (Recommended)

**Complexity:** High  
**Time Estimate:** 40-60 hours  
**Maintenance:** Medium

#### Step 1: Get NASA Earthdata Account
1. Visit: https://urs.earthdata.nasa.gov/
2. Create free account
3. Save username and password

#### Step 2: Understand AppEEARS Workflow
AppEEARS is **asynchronous** - not instant like NASA POWER:

```
1. Submit Task → 2. Wait for Processing → 3. Check Status → 4. Download Results
   (instant)        (5-60 minutes)           (polling)        (extract data)
```

#### Step 3: Implement Authentication

```python
# File: data_sources/modis.py

import requests
import time
from typing import Dict, Optional

class AppEEARSClient:
    """Client for NASA AppEEARS API"""
    
    BASE_URL = "https://appeears.earthdatacloud.nasa.gov/api"
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.token = None
    
    def login(self) -> str:
        """Authenticate and get token"""
        url = f"{self.BASE_URL}/login"
        response = requests.post(
            url,
            auth=(self.username, self.password),
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.text}")
        
        self.token = response.json()["token"]
        return self.token
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.token:
            self.login()
        return {"Authorization": f"Bearer {self.token}"}
```

#### Step 4: Implement Task Submission

```python
def submit_task(
    self,
    task_name: str,
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
) -> str:
    """Submit data extraction task"""
    
    # Format coordinates
    coordinates = []
    for idx, (lat, lon) in enumerate(locations):
        coordinates.append({
            "id": str(idx),
            "latitude": lat,
            "longitude": lon,
            "category": f"location_{idx}"
        })
    
    # Format layers (parameters)
    layers = []
    for param in parameters:
        # Parse parameter like "MOD11A1.061_LST_Day_1km"
        parts = param.split(".")
        product = parts[0]  # e.g., "MOD11A1"
        version = parts[1].split("_")[0]  # e.g., "061"
        layer_name = "_".join(parts[1].split("_")[1:])  # e.g., "LST_Day_1km"
        
        layers.append({
            "product": f"{product}.{version}",
            "layer": layer_name
        })
    
    # Create task payload
    task = {
        "task_type": "point",
        "task_name": task_name,
        "params": {
            "dates": [{
                "startDate": start_date,  # Format: MM-DD-YYYY
                "endDate": end_date
            }],
            "layers": layers,
            "coordinates": coordinates,
        }
    }
    
    # Submit task
    url = f"{self.BASE_URL}/task"
    response = requests.post(
        url,
        json=task,
        headers=self.get_headers(),
        timeout=30
    )
    
    if response.status_code != 202:
        raise Exception(f"Task submission failed: {response.text}")
    
    task_id = response.json()["task_id"]
    print(f"Task submitted: {task_id}")
    return task_id
```

#### Step 5: Implement Task Monitoring

```python
def get_task_status(self, task_id: str) -> Dict:
    """Check task status"""
    url = f"{self.BASE_URL}/task/{task_id}"
    response = requests.get(url, headers=self.get_headers(), timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get status: {response.text}")
    
    return response.json()

def wait_for_completion(self, task_id: str, timeout: int = 3600) -> bool:
    """Wait for task to complete (with timeout)"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = self.get_task_status(task_id)
        
        if status["status"] == "done":
            print(f"Task {task_id} completed!")
            return True
        elif status["status"] == "error":
            raise Exception(f"Task failed: {status.get('error', 'Unknown error')}")
        
        print(f"Status: {status['status']} - waiting...")
        time.sleep(30)  # Check every 30 seconds
    
    raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
```

#### Step 6: Implement Data Download

```python
def download_results(self, task_id: str, output_dir: str = ".") -> str:
    """Download task results"""
    import os
    import zipfile
    
    # Get download URL
    url = f"{self.BASE_URL}/bundle/{task_id}"
    response = requests.get(url, headers=self.get_headers(), stream=True)
    
    if response.status_code != 200:
        raise Exception(f"Download failed: {response.text}")
    
    # Save zip file
    zip_path = os.path.join(output_dir, f"{task_id}.zip")
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Extract
    extract_dir = os.path.join(output_dir, task_id)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"Results extracted to: {extract_dir}")
    return extract_dir
```

#### Step 7: Parse Results into DataFrame

```python
def parse_results(self, results_dir: str) -> pd.DataFrame:
    """Parse AppEEARS results CSV into DataFrame"""
    import os
    import glob
    
    # Find CSV file
    csv_files = glob.glob(os.path.join(results_dir, "*.csv"))
    
    if not csv_files:
        raise Exception("No CSV files found in results")
    
    # Read and combine CSVs
    dfs = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Rename columns to match portal format
    rename_map = {
        "Date": "datetime",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Category": "location_id"
    }
    combined_df = combined_df.rename(columns=rename_map)
    
    # Convert date
    combined_df["datetime"] = pd.to_datetime(combined_df["datetime"])
    
    return combined_df
```

#### Step 8: Update fetch_modis_data Function

```python
def fetch_modis_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    username: str,
    password: str,
) -> pd.DataFrame:
    """
    Fetch MODIS data via NASA AppEEARS API.
    
    Note: This is an asynchronous process that may take 5-60 minutes.
    """
    
    # Create client
    client = AppEEARSClient(username, password)
    
    # Login
    print("Authenticating with NASA Earthdata...")
    client.login()
    
    # Submit task
    task_name = f"weather_portal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Submitting task: {task_name}")
    
    # Convert date format from YYYY-MM-DD to MM-DD-YYYY for AppEEARS
    start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m-%d-%Y")
    end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m-%d-%Y")
    
    task_id = client.submit_task(
        task_name=task_name,
        locations=locations,
        parameters=parameters,
        start_date=start_date_formatted,
        end_date=end_date_formatted,
    )
    
    # Wait for completion
    print(f"Waiting for task {task_id} to complete...")
    print("This may take 5-60 minutes. Please be patient.")
    client.wait_for_completion(task_id, timeout=3600)  # 1 hour timeout
    
    # Download results
    print("Downloading results...")
    results_dir = client.download_results(task_id, output_dir="./temp")
    
    # Parse results
    print("Parsing results...")
    df = client.parse_results(results_dir)
    
    # Cleanup temporary files
    import shutil
    shutil.rmtree("./temp", ignore_errors=True)
    
    return df
```

#### Step 9: Update UI to Collect Credentials

In `app.py`, add credential inputs:

```python
if source_key == "modis":
    st.sidebar.subheader("🔑 NASA Earthdata Credentials")
    st.sidebar.info("Required for MODIS data access")
    
    earthdata_username = st.sidebar.text_input(
        "NASA Earthdata Username",
        help="Register at https://urs.earthdata.nasa.gov/"
    )
    earthdata_password = st.sidebar.text_input(
        "NASA Earthdata Password",
        type="password"
    )
    
    st.sidebar.warning("""
    ⏱️ **MODIS requests take 5-60 minutes to process.**
    
    The app will wait for results. Don't close your browser.
    """)
```

#### Step 10: Test Implementation

```python
# Test script
if __name__ == "__main__":
    # Test credentials
    username = "your_earthdata_username"
    password = "your_earthdata_password"
    
    # Test parameters
    locations = [(6.5244, 3.3792)]  # Lagos
    parameters = ["MOD11A1.061_LST_Day_1km"]
    start_date = "2024-01-01"
    end_date = "2024-01-07"
    
    # Fetch data
    df = fetch_modis_data(
        locations=locations,
        parameters=parameters,
        start_date=start_date,
        end_date=end_date,
        temporal_resolution="Daily",
        username=username,
        password=password
    )
    
    print(df.head())
```

---

### Option 2: Google Earth Engine (Alternative)

**Complexity:** Medium  
**Time Estimate:** 20-30 hours  
**Maintenance:** Low

Google Earth Engine has MODIS data and a Python API:

```python
import ee

# Initialize
ee.Initialize()

# Get MODIS LST
dataset = ee.ImageCollection('MODIS/006/MOD11A1') \
    .filterDate('2024-01-01', '2024-01-31') \
    .select('LST_Day_1km')

# Extract for point
point = ee.Geometry.Point([3.3792, 6.5244])
values = dataset.getRegion(point, 1000).getInfo()

# Convert to DataFrame
df = pd.DataFrame(values[1:], columns=values[0])
```

**Pros:**
- Simpler API
- Faster results
- No asynchronous tasks

**Cons:**
- Requires Google Earth Engine account
- Learning curve for Earth Engine
- Rate limits

---

## 🌧️ CHIRPS Implementation

### What is CHIRPS?
Climate Hazards Group InfraRed Precipitation with Station data - focuses on precipitation.

### Current Status
- ❌ Placeholder that returns empty data
- ✅ Data structure defined
- ❌ No API integration

---

## 📋 CHIRPS Implementation Steps

### Option 1: Direct NetCDF Download

**Complexity:** Medium  
**Time Estimate:** 10-20 hours  
**Maintenance:** Low

#### Step 1: Install Required Libraries

```bash
pip install netCDF4 xarray cftime
```

#### Step 2: Implement CHIRPS Fetcher

```python
# File: data_sources/chirps.py

import xarray as xr
import pandas as pd
from datetime import datetime
from typing import List, Tuple
import requests
import os

def fetch_chirps_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
) -> pd.DataFrame:
    """
    Fetch CHIRPS precipitation data.
    
    CHIRPS data is available at:
    https://data.chc.ucsb.edu/products/CHIRPS-2.0/
    """
    
    # Parse dates
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Determine data URL based on resolution
    if temporal_resolution == "Daily":
        # Daily data
        base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/"
    else:
        # Monthly data
        base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/"
    
    all_data = []
    
    # Download and process data for date range
    if temporal_resolution == "Daily":
        # Daily: One file per year
        for year in range(start_dt.year, end_dt.year + 1):
            nc_file = f"chirps-v2.0.{year}.days_p05.nc"
            url = f"{base_url}{nc_file}"
            
            print(f"Downloading {nc_file}...")
            
            # Download file
            response = requests.get(url, timeout=300)
            if response.status_code != 200:
                print(f"Failed to download {nc_file}")
                continue
            
            # Save temporarily
            temp_file = f"./temp_{nc_file}"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # Read NetCDF
            ds = xr.open_dataset(temp_file)
            
            # Extract data for each location
            for idx, (lat, lon) in enumerate(locations):
                # Select nearest point
                point_data = ds.sel(latitude=lat, longitude=lon, method='nearest')
                
                # Filter by date range
                point_data = point_data.sel(
                    time=slice(start_date, end_date)
                )
                
                # Convert to DataFrame
                df = point_data.to_dataframe().reset_index()
                df['location_id'] = idx
                df = df.rename(columns={
                    'time': 'datetime',
                    'precip': 'precipitation'
                })
                
                all_data.append(df[['datetime', 'latitude', 'longitude', 
                                    'location_id', 'precipitation']])
            
            # Cleanup
            ds.close()
            os.remove(temp_file)
    
    else:
        # Monthly: One file per year
        for year in range(start_dt.year, end_dt.year + 1):
            nc_file = f"chirps-v2.0.{year}.days_p05.nc"
            # Similar process as daily
            pass
    
    # Combine all data
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        return final_df
    else:
        return pd.DataFrame()
```

#### Step 3: Handle Large Files

CHIRPS files can be large (>500MB per year). Consider:

1. **Caching downloaded files**
2. **Using dask for lazy loading**
3. **Spatial subsetting before download**

```python
# Use subset API
def get_chirps_subset(bbox, start_date, end_date):
    """Get spatially subsetted CHIRPS data"""
    # CHIRPS subset API (if available)
    # Or pre-process files to cover only Nigeria
    pass
```

---

### Option 2: Google Earth Engine (Simpler)

```python
import ee

# Initialize
ee.Initialize()

# Get CHIRPS precipitation
dataset = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
    .filterDate('2024-01-01', '2024-01-31')

# Extract for point
point = ee.Geometry.Point([3.3792, 6.5244])
values = dataset.getRegion(point, 5000).getInfo()

# Convert to DataFrame
df = pd.DataFrame(values[1:], columns=values[0])
```

---

## 📊 Comparison: Implementation Options

| Approach | MODIS | CHIRPS | Complexity | Time | Recommended |
|----------|-------|--------|------------|------|-------------|
| **AppEEARS API** | ✅ | ❌ | High | 40-60h | For production |
| **Google Earth Engine** | ✅ | ✅ | Medium | 20-30h | ⭐ Best balance |
| **Direct NetCDF** | ❌ | ✅ | Medium | 10-20h | For CHIRPS only |
| **Keep NASA POWER** | ✅ | ✅ | Zero | 0h | ⭐ Easiest |

---

## 🎯 Recommendations

### For Most Users: **Don't Implement**
**Use NASA POWER instead:**
- Temperature data covers LST use cases
- Precipitation data (PRECTOTCORR) covers CHIRPS use cases
- Solar radiation covers vegetation proxy
- **Zero implementation time**
- **Zero maintenance**

### For Specific MODIS Needs: **Use Google Earth Engine**
- Simpler than AppEEARS
- Faster results
- Better documentation
- Community support

### For Production MODIS: **Use AppEEARS API**
- Official NASA API
- Complete MODIS catalog
- Reliable long-term
- Good for automation

### For CHIRPS: **Use Google Earth Engine or NASA POWER**
- GEE: Easy CHIRPS access
- NASA POWER: Already implemented

---

## 📝 Next Steps

### If you decide to implement:

1. **Start with Google Earth Engine** (easiest):
   - Register: https://earthengine.google.com/
   - Install: `pip install earthengine-api`
   - Test with sample script
   - Integrate into portal

2. **Or stick with NASA POWER** (recommended):
   - Already works
   - Covers 90% of use cases
   - Zero maintenance

3. **Full implementation timeline**:
   - Week 1: Set up accounts and test APIs
   - Week 2: Implement authentication and task submission
   - Week 3: Implement data download and parsing
   - Week 4: UI integration and testing
   - Week 5: Error handling and edge cases
   - Week 6: Documentation and deployment

---

## 💡 Cost-Benefit Analysis

### MODIS/CHIRPS Implementation:
- **Time:** 40-80 hours
- **Complexity:** High
- **Maintenance:** Ongoing
- **Benefit:** Specific satellite products

### NASA POWER (Current):
- **Time:** 0 hours (done)
- **Complexity:** Low
- **Maintenance:** Zero
- **Benefit:** 90% of weather data needs

### **Recommendation:** Unless you specifically need NDVI, LST, or other satellite products that NASA POWER doesn't provide, stick with NASA POWER.

---

## 📞 Need Help?

If you decide to implement:

1. **Study the APIs first:**
   - AppEEARS: https://appeears.earthdatacloud.nasa.gov/api/
   - Earth Engine: https://developers.google.com/earth-engine
   - CHIRPS: https://data.chc.ucsb.edu/products/CHIRPS-2.0/

2. **Start small:**
   - Test with one location
   - Test with one week of data
   - Verify data quality

3. **Consider alternatives:**
   - NASA POWER for most weather data
   - Commercial APIs (planet.com, sentinel-hub)
   - Pre-processed datasets

---

**Bottom Line:** For a weather portal, **NASA POWER is sufficient for 90%+ of use cases**. Only implement MODIS/CHIRPS if you have specific requirements that NASA POWER cannot meet.
