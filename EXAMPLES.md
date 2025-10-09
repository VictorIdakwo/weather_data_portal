# 📚 Usage Examples

## Example 1: Download Temperature Data for Lagos

### Steps:
1. **Data Source**: Select "NASA POWER"
2. **Parameters**: 
   - Expand "Temperature"
   - Check "Temperature at 2 Meters (°C)"
   - Check "Maximum Temperature at 2 Meters (°C)"
   - Check "Minimum Temperature at 2 Meters (°C)"
3. **Temporal Resolution**: Select "Daily"
4. **Date Range**: 
   - Start: 2024-01-01
   - End: 2024-01-31
5. **Location**: 
   - Select "Lagos" from States dropdown
6. **Fetch**: Click "Fetch Weather Data"
7. **Export**: Select "CSV" and download

### Expected Output:
A CSV file with daily temperature data for Lagos in January 2024.

---

## Example 2: Compare Precipitation Across Multiple States

### Steps:
1. **Data Source**: Select "NASA POWER"
2. **Parameters**:
   - Expand "Precipitation"
   - Check "Precipitation Corrected (mm/day)"
3. **Temporal Resolution**: Select "Monthly"
4. **Date Range**:
   - Start: 2023-01-01
   - End: 2023-12-31
5. **Location**:
   - Select multiple states: "Lagos", "Kano", "Rivers", "FCT"
6. **Fetch**: Click "Fetch Weather Data"
7. **Export**: Select "Excel" format

### Use Case:
Compare monthly precipitation patterns across different regions of Nigeria in 2023.

---

## Example 3: Wind Speed Analysis for Wind Farm Planning

### Steps:
1. **Data Source**: Select "NASA POWER"
2. **Parameters**:
   - Expand "Wind"
   - Check "Wind Speed at 50 Meters (m/s)"
   - Check "Wind Direction at 50 Meters (Degrees)"
3. **Temporal Resolution**: Select "Hourly"
4. **Date Range**:
   - Start: 2024-06-01
   - End: 2024-06-07 (one week)
5. **Location**:
   - Select "Plateau" state
6. **Fetch**: Click "Fetch Weather Data"
7. **Export**: Select "CSV"

### Use Case:
Assess wind energy potential at 50m height for potential wind farm locations.

---

## Example 4: Agricultural Planning with Multiple Parameters

### Steps:
1. **Data Source**: Select "NASA POWER"
2. **Parameters**:
   - Temperature: "Temperature at 2 Meters (°C)"
   - Precipitation: "Precipitation Corrected (mm/day)"
   - Humidity: "Relative Humidity at 2 Meters (%)"
   - Solar: "All Sky Surface Shortwave Downward Irradiance"
3. **Temporal Resolution**: Select "Daily"
4. **Date Range**:
   - Start: 2023-03-01
   - End: 2023-09-30 (growing season)
5. **Location**:
   - Select agricultural states: "Kaduna", "Kano", "Niger", "Benue"
6. **Fetch**: Click "Fetch Weather Data"
7. **Export**: Select "GeoJSON" for GIS analysis

### Use Case:
Analyze growing season conditions across major agricultural states.

---

## Example 5: Using Custom Locations with Shapefile

### Scenario:
You have GPS coordinates of health facilities and need weather data for each location.

### Steps:
1. **Prepare Shapefile**:
   - Create a shapefile with point locations
   - Ensure it's in WGS84 (EPSG:4326)
   - Include attributes like facility name
   - Zip all components (.shp, .shx, .dbf, .prj)

2. **Upload**:
   - Select "Upload Shapefile" option
   - Choose your ZIP file
   - Verify locations are displayed correctly

3. **Data Source**: Select "NASA POWER"

4. **Parameters**:
   - Temperature: "Temperature at 2 Meters (°C)"
   - Humidity: "Relative Humidity at 2 Meters (%)"

5. **Temporal Resolution**: Select "Daily"

6. **Date Range**: Last 30 days

7. **Fetch**: Click "Fetch Weather Data"

8. **Export**: Select "Shapefile" to maintain spatial attributes

### Use Case:
Environmental monitoring for health facilities - correlate weather with disease patterns.

---

## Example 6: Current Weather Conditions (OpenWeather)

### Steps:
1. **Setup**: Add OpenWeather API key in .env file

2. **Data Source**: Select "OpenWeather API"

3. **Parameters**:
   - Check "Temperature (°C)"
   - Check "Humidity (%)"
   - Check "Wind Speed (m/s)"
   - Check "Pressure (hPa)"

4. **Temporal Resolution**: Select "Hourly"

5. **Date Range**:
   - Start: Today's date
   - End: 2 days from now (forecast)

6. **Location**:
   - Select "Lagos", "FCT", "Port Harcourt"

7. **Fetch**: Click "Fetch Weather Data"

8. **Export**: Select "JSON"

### Use Case:
Get current weather and short-term forecast for operational planning.

---

## Example 7: Climate Analysis with ERA5

### Steps:
1. **Setup**: Register at Copernicus CDS and add API key

2. **Data Source**: Select "ERA5 (Copernicus)"

3. **Parameters**:
   - Expand "Temperature"
   - Check "2m Temperature (K)"
   - Expand "Precipitation"
   - Check "Total Precipitation (m)"

4. **Temporal Resolution**: Select "Monthly"

5. **Date Range**:
   - Start: 2020-01-01
   - End: 2023-12-31 (4 years)

6. **Location**:
   - Select: "Lagos", "Kano", "Rivers"

7. **Fetch**: Click "Fetch Weather Data" (be patient, this can take 10-20 minutes)

8. **Export**: Select "CSV"

### Use Case:
Long-term climate trend analysis using high-quality reanalysis data.

---

## Example 8: Precipitation Monitoring with CHIRPS

### Steps:
1. **Data Source**: Select "CHIRPS"

2. **Parameters**:
   - Check "Precipitation (mm)"

3. **Temporal Resolution**: Select "Monthly"

4. **Date Range**:
   - Start: 2023-01-01
   - End: 2023-12-31

5. **Location**:
   - Select all northern states for drought monitoring

6. **Fetch**: Click "Fetch Weather Data"

7. **Export**: Select "Excel"

### Use Case:
Drought monitoring and precipitation analysis for northern Nigeria.

---

## Example 9: Multi-LGA Analysis

### Steps:
1. **Data Source**: Select "NASA POWER"

2. **Parameters**:
   - Temperature: "Temperature at 2 Meters (°C)"
   - Precipitation: "Precipitation Corrected (mm/day)"

3. **Temporal Resolution**: Select "Daily"

4. **Date Range**: Last 90 days

5. **Location**:
   - Select State: "Lagos"
   - Select Multiple LGAs:
     - Ikeja
     - Lagos Island
     - Lagos Mainland
     - Epe
     - Badagry
     - Ikorodu

6. **Fetch**: Click "Fetch Weather Data"

7. **Export**: Select "Shapefile"

### Use Case:
Intra-city climate variation analysis across Lagos metropolis.

---

## Example 10: Solar Energy Assessment

### Steps:
1. **Data Source**: Select "NASA POWER"

2. **Parameters**:
   - Expand "Solar Radiation"
   - Check "All Sky Surface Shortwave Downward Irradiance (kW-hr/m^2/day)"
   - Check "All Sky Surface Shortwave Direct Normal Irradiance"

3. **Temporal Resolution**: Select "Monthly"

4. **Date Range**:
   - Start: 2022-01-01
   - End: 2024-12-31 (3 years)

5. **Location**:
   - Select multiple states across different regions

6. **Fetch**: Click "Fetch Weather Data"

7. **Export**: Select "CSV"

### Use Case:
Solar panel site selection and energy yield estimation.

---

## Tips for Effective Use

### 1. Start Small
- Test with short date ranges first
- Use fewer locations initially
- Select 2-3 parameters to start

### 2. Optimize Performance
- NASA POWER is fastest for testing
- Avoid large date ranges with hourly data
- Consider monthly resolution for multi-year analyses

### 3. Data Quality
- NASA POWER: Most reliable for historical data
- OpenWeather: Best for current/forecast
- ERA5: Highest quality but slowest

### 4. Export Format Selection
- **CSV**: Data analysis in Excel/Python/R
- **JSON**: Web applications and APIs
- **GeoJSON**: Quick GIS visualization
- **Shapefile**: Full GIS analysis in QGIS/ArcGIS
- **Excel**: Sharing with non-technical users

### 5. API Key Management
- Keep API keys secure
- Don't share .env file
- Check API usage limits
- Use free tiers for testing

### 6. Common Workflows

**Workflow A: Quick Analysis**
```
NASA POWER → Daily → 1 month → 1-3 locations → CSV
```

**Workflow B: Detailed Study**
```
ERA5 → Hourly → 1 week → Multiple locations → Shapefile
```

**Workflow C: Long-term Trends**
```
NASA POWER → Monthly → 5 years → Multiple states → Excel
```

**Workflow D: Real-time Monitoring**
```
OpenWeather → Hourly → Current + 2 days → Key locations → JSON
```

---

## Python Script Examples

### Analyzing Exported CSV Data

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load exported CSV
df = pd.read_csv('weather_data_NASA_POWER_20241009.csv')

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Calculate average temperature by location
avg_temp = df.groupby('location_name')['T2M'].mean()
print(avg_temp)

# Plot temperature trend
plt.figure(figsize=(12, 6))
for location in df['location_name'].unique():
    loc_data = df[df['location_name'] == location]
    plt.plot(loc_data['date'], loc_data['T2M'], label=location)

plt.xlabel('Date')
plt.ylabel('Temperature (°C)')
plt.title('Temperature Trends by Location')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('temperature_trends.png')
plt.show()
```

### Processing GeoJSON in Python

```python
import geopandas as gpd
import matplotlib.pyplot as plt

# Load GeoJSON
gdf = gpd.read_file('weather_data_NASA_POWER_20241009.geojson')

# Plot precipitation on map
fig, ax = plt.subplots(figsize=(10, 8))
gdf.plot(column='PRECTOTCORR', cmap='Blues', legend=True, ax=ax)
ax.set_title('Precipitation Distribution')
plt.savefig('precipitation_map.png')
plt.show()
```

---

## Troubleshooting Common Scenarios

### Scenario 1: No Data Returned
**Possible Causes**:
- Invalid date range
- Data not available for that period
- API temporarily down

**Solution**:
- Try shorter date range
- Check data source availability dates
- Try different data source

### Scenario 2: API Key Error
**Issue**: "API key is required"

**Solution**:
- Verify .env file exists
- Check API key format
- Ensure no extra spaces in key

### Scenario 3: Slow Performance
**Issue**: Data fetching takes too long

**Solution**:
- Reduce date range
- Fewer parameters
- Use lower temporal resolution
- Try NASA POWER instead of ERA5

### Scenario 4: Export Fails
**Issue**: Cannot generate export file

**Solution**:
- Check disk space
- Verify data was fetched
- Try different export format
- Check for special characters in data

---

**More examples and updates available in the project repository!**
