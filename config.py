"""
Configuration settings for Weather Data Portal
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
CDS_API_URL = os.getenv("CDS_API_URL", "https://cds.climate.copernicus.eu/api/v2")
CDS_API_KEY = os.getenv("CDS_API_KEY", "")
NASA_USERNAME = os.getenv("NASA_USERNAME", "")
NASA_PASSWORD = os.getenv("NASA_PASSWORD", "")

# Nigeria Geographic Bounds
NIGERIA_BOUNDS = {
    "min_lat": 4.0,
    "max_lat": 14.0,
    "min_lon": 2.5,
    "max_lon": 15.0,
}

# Data Source URLs
DATA_SOURCE_URLS = {
    "nasa_power": "https://power.larc.nasa.gov/api/temporal/",
    "openweather": "https://api.openweathermap.org/data/2.5/",
    "openweather_onecall": "https://api.openweathermap.org/data/3.0/onecall/",
    "cds": "https://cds.climate.copernicus.eu/api/v2",
    "appeears": "https://appeears.earthdatacloud.nasa.gov/api/",
    "chirps": "https://data.chc.ucsb.edu/products/CHIRPS-2.0",
}

# Temporal Resolution Mappings
TEMPORAL_RESOLUTION_MAP = {
    "Hourly": "hourly",
    "Daily": "daily",
    "Monthly": "monthly",
    "Pentadal": "pentad",
    "Dekadal": "dekad",
    "8-day": "8day",
    "16-day": "16day",
}

# Export Settings
EXPORT_FORMATS = ["CSV", "JSON", "GeoJSON", "Shapefile", "Excel"]

# Maximum number of locations per request
MAX_LOCATIONS = 100

# Maximum date range (days)
MAX_DATE_RANGE_DAYS = 365

# Timeout settings (seconds)
API_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 300

# Cache settings
ENABLE_CACHE = True
CACHE_TTL = 3600  # 1 hour in seconds

# Logging
LOG_LEVEL = "INFO"
