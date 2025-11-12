"""
Debug script to test location detection accuracy
Run this to see what different IP geolocation services detect for your location
"""

import streamlit as st
from utils.analytics import Analytics
import json

# Page config
st.set_page_config(
    page_title="Location Debug",
    page_icon="🌍",
    layout="wide"
)

st.title("🔍 Location Detection Debug")
st.markdown("This tool helps debug IP geolocation accuracy issues")

# Create analytics instance for testing
analytics = Analytics()

if st.button("🧪 Test Location Detection"):
    st.markdown("### Testing all geolocation services...")
    
    with st.spinner("Checking multiple IP geolocation services..."):
        results = analytics.debug_location_detection()
    
    # Display results
    st.markdown("### Results from all services:")
    
    for service_name, result in results.items():
        if result['success']:
            country = result['country']
            city = result['city']
            ip = result['ip']
            isp = result['isp']
            
            # Color code based on accuracy
            if country == 'Nigeria':
                st.success(f"✅ **{service_name}**: {country}, {city} (IP: {ip}, ISP: {isp})")
            elif country in ['United States', 'US']:
                st.error(f"❌ **{service_name}**: {country}, {city} (IP: {ip}, ISP: {isp}) - **INCORRECT!**")
            else:
                st.warning(f"⚠️ **{service_name}**: {country}, {city} (IP: {ip}, ISP: {isp}) - **Verify accuracy**")
        else:
            st.error(f"❌ **{service_name}**: Failed - {result['error']}")
    
    # Show detailed data
    with st.expander("🔍 View Raw Response Data"):
        for service_name, result in results.items():
            if result['success']:
                st.markdown(f"#### {service_name}")
                st.json(result['full_data'])

# Explanation section
st.markdown("---")
st.markdown("### 🤔 Why Location Detection Can Be Wrong")

st.markdown("""
**Common reasons for location misdetection:**

1. **🌐 VPN/Proxy Usage**
   - If you're using a VPN, it will show the VPN server location
   - Corporate proxies can route traffic through different countries

2. **🏢 ISP Routing**
   - Some Nigerian ISPs route international traffic through US/European gateways
   - This makes your IP appear to originate from those locations

3. **☁️ Cloud/CDN Services**
   - If your traffic goes through CloudFlare, Akamai, or similar CDNs
   - The detected location might be the CDN edge server location

4. **📡 Satellite Internet**
   - Satellite connections often show incorrect locations
   - Ground stations might be in different countries

5. **🏗️ Infrastructure**
   - Poor IP geolocation database coverage for some regions
   - Outdated or incorrect ISP registration data
""")

st.markdown("### 💡 Solutions")

st.markdown("""
**To improve accuracy:**

1. **🔍 Check Multiple Services**: The app now uses 4 different services and picks the most reliable one

2. **📊 Priority System**: 
   - `ipinfo.io` (highest priority - most accurate)
   - `ip-api.com` (good for ISP info)
   - `ipwhois.app` (backup)
   - `ipapi.co` (fallback)

3. **🚨 Conflict Detection**: The app now detects when services disagree and logs this for analysis

4. **🎯 Manual Override**: Consider adding a manual location selection option for users who want to specify their actual location
""")

# Current detection
st.markdown("### 🎯 Current Detection Result")
current_country, current_city = analytics._get_user_location()
st.info(f"**Currently detected as**: {current_country}, {current_city}")

if current_country == 'Nigeria':
    st.success("✅ Correct detection!")
elif current_country in ['United States', 'US']:
    st.error("❌ Incorrect - showing US instead of Nigeria")
    st.markdown("""
    **This suggests:**
    - Your ISP routes traffic through US gateways
    - You might be using a VPN/proxy
    - Your IP is registered to a US-based service provider
    """)
else:
    st.warning(f"⚠️ Detected as {current_country} - please verify if this is correct")
