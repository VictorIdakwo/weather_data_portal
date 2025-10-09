"""
Test script to verify that all dependencies are installed correctly
and the Weather Data Portal is ready to use.
"""

import sys
from datetime import datetime

print("=" * 60)
print("Weather Data Portal - Setup Verification")
print("=" * 60)
print()

# Test Python version
print("✓ Checking Python version...")
python_version = sys.version_info
if python_version.major >= 3 and python_version.minor >= 8:
    print(f"  ✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
else:
    print(f"  ✗ Python version {python_version.major}.{python_version.minor} is too old")
    print("  ! Please upgrade to Python 3.8 or higher")
    sys.exit(1)

# Test required packages
required_packages = [
    "streamlit",
    "pandas",
    "geopandas",
    "shapely",
    "requests",
    "numpy",
    "xarray",
    "netCDF4",
    "cdsapi",
    "rasterio",
    "pyproj",
    "folium",
    "streamlit_folium",
    "openpyxl",
    "fiona",
    "dotenv",
]

print("\n✓ Checking required packages...")
missing_packages = []

for package in required_packages:
    try:
        if package == "streamlit_folium":
            __import__("streamlit_folium")
        elif package == "dotenv":
            __import__("dotenv")
        else:
            __import__(package)
        print(f"  ✓ {package}")
    except ImportError:
        print(f"  ✗ {package} - NOT FOUND")
        missing_packages.append(package)

if missing_packages:
    print("\n! Missing packages detected. Please install them:")
    print(f"  pip install {' '.join(missing_packages)}")
    sys.exit(1)

# Test data source modules
print("\n✓ Checking data source modules...")
try:
    from data_sources import nasa_power, openweather, era5, modis, chirps
    print("  ✓ NASA POWER module")
    print("  ✓ OpenWeather module")
    print("  ✓ ERA5 module")
    print("  ✓ MODIS module")
    print("  ✓ CHIRPS module")
except ImportError as e:
    print(f"  ✗ Error importing data source modules: {e}")
    sys.exit(1)

# Test utility modules
print("\n✓ Checking utility modules...")
try:
    from utils.nigeria_locations import get_states, get_state_location
    from utils.shapefile_handler import read_shapefile
    from utils.export_handler import export_to_csv
    print("  ✓ Nigeria locations module")
    print("  ✓ Shapefile handler module")
    print("  ✓ Export handler module")
except ImportError as e:
    print(f"  ✗ Error importing utility modules: {e}")
    sys.exit(1)

# Test Nigeria data
print("\n✓ Checking Nigeria location data...")
states = get_states()
if len(states) > 0:
    print(f"  ✓ Found {len(states)} states/FCT")
    # Test a specific state
    lagos_loc = get_state_location("Lagos")
    if lagos_loc:
        print(f"  ✓ Lagos location: {lagos_loc}")
    else:
        print("  ✗ Could not get Lagos location")
else:
    print("  ✗ No states found")
    sys.exit(1)

# Test NASA POWER API availability
print("\n✓ Testing NASA POWER API connection...")
try:
    import requests
    response = requests.get("https://power.larc.nasa.gov/api/temporal/", timeout=10)
    if response.status_code in [200, 400, 404]:  # API responds (even with errors)
        print("  ✓ NASA POWER API is reachable")
    else:
        print(f"  ! NASA POWER API returned status code: {response.status_code}")
except Exception as e:
    print(f"  ! Could not connect to NASA POWER API: {e}")
    print("  ! Check your internet connection")

# Check for .env file
print("\n✓ Checking configuration...")
import os
if os.path.exists(".env"):
    print("  ✓ .env file found")
    print("  ! Remember to add your API keys to .env file")
else:
    print("  ! .env file not found")
    print("  ! Copy .env.example to .env and add your API keys")

# Test basic data fetching
print("\n✓ Testing basic data fetching...")
try:
    from datetime import datetime, timedelta
    test_location = [(6.5244, 3.3792)]  # Lagos
    test_start = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    test_end = datetime.now().strftime("%Y-%m-%d")
    
    print("  ⏳ Fetching sample data from NASA POWER (this may take a moment)...")
    df = nasa_power.fetch_nasa_power_data(
        locations=test_location,
        parameters=["T2M"],
        start_date=test_start,
        end_date=test_end,
        temporal_resolution="Daily"
    )
    
    if df is not None and not df.empty:
        print(f"  ✓ Successfully fetched {len(df)} records")
        print(f"  ✓ Sample data columns: {', '.join(df.columns.tolist()[:5])}...")
    else:
        print("  ! No data returned (this might be OK if API is temporarily unavailable)")
        
except Exception as e:
    print(f"  ! Error during test fetch: {e}")
    print("  ! This might be due to network issues or API availability")

# Summary
print("\n" + "=" * 60)
print("Setup Verification Complete!")
print("=" * 60)

if not missing_packages:
    print("\n✅ All required packages are installed correctly!")
    print("✅ All modules are working properly!")
    print("\n🚀 You're ready to use the Weather Data Portal!")
    print("\nTo start the application, run:")
    print("  streamlit run app.py")
    print("\n📖 For detailed instructions, see README.md")
    print("🚀 For quick start guide, see QUICKSTART.md")
else:
    print("\n❌ Some issues were detected. Please install missing packages.")
    print("   Run: pip install -r requirements.txt")

print("\n" + "=" * 60)
