"""
Quick test script to verify NASA POWER API connectivity
"""
import requests
from datetime import datetime

# Test parameters
lat, lon = 6.5244, 3.3792  # Lagos
parameters = ["T2M", "PRECTOTCORR", "RH2M"]  # Test user's original params  
# Test daily which should work
temporal = "daily"  
start_date = "20240901"
end_date = "20240930"  # September 2024  

# Build URL
base_url = "https://power.larc.nasa.gov/api/temporal/"
params_str = ",".join(parameters)

url = (
    f"{base_url}{temporal}/point?"
    f"parameters={params_str}&"
    f"community=AG&"
    f"longitude={lon}&"
    f"latitude={lat}&"
    f"start={start_date}&"
    f"end={end_date}&"
    f"format=JSON"
)

print("=" * 70)
print("Testing NASA POWER API")
print("=" * 70)
print(f"\nURL: {url}\n")
print("Fetching data...")

try:
    response = requests.get(url, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n[SUCCESS] API is working!")
        print(f"\nResponse structure:")
        print(f"  - Top level keys: {list(data.keys())}")
        
        if "properties" in data:
            print(f"  - Properties keys: {list(data['properties'].keys())}")
            
            if "parameter" in data["properties"]:
                params = data["properties"]["parameter"]
                print(f"  - Parameters returned: {list(params.keys())}")
                
                for param_name, param_values in params.items():
                    if isinstance(param_values, dict):
                        print(f"    - {param_name}: {len(param_values)} records")
                        # Show first value
                        first_key = list(param_values.keys())[0]
                        print(f"      First: {first_key} = {param_values[first_key]}")
        
        if "errors" in data:
            print(f"\n[ERROR] API returned errors: {data['errors']}")
    else:
        print(f"\n[ERROR] HTTP Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as e:
    print(f"\n[ERROR] Error: {str(e)}")

print("\n" + "=" * 70)
print("Test complete!")
print("=" * 70)
