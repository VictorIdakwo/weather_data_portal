"""
Quick ERA5-Land test via Earth Engine
"""
import json
import sys

# Load credentials
with open('ee_credentials.json', 'r') as f:
    credentials = json.load(f)

# Import and test
from data_sources.earth_engine_utils import fetch_era5_data

print("Testing ERA5-Land via Earth Engine...")
print("=" * 70)

# Test with just 2 days and 1 location (Lagos)
try:
    df = fetch_era5_data(
        locations=[(6.5244, 3.3792)],  # Lagos
        parameters=['temperature_2m', 'total_precipitation'],
        start_date='2024-09-01',
        end_date='2024-09-02',  # Just 2 days (48 hours)
        credentials_dict=credentials
    )
    
    if not df.empty:
        print(f"\n[SUCCESS] Retrieved {len(df)} records")
        print(f"\nFirst few records:")
        print(df.head(10))
        print(f"\nColumns: {list(df.columns)}")
        print(f"\nTemperature range: {df['temperature_2m'].min():.1f}°C to {df['temperature_2m'].max():.1f}°C")
        if 'total_precipitation' in df.columns:
            print(f"Precipitation sum: {df['total_precipitation'].sum():.2f} mm")
    else:
        print("\n[FAIL] No data retrieved")
        
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
