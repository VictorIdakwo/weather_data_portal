# 📊 Data Sources Quick Reference

## Which Data Source Should I Use?

### 🎯 Quick Decision Guide

**Need historical weather data (past months/years)?**
→ Use **NASA POWER** ✅ (Free, no API key)

**Need current weather or short-term forecast?**
→ Use **OpenWeather** (Free tier available, requires API key)

**Need high-quality climate research data?**
→ Use **ERA5** (Free, requires CDS account, slower)

---

## 📡 NASA POWER (Recommended for Most Use Cases)

### What is it?
NASA's Prediction of Worldwide Energy Resources - satellite-based weather and climate data

### ✅ Pros
- **Completely FREE** - no API key needed
- **Long history** - data from 1981 to ~7 days ago
- **Global coverage** - anywhere on Earth
- **Reliable** - NASA-managed infrastructure
- **Multiple parameters** - temperature, precipitation, humidity, wind, solar radiation
- **Multiple resolutions** - hourly, daily

### ❌ Limitations
- **Data latency** - ~7 day delay (latest data is from a week ago)
- **No real-time** - can't get today's weather
- **No forecasts** - past data only

### Best For
- ✅ Historical weather analysis
- ✅ Climate studies
- ✅ Agricultural planning
- ✅ Research projects
- ✅ Long-term trends

### Example Use Cases
- "Get temperature data for Lagos from 2020-2023"
- "Download precipitation for all Nigerian states, last 5 years"
- "Analyze wind patterns for the past decade"

---

## 🌤️ OpenWeather API

### What is it?
Real-time weather data and forecasts from OpenWeather

### ✅ Pros (Free Tier)
- **Real-time** - current weather conditions
- **Forecasts** - up to 7 days ahead
- **Fast** - immediate results
- **Multiple parameters** - temp, humidity, pressure, wind, clouds

### ❌ Limitations (Free Tier)
- **No historical data** - free tier doesn't include past weather
- **Requires API key** - must register at openweathermap.org
- **Rate limits** - 1000 calls/day for free tier
- **Limited forecast** - only 7 days ahead

### 💰 Historical Data (Paid Only)
Historical weather data requires **One Call API 3.0 subscription**:
- Cost: Varies by plan
- Website: https://openweathermap.org/api/one-call-3

### Best For
- ✅ Current weather conditions
- ✅ Short-term forecasts (1-7 days)
- ✅ Weather apps/dashboards
- ❌ NOT for historical analysis (use NASA POWER instead)

### Example Use Cases
- "What's the current temperature in Abuja?"
- "Get 5-day forecast for Lagos"
- "Monitor real-time weather for multiple locations"

---

## 🌍 ERA5 (Copernicus Climate Reanalysis)

### What is it?
High-quality climate reanalysis data from European Centre for Medium-Range Weather Forecasts (ECMWF)

### ✅ Pros
- **High quality** - research-grade data
- **Long history** - from 1940 to ~5 days ago
- **High resolution** - detailed spatial and temporal data
- **FREE** - no cost
- **Comprehensive** - extensive parameter list

### ❌ Limitations
- **Requires registration** - must create CDS account
- **API key needed** - CDS API credentials
- **SLOW** - requests can take 5-30 minutes to process
- **Queue system** - jobs are queued, not instant
- **Data latency** - ~5 day delay

### Best For
- ✅ Research projects
- ✅ Climate modeling
- ✅ High-quality historical analysis
- ❌ NOT for quick analysis (use NASA POWER instead)

### Example Use Cases
- "Research-grade climate data for thesis"
- "Detailed atmospheric pressure analysis"
- "High-resolution climate modeling"

---

## 🛰️ MODIS (Demo Only - NOT FUNCTIONAL)

### ⚠️ Current Status
**This is a placeholder/demo implementation that returns EMPTY data only.**

### Why Not Functional?
MODIS data requires:
- NASA Earthdata account
- Complex AppEEARS API workflow
- Asynchronous task submission and monitoring
- Authentication tokens
- Multi-step data retrieval process

### What You Get
- ❌ Empty DataFrame with None values
- ❌ No actual satellite data
- ✅ Data structure example only

### Alternative
**Use NASA POWER instead for satellite-derived data:**
- Land surface temperature
- Vegetation indices (indirect via solar radiation)
- Precipitation
- All FREE and functional

---

## 🌧️ CHIRPS (Demo Only - NOT FUNCTIONAL)

### ⚠️ Current Status
**This is a placeholder/demo implementation that returns EMPTY data only.**

### Alternative
**Use NASA POWER PRECTOTCORR parameter for precipitation data:**
- Free global precipitation data
- Daily resolution available
- Functional and reliable

---

## 🆚 Comparison Table

| Feature | NASA POWER | OpenWeather (Free) | ERA5 | MODIS | CHIRPS |
|---------|------------|-------------------|------|-------|--------|
| **Status** | ✅ Functional | ✅ Functional | ✅ Functional | ❌ Demo Only | ❌ Demo Only |
| **Returns Data** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Empty/None | ❌ Empty/None |
| **Cost** | FREE | FREE | FREE | N/A | N/A |
| **API Key** | ❌ Not needed | ✅ Required | ✅ Required | N/A | N/A |
| **Historical Data** | ✅ 1981 - 7 days ago | ❌ Paid only | ✅ 1940 - 5 days ago | ❌ | ❌ |
| **Current Weather** | ❌ No | ✅ Yes | ❌ No | ❌ | ❌ |
| **Forecasts** | ❌ No | ✅ 7 days | ❌ No | ❌ | ❌ |
| **Data Latency** | ~7 days | Real-time | ~5 days | N/A | N/A |
| **Speed** | Fast | Instant | Slow (5-30 min) | N/A | N/A |
| **Best For** | Historical analysis | Current/Forecast | Research | Demo only | Demo only |
| **Setup Difficulty** | ⭐ Easy | ⭐⭐ Moderate | ⭐⭐⭐ Complex | N/A | N/A |

**⚠️ Important:** MODIS and CHIRPS are placeholder implementations for demonstration purposes only. They return empty data structures. **Use NASA POWER for actual weather and precipitation data.**

---

## 📝 Recommendations by Use Case

### Student/Academic Research
**Use NASA POWER**
- Free, no API key hassle
- Good enough quality for most projects
- Easy to use
- Fast results

### Professional Climate Research
**Use ERA5**
- Highest quality data
- Worth the setup effort
- Industry standard
- Be patient with processing time

### Weather App/Dashboard
**Use OpenWeather**
- Real-time updates
- Current conditions + forecasts
- Fast and responsive

### Business/Agriculture Planning
**Use NASA POWER**
- Historical trends
- Free and reliable
- No API limits
- Easy integration

### If You Need Historical Data
**ALWAYS use NASA POWER or ERA5**
- OpenWeather free tier does NOT provide historical data
- Don't waste time trying to get past weather from OpenWeather free API

---

## 🔧 How to Get API Keys

### OpenWeather (Optional)
1. Visit: https://openweathermap.org/api
2. Click "Sign Up"
3. Create free account
4. Go to "API Keys" section
5. Copy your API key
6. Paste in app sidebar

**Note:** Only needed if you want current weather or forecasts. Skip this if using NASA POWER.

### ERA5 / CDS (Optional)
1. Visit: https://cds.climate.copernicus.eu/
2. Create account
3. Go to your profile
4. Find API key under "API Key" section
5. Copy UID and API key
6. Format: `UID:API_KEY`
7. Paste in app sidebar

**Note:** Only needed for ERA5 data. Skip this if using NASA POWER.

### NASA POWER
**No API key needed!** Just select NASA POWER and start fetching data. 🎉

---

## ❓ FAQ

**Q: Which data source should I use for my thesis?**
A: NASA POWER for most cases. ERA5 if you need the highest quality and have time.

**Q: Can I get yesterday's weather from OpenWeather?**
A: No, not with the free tier. Use NASA POWER instead (data from 7 days ago and earlier).

**Q: Why is my OpenWeather request failing for 2024-01-01?**
A: OpenWeather free tier doesn't support historical data. Switch to NASA POWER.

**Q: How far back can I get data?**
A: NASA POWER: 1981+, ERA5: 1940+, OpenWeather free: current + 7-day forecast only

**Q: Which is the fastest?**
A: OpenWeather (instant) > NASA POWER (fast) > ERA5 (slow, 5-30 min)

**Q: Which has the best data quality?**
A: ERA5 > NASA POWER > OpenWeather (all are good quality)

**Q: Do I need to pay for anything?**
A: No! NASA POWER is completely free and works great for most needs.

---

**Last Updated:** October 2025

For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
For examples, see [EXAMPLES.md](EXAMPLES.md)
