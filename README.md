# 🌍 Weather Data Portal for Africa

A comprehensive Streamlit-based web application for downloading and analyzing weather and climate data from multiple sources for locations across all African countries.

**Coverage:** All 54 African countries with their administrative divisions (States, Regions, Provinces, Counties, Departments, etc.)

**Created by:** Victor Iko-ojo Idakwo (RTP, MNITP, MGEOSON)  
**LinkedIn:** [https://www.linkedin.com/in/victor-idakwo-8a838a12a/](https://www.linkedin.com/in/victor-idakwo-8a838a12a/)  
**GitHub:** [https://github.com/VictorIdakwo](https://github.com/VictorIdakwo)

## 📋 Features

### Data Sources - ALL FUNCTIONAL! ✅

#### Primary Data Sources
- **NASA POWER** ⭐ **RECOMMENDED** - Free global meteorological and solar energy data (no API key needed)
  - Historical weather from 1981 to ~7 days ago
  - Instant results
  
- **OpenWeather API** - Real-time weather and forecasts (requires API key, free tier available)
  - Current weather + 7-day forecast
  - Instant results

- **ERA5** - ECMWF Reanalysis v5 climate data (requires CDS account)
  - High-quality climate reanalysis from 1940
  - Slower (5-30 minutes processing)

#### Satellite Data (via Google Earth Engine) 🆕
- **MODIS** ✅ **NOW FUNCTIONAL** - Real satellite data via Earth Engine
  - Land Surface Temperature (Day/Night)
  - Vegetation Indices (NDVI, EVI)
  - Processing time: 30-90 seconds
  
- **CHIRPS** ✅ **NOW FUNCTIONAL** - Real precipitation data via Earth Engine
  - Daily precipitation (mm)
  - Global coverage at ~5km resolution
  - Processing time: 20-60 seconds

### Available Parameters

#### NASA POWER
- Temperature (2m, max, min, dew point, wet bulb)
- Precipitation (corrected, sum)
- Humidity (relative, specific)
- Wind speed and direction (2m, 10m, 50m)
- Solar radiation (shortwave, longwave, direct normal)
- Surface pressure
- Evapotranspiration

#### OpenWeather
- Temperature and feels-like temperature
- Humidity and pressure
- Wind speed and direction
- Cloud cover
- Precipitation (rain, snow)

#### ERA5
- Temperature (2m, dewpoint, skin)
- Precipitation (total, convective)
- Pressure (surface, mean sea level)
- Wind components (10m U and V)
- Relative humidity
- Solar and thermal radiation
- Cloud cover (total, low, medium, high)
- Evaporation and potential evaporation

#### MODIS
- Land Surface Temperature (day/night, Terra/Aqua)
- Vegetation Indices (NDVI, EVI)
- Evapotranspiration
- Gross Primary Productivity
- Snow Cover

#### CHIRPS
- Precipitation data

### Temporal Resolutions
- **NASA POWER**: Hourly, Daily, Monthly
- **OpenWeather**: Hourly, Daily
- **ERA5**: Hourly, Daily, Monthly
- **MODIS**: Daily, 8-day, 16-day
- **CHIRPS**: Daily, Pentadal, Dekadal, Monthly

### Location Selection Options

1. **Nigeria States and LGAs**
   - Select from all 36 states + FCT
   - Choose specific Local Government Areas (LGAs)
   - Uses pre-defined centroids for each location

2. **Shapefile Upload**
   - Upload custom shapefiles (as ZIP)
   - Supports polygon geometries (centroid extracted)
   - Supports point geometries (used directly)
   - Automatic validation for Nigeria bounds

### Export Formats
- **CSV** - Comma-separated values
- **JSON** - JavaScript Object Notation
- **GeoJSON** - Geographic JSON format
- **Shapefile** - ESRI Shapefile (as ZIP)
- **Excel** - Microsoft Excel format (.xlsx)

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download this repository**

2. **Install required packages**

```bash
pip install -r requirements.txt
```

3. **Set up API keys (if needed)**

Copy the `.env.example` file to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
# OpenWeather API Key (get from https://openweathermap.org/api)
OPENWEATHER_API_KEY=your_api_key_here

# Copernicus CDS API credentials (get from https://cds.climate.copernicus.eu/)
CDS_API_URL=https://cds.climate.copernicus.eu/api/v2
CDS_API_KEY=your_uid:your_api_key_here

# NASA Earthdata credentials (for MODIS, get from https://urs.earthdata.nasa.gov/)
NASA_USERNAME=your_username_here
NASA_PASSWORD=your_password_here
```

### Running the Application

Run the Streamlit app:

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## 📖 Usage Guide

### Step 1: Select Data Source
1. In the sidebar, choose your desired data source from the dropdown menu
2. The available parameters will update based on your selection

### Step 2: Select Parameters
1. Expand the parameter categories (Temperature, Precipitation, etc.)
2. Check the boxes for the parameters you want to download
3. You can select multiple parameters

### Step 3: Choose Temporal Resolution
- Select the time interval for data aggregation (Hourly, Daily, Monthly, etc.)
- Available options depend on the data source

### Step 4: Set Date Range
- Choose start and end dates for your data request
- Be mindful that large date ranges may take longer to process

### Step 5: Configure API Keys (if needed)
- For OpenWeather API: Enter your API key
- For ERA5: Enter your CDS API key in format `uid:api_key`

### Step 6: Select Locations

**Option A: Nigeria States/LGAs**
1. Select one or more states from the dropdown
2. Optionally, select specific LGAs within those states
3. If no LGAs are selected, state centroids will be used

**Option B: Upload Shapefile**
1. Prepare a ZIP file containing your shapefile (.shp, .shx, .dbf, .prj)
2. Click "Browse files" and select your ZIP file
3. The app will extract locations (centroids for polygons, points directly)

### Step 7: Fetch Data
1. Click the "Fetch Weather Data" button
2. Wait for the data to be retrieved (progress indicator will show)
3. Preview the data in the table

### Step 8: Export Data
1. Select your desired export format (CSV, JSON, GeoJSON, Shapefile, Excel)
2. Click "Download Data"
3. The file will be prepared and ready for download

## 🔑 API Key Setup

### OpenWeather API
1. Sign up at [OpenWeather](https://openweathermap.org/api)
2. Get your free API key from your account
3. Note: Free tier has limitations on historical data

### Copernicus CDS (for ERA5)
1. Register at [Copernicus CDS](https://cds.climate.copernicus.eu/user/register)
2. Accept the license terms
3. Get your UID and API key from your profile
4. Format as `uid:api_key`

### NASA Earthdata (for MODIS)
1. Register at [NASA Earthdata](https://urs.earthdata.nasa.gov/users/new)
2. Accept the EULA for AppEEARS
3. Use your username and password

## 📂 Project Structure

```
Weather Data Portal/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Example environment variables
├── README.md                  # This file
├── data_sources/              # Data source modules
│   ├── __init__.py
│   ├── nasa_power.py         # NASA POWER API integration
│   ├── openweather.py        # OpenWeather API integration
│   ├── era5.py               # ERA5 Copernicus CDS integration
│   ├── modis.py              # MODIS AppEEARS integration
│   └── chirps.py             # CHIRPS data integration
└── utils/                     # Utility modules
    ├── __init__.py
    ├── nigeria_locations.py   # Nigeria states and LGAs data
    ├── shapefile_handler.py   # Shapefile processing utilities
    └── export_handler.py      # Data export utilities
```

## ⚠️ Important Notes

### Data Availability
- **NASA POWER**: No API key required, freely available
- **OpenWeather**: Free tier limited to current weather and short-term forecast
- **ERA5**: Requires CDS account, data requests can be slow (queue-based)
- **MODIS**: Requires NASA Earthdata account, implementation simplified
- **CHIRPS**: Freely available but requires file download and processing

### Performance Considerations
- Large date ranges will take longer to process
- Multiple locations increase processing time
- ERA5 requests are queued and may take several minutes
- Consider breaking large requests into smaller chunks

### Data Processing
- MODIS and CHIRPS implementations are simplified demonstrations
- For production use, implement full API workflows:
  - MODIS: Complete AppEEARS task submission and retrieval
  - CHIRPS: GeoTIFF download and raster extraction

### Data Limitations
- Historical data availability varies by source
- Some sources have spatial resolution limitations
- Temporal resolution affects data volume and processing time

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**API authentication errors**
- Verify your API keys are correct
- Check that you've accepted all license terms
- Ensure API key format is correct (especially for CDS)

**Slow data retrieval**
- ERA5 requests go through a queue system
- Reduce date range or number of parameters
- Consider using a different data source for faster results

**Shapefile upload errors**
- Ensure ZIP contains all required files (.shp, .shx, .dbf, .prj)
- Check that coordinate system is WGS84 (EPSG:4326)
- Verify locations are within Nigeria bounds

## 📚 Additional Resources

- [NASA POWER Documentation](https://power.larc.nasa.gov/docs/)
- [OpenWeather API Documentation](https://openweathermap.org/api)
- [Copernicus CDS Documentation](https://cds.climate.copernicus.eu/api-how-to)
- [MODIS Data Products](https://modis.gsfc.nasa.gov/data/)
- [CHIRPS Documentation](https://www.chc.ucsb.edu/data/chirps)

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Complete MODIS AppEEARS workflow implementation
- Complete CHIRPS GeoTIFF processing implementation
- Add more data sources (e.g., TRMM, SRTM)
- Implement data visualization features
- Add data quality checks and validation
- Improve error handling and user feedback

## 📧 Support

For issues, questions, or suggestions, please open an issue in the repository or contact the development team.

---

**Developed for eHealth Africa**

Last updated: October 2025
