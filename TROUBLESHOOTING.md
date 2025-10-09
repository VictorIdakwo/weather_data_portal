# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "No data retrieved" with NASA POWER

#### Symptoms:
```
⚠️ No data retrieved. Please check your parameters and try again.
```

#### Common Causes and Solutions:

**A. Incompatible Parameters for Hourly Data**

**Problem:** Selecting parameters like `T2M_MAX` or `T2M_MIN` with Hourly resolution.

**Solution:**
- These parameters are only available for **Daily** or **Monthly** resolution
- Either:
  1. Change to Daily/Monthly resolution, OR
  2. Use hourly-compatible parameters:
     - ✅ T2M (Temperature)
     - ✅ T2MDEW (Dew Point) 
     - ✅ RH2M (Humidity)
     - ✅ WS2M (Wind Speed)
     - ✅ PRECTOTCORR (Precipitation)

**B. Data Too Recent (Data Latency)**

**Problem:** Selecting dates within the last 7 days.

**Solution:**
- NASA POWER has ~7 day data latency
- Select dates at least **7 days in the past**
- Latest available: Check the sidebar warning for exact date
- **Example:** Use dates from last month: `2024-09-01` to `2024-09-30`

**C. Large Date Range with Hourly Data**

**Problem:** Requesting hourly data for 1000+ days.

**Solution:**
- Hourly data works best for **30-90 days**
- For longer periods:
  - Use **Daily** resolution (good for up to 10 years)
  - Use **Monthly** resolution (good for 20+ years)

---

### Issue 2: Timeout Errors

#### Symptoms:
```
Timeout fetching data for location...
```

#### Solution:
1. **Reduce date range**: Try shorter periods
2. **Change resolution**: Use Daily instead of Hourly
3. **Reduce parameters**: Select fewer parameters (2-3 instead of 6+)
4. **Reduce locations**: Try 1-2 locations first

---

### Issue 3: Duplicate Widget Keys (OpenWeather)

#### Symptoms:
```
StreamlitDuplicateElementKey: There are multiple elements with the same key
```

#### Solution:
- **Already Fixed!** The app now creates unique keys for each parameter
- If you still see this, refresh the app (Ctrl+R)

---

### Issue 4: Installation Errors

#### Symptoms:
```
ModuleNotFoundError: No module named 'cdsapi'
```

#### Solution:
```powershell
pip install -r requirements.txt
```

If specific packages fail:
```powershell
# Install individually
pip install streamlit pandas geopandas requests numpy
pip install cdsapi xarray netCDF4 rasterio
```

---

## Best Practices

### ✅ Recommended Configurations

**For Quick Testing:**
```
- Data Source: NASA POWER
- Parameters: T2M, PRECTOTCORR (2 parameters)
- Resolution: Daily
- Date Range: Last month (30 days)
- Locations: 1-2 states
```

**For Climate Analysis:**
```
- Data Source: NASA POWER
- Parameters: 3-5 parameters
- Resolution: Monthly
- Date Range: 5-10 years
- Locations: Multiple states
```

**For Hourly Weather:**
```
- Data Source: NASA POWER
- Parameters: T2M, RH2M, WS2M (avoid MAX/MIN)
- Resolution: Hourly
- Date Range: 7-30 days
- Locations: 1-2 locations
```

---

## Data Source Specific Issues

### NASA POWER

**Limitations:**
- ⏱️ 7 day data latency
- 🔄 Some parameters only for Daily/Monthly
- ⚡ Large hourly requests can timeout

**Solutions:**
- Use dates at least 7 days old
- Check parameter compatibility
- Limit hourly requests to <90 days

### OpenWeather API

**Limitations:**
- 🔑 Requires API key
- 📅 Historical data requires subscription
- ⏰ Mainly for current + 7-day forecast

**Solutions:**
- Get free API key from openweathermap.org
- For historical, use NASA POWER instead
- Best for current weather and short forecasts

### ERA5

**Limitations:**
- 🔑 Requires CDS account
- ⏱️ 5 day data latency  
- ⏳ Requests can take 5-30 minutes

**Solutions:**
- Register at cds.climate.copernicus.eu
- Be patient - requests are queued
- Use for high-quality climate data only

---

## Error Messages Reference

### "API key is required"
**Solution:** Add your API key in the sidebar configuration section

### "Start date must be before end date"
**Solution:** Check your date inputs - start should be earlier than end

### "No valid parameters for hourly data"
**Solution:** All selected parameters are incompatible with hourly. Change to Daily/Monthly.

### "HTTP 422" or "One of your parameters is incorrect"
**Solution:** Parameter not available for selected resolution. Check compatibility.

### "Timeout"
**Solution:** Request too large. Reduce date range, resolution, or number of locations.

---

## Getting Help

### Check These First:
1. ✅ Date range is valid (not in future for NASA POWER)
2. ✅ Parameters are compatible with resolution
3. ✅ API keys are correct (if required)
4. ✅ Internet connection is working

### Still Having Issues?

Run the test script to verify API connectivity:
```powershell
python test_nasa_power.py
```

Check terminal/console output for detailed error messages.

---

## Quick Fixes

### Reset Everything
If the app seems stuck or behaving oddly:
1. Click the hamburger menu (☰) in Streamlit
2. Choose "Rerun"
3. Or press **Ctrl+R** to refresh

### Clear Cache
If data seems outdated:
1. Click hamburger menu (☰)
2. Choose "Clear cache"

### Restart App
```powershell
# Stop the app (Ctrl+C in terminal)
# Then restart:
streamlit run app.py
```

---

**Last Updated:** October 2025

For more examples, see [EXAMPLES.md](EXAMPLES.md)
For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md)
