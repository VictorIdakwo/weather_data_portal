"""
Test script for earth globe visualization module
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.earth_globe import (
    create_earth_globe,
    create_animated_earth_globe,
    create_location_zoom_globe
)

def test_earth_globe():
    """Test the earth globe visualization functions"""
    
    # Test data: Some African cities
    test_locations = [
        (9.0820, 8.6753, "Abuja, Nigeria"),
        (6.5244, 3.3792, "Lagos, Nigeria"),
        (-1.2921, 36.8219, "Nairobi, Kenya"),
        (-26.2041, 28.0473, "Johannesburg, South Africa"),
        (30.0444, 31.2357, "Cairo, Egypt"),
        (5.6037, -0.1870, "Accra, Ghana"),
    ]
    
    print("Testing Earth Globe Visualization Module...")
    print(f"Test locations: {len(test_locations)}")
    
    try:
        # Test 1: Basic globe with all locations
        print("\n1. Testing basic globe creation...")
        fig1 = create_earth_globe(test_locations)
        print("   ✓ Basic globe created successfully")
        
        # Test 2: Globe zoomed to specific location
        print("\n2. Testing zoom to specific location...")
        fig2 = create_earth_globe(test_locations, zoom_to_location=0)
        print("   ✓ Zoom to location created successfully")
        
        # Test 3: Animated rotating globe
        print("\n3. Testing animated rotating globe...")
        fig3 = create_animated_earth_globe(test_locations)
        print("   ✓ Animated globe created successfully")
        
        # Test 4: Auto-zoom to all locations
        print("\n4. Testing auto-zoom to all locations...")
        fig4 = create_location_zoom_globe(test_locations)
        print("   ✓ Auto-zoom globe created successfully")
        
        # Test 5: Empty locations
        print("\n5. Testing with empty locations...")
        fig5 = create_earth_globe([])
        print("   ✓ Empty globe created successfully")
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
        print("\nThe earth globe visualization module is working correctly.")
        print("You can now run the Streamlit app to see it in action:")
        print("  streamlit run app.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_earth_globe()
    sys.exit(0 if success else 1)
