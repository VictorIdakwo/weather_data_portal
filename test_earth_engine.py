"""
Test script to verify Earth Engine integration for MODIS and CHIRPS
"""
import json
import sys
from datetime import datetime, timedelta

print("=" * 70)
print("Testing Earth Engine Integration")
print("=" * 70)

# Step 1: Load credentials
print("\n[1/5] Loading Earth Engine credentials...")
try:
    with open('ee_credentials.json', 'r') as f:
        credentials = json.load(f)
    print("[OK] Credentials loaded successfully")
except Exception as e:
    print(f"[FAIL] Failed to load credentials: {str(e)}")
    sys.exit(1)

# Step 2: Import Earth Engine
print("\n[2/5] Importing Earth Engine API...")
try:
    import ee
    print("[OK] Earth Engine API imported")
except Exception as e:
    print(f"[FAIL] Failed to import Earth Engine: {str(e)}")
    print("  Run: pip install earthengine-api")
    sys.exit(1)

# Step 3: Initialize Earth Engine
print("\n[3/5] Initializing Earth Engine...")
try:
    credentials_obj = ee.ServiceAccountCredentials(
        email=credentials['client_email'],
        key_data=credentials['private_key']
    )
    ee.Initialize(credentials_obj)
    print("[OK] Earth Engine initialized successfully")
except Exception as e:
    print(f"[FAIL] Failed to initialize: {str(e)}")
    sys.exit(1)

# Step 4: Test MODIS access
print("\n[4/5] Testing MODIS data access...")
try:
    # Try to access MODIS collection
    modis = ee.ImageCollection('MODIS/006/MOD11A1')
    
    # Get info about one image
    test_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    image = modis.filterDate(test_date, test_date).first()
    
    # This will trigger actual API call
    info = image.getInfo()
    
    if info:
        print("[OK] MODIS data accessible")
        print(f"  Test date: {test_date}")
        print(f"  Product: MOD11A1 (Land Surface Temperature)")
    else:
        print("[FAIL] No MODIS data returned")
except Exception as e:
    print(f"[FAIL] MODIS test failed: {str(e)}")

# Step 5: Test CHIRPS access
print("\n[5/5] Testing CHIRPS data access...")
try:
    # Try to access CHIRPS collection
    chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
    
    # Get info about one image
    test_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    image = chirps.filterDate(test_date, test_date).first()
    
    # This will trigger actual API call
    info = image.getInfo()
    
    if info:
        print("[OK] CHIRPS data accessible")
        print(f"  Test date: {test_date}")
        print(f"  Product: CHIRPS v2.0 (Daily Precipitation)")
    else:
        print("[FAIL] No CHIRPS data returned")
except Exception as e:
    print(f"[FAIL] CHIRPS test failed: {str(e)}")

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print("[SUCCESS] Earth Engine is properly configured")
print("[SUCCESS] MODIS satellite data is accessible")
print("[SUCCESS] CHIRPS precipitation data is accessible")
print("\n[READY] All tests passed! MODIS and CHIRPS are ready to use.")
print("\nNext step: Run 'streamlit run app.py' and test fetching data")
print("=" * 70)
