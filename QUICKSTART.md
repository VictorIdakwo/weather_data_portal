# 🚀 Quick Start Guide - UPDATED

## ✅ MODIS & CHIRPS NOW WORKING!

Your Weather Data Portal is fully functional with **all 5 data sources** working:
- NASA POWER (historical weather)
- OpenWeather (current/forecast)
- ERA5 (climate research)
- **MODIS (satellite data) ✅ NEW!**
- **CHIRPS (precipitation) ✅ NEW!**

---

# 🚀 Quick Start Guide

## For Windows Users

### Step 1: Install Python
If you don't have Python installed:
1. Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Run the installer and check "Add Python to PATH"
3. Verify installation by opening PowerShell and typing:
   ```powershell
   python --version
   ```

### Step 2: Set Up the Project

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd "c:\Users\victor.idakwo\Documents\ehealth Africa\ehealth Africa\eHA GitHub\Weather Data Portal"
   ```

2. Create a virtual environment (recommended):
   ```powershell
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   If you get an error about execution policies, run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```

### Step 3: Configure API Keys (Optional but Recommended)

1. Copy the example environment file:
   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` file with your text editor and add your API keys:
   - **NASA POWER**: No API key needed ✅
   - **OpenWeather**: Get free API key from [openweathermap.org](https://openweathermap.org/api)
   - **ERA5**: Register at [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu/)
   - **MODIS/CHIRPS**: Optional for advanced usage

### Step 4: Run the Application

```powershell
streamlit run app.py
```

The app will automatically open in your web browser at `http://localhost:8501`

## Quick Test Run

### Test with NASA POWER (No API Key Required)

1. **Select Data Source**: NASA POWER
2. **Select Parameters**: 
   - Expand "Temperature" → Check "Temperature at 2 Meters (°C)"
   - Expand "Precipitation" → Check "Precipitation Corrected (mm/day)"
3. **Temporal Resolution**: Daily
4. **Date Range**: Last 7 days
5. **Location**: Select "Lagos" and "FCT" from States
6. **Click**: "Fetch Weather Data"
7. **Export**: Choose CSV format and download

### Expected Result
You should see a table with temperature and precipitation data for Lagos and FCT for the past 7 days.

## Troubleshooting

### Issue: "pip is not recognized"
**Solution**: Make sure Python is added to PATH, or use:
```powershell
python -m pip install -r requirements.txt
```

### Issue: "streamlit is not recognized"
**Solution**: 
1. Make sure virtual environment is activated
2. Or use: `python -m streamlit run app.py`

### Issue: Package installation fails
**Solution**: 
1. Try upgrading pip: `python -m pip install --upgrade pip`
2. Install packages one by one to identify the problematic one
3. For GDAL-related packages (geopandas, rasterio, fiona):
   - Download pre-built wheels from [gohlke](https://www.lfd.uci.edu/~gohlke/pythonlibs/)
   - Install using: `pip install package-name.whl`

### Issue: "No module named 'data_sources'"
**Solution**: Make sure you're running the command from the project root directory

### Issue: "Execution policy" error when activating venv
**Solution**: Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy RemoteSigned
```

## Next Steps

1. **Add API Keys**: For OpenWeather and ERA5 to access more data sources
2. **Upload Shapefiles**: Try uploading custom location shapefiles
3. **Export Data**: Experiment with different export formats
4. **Multiple Parameters**: Select multiple parameters to analyze relationships
5. **Large Date Ranges**: Test with longer time periods (be patient, it may take time!)

## Tips for Best Experience

- Start with small date ranges to test
- NASA POWER is the fastest data source
- ERA5 requests can take several minutes (queue-based)
- Use CSV or JSON for quick data analysis
- Use Shapefile/GeoJSON for GIS applications
- Select multiple states to compare regional differences

## Need Help?

- Check the main README.md for detailed documentation
- Review error messages carefully - they often indicate what's wrong
- Make sure API keys are correctly formatted
- Verify internet connection for data downloads

---

**Happy Data Exploring! 🌦️📊**
