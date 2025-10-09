# 🛰️ Earth Engine Setup Guide

## MODIS and CHIRPS are now functional via Google Earth Engine!

### Step 1: Install Earth Engine API

```bash
pip install -r requirements.txt
```

This will install `earthengine-api` and all other dependencies.

### Step 2: Save Your Credentials

1. Get your Earth Engine service account credentials from Google Cloud Console
2. Create a file named `ee_credentials.json` in the project root directory
3. Paste your Google Earth Engine service account JSON credentials

**Format example:**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  ...
}
```

**Important:** The `.gitignore` file will prevent this from being committed to Git (security feature).
**Never share or commit your actual credentials to version control!**

### Step 3: Run the App

```bash
streamlit run app.py
```

### Step 4: Test MODIS

1. Select "MODIS" as data source
2. Select parameters:
   - MOD11A1.061_LST_Day_1km (Land Surface Temperature - Day)
   - MOD13Q1.061_250m_16_days_NDVI (NDVI - Vegetation)
3. Select a few locations (start with 1-2)
4. Select date range (e.g., last week or month)
5. Click "Fetch Weather Data"
6. Wait 30-60 seconds for Earth Engine processing
7. ✅ Real satellite data!

### Step 5: Test CHIRPS

1. Select "CHIRPS" as data source
2. Parameter "precipitation" is automatically selected
3. Select locations
4. Select date range
5. Click "Fetch Weather Data"
6. ✅ Real precipitation data from CHIRPS!

---

## 📊 What's Available

### MODIS via Earth Engine
- ✅ **LST (Land Surface Temperature)**
  - Day temperature
  - Night temperature
  - Converted to Celsius automatically

- ✅ **NDVI (Normalized Difference Vegetation Index)**
  - Vegetation health indicator
  - Scale: -1 to 1 (higher = more vegetation)
  - 16-day composite

- ⏳ **Coming Soon:**
  - EVI (Enhanced Vegetation Index)
  - ET (Evapotranspiration)
  - GPP (Gross Primary Productivity)

### CHIRPS via Earth Engine
- ✅ **Daily Precipitation**
  - mm per day
  - Global coverage
  - ~5km resolution

---

## 🔧 Troubleshooting

### Error: "Earth Engine initialization failed"

**Solution:**
1. Make sure `ee_credentials.json` exists in project root
2. Check JSON is properly formatted (no extra commas, proper quotes)
3. Run: `pip install --upgrade earthengine-api`

### Error: "No data retrieved"

**Possible reasons:**
1. Date range too large (start with 1 week)
2. Too many locations (start with 1-2)
3. Earth Engine processing timeout (try smaller request)

**Solution:** Start small and scale up:
- 1 location
- 1 week of data
- 1-2 parameters

### Error: "Connection timeout"

**Solution:**
- Check internet connection
- Try again (Earth Engine servers might be busy)
- Reduce number of locations or date range

---

## ⚡ Performance Tips

### For Faster Results:

1. **Start Small**
   - Test with 1 location first
   - 1 week of data
   - Then scale up

2. **Reasonable Limits**
   - Max 10 locations at once
   - Max 31 days for MODIS LST
   - Max 90 days for CHIRPS daily

3. **Be Patient**
   - MODIS: 30-90 seconds typical
   - CHIRPS: 20-60 seconds typical
   - More locations = more time

4. **Avoid Peak Times**
   - Earth Engine can be slower during US/Europe business hours
   - Try early morning or evening (your timezone)

---

## 📝 Example Requests

### Quick Test (30 seconds)
```
Data Source: MODIS
Parameters: LST_Day
Locations: Lagos (1 location)
Dates: 2024-09-01 to 2024-09-07 (7 days)
Expected: ~7 records in 30 seconds
```

### Medium Request (1-2 minutes)
```
Data Source: CHIRPS
Locations: 5 Nigerian states
Dates: 2024-09-01 to 2024-09-30 (30 days)
Expected: 150 records (5 locations × 30 days)
```

### Large Request (3-5 minutes)
```
Data Source: MODIS
Parameters: LST_Day + NDVI
Locations: 10 locations
Dates: 2024-08-01 to 2024-09-01 (31 days)
Expected: May take several minutes
```

---

## 🎉 Success!

You now have:
- ✅ Real MODIS satellite data
- ✅ Real CHIRPS precipitation data
- ✅ NASA POWER historical weather
- ✅ OpenWeather current/forecast
- ✅ Multiple export formats (CSV, Shapefile, JSON)

Your Weather Data Portal is now **fully functional** with all major data sources! 🚀

---

## 📞 Need Help?

If you encounter issues:
1. Check this setup guide
2. Review TROUBLESHOOTING.md
3. Check the console/terminal for detailed error messages
4. Start with smallest possible request to test connection

**Happy data fetching!** 🌍🛰️
