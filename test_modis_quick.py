"""
Quick MODIS test with small date range
"""
import json
import sys

# Load credentials
with open('ee_credentials.json', 'r') as f:
    credentials = json.load(f)

# Import and test
from data_sources.earth_engine_utils import fetch_modis_lst

print("Testing MODIS with small date range...")
print("=" * 70)

# Test with just 7 days and 1 location (Lagos)
try:
    df = fetch_modis_lst(
        locations=[(6.5244, 3.3792)],  # Lagos
        start_date='2024-09-01',
        end_date='2024-09-07',  # Just 7 days
        product='day',
        credentials_dict=credentials
    )
    
    if not df.empty:
        print(f"\n[SUCCESS] Retrieved {len(df)} records")
        print(f"\nFirst few records:")
        print(df.head())
        print(f"\nColumns: {list(df.columns)}")
    else:
        print("\n[FAIL] No data retrieved")
        
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
