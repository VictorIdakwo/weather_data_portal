# 📊 Analytics Dashboard Setup Guide

Your Weather Data Portal now includes a powerful analytics system that tracks:
- 📈 **Page Visits** - Total visitors to your app
- 🌍 **Data Source Usage** - Which data sources users are fetching from
- ⬇️ **Downloads** - What formats users are downloading

All data is stored in a Google Sheet and accessible via a password-protected admin dashboard.

---

## 🎯 What's New

### **Analytics Features:**
1. **Automatic Tracking**
   - Every page visit is recorded (once per session)
   - Data source usage tracked (data source, parameters, locations, date range)
   - Downloads tracked (format, data source, row count)

2. **Admin Dashboard**
   - Password-protected page at `/📊_Admin_Analytics`
   - Beautiful visualizations with Plotly charts
   - Real-time data from Google Sheets
   - Export analytics data to Excel

3. **Privacy-Friendly**
   - Anonymous tracking (no personal data)
   - Session-based IDs only
   - Minimal data collection

---

## 🚀 Setup Instructions

### **Step 1: Google Sheets Permissions**

The analytics system uses your existing Google Earth Engine service account. We need to grant it access to Google Sheets API.

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select your project**: `ee-victoridakwo`
3. **Enable Google Sheets API**:
   - Go to "APIs & Services" → "Enable APIs and Services"
   - Search for "Google Sheets API"
   - Click "Enable"
4. **Enable Google Drive API** (also needed):
   - Same process - search for "Google Drive API"
   - Click "Enable"

**That's it!** Your existing service account (`heatindex-analytics@ee-victoridakwo.iam.gserviceaccount.com`) now has access to create and manage Google Sheets.

---

### **Step 2: Set Admin Password**

Add an admin password to your Streamlit Cloud secrets:

1. **Go to**: https://share.streamlit.io/
2. **Find your app**: `VictorIdakwo/weather_data_portal`
3. **Click**: Settings (⋮ menu) → Secrets
4. **Add this line** at the bottom of your existing secrets:

```toml
admin_password = "YourSecurePassword123"
```

5. **Click "Save"**

**Choose a strong password!** This protects your analytics dashboard.

---

### **Step 3: First Run**

1. **Visit your app**: The analytics system will automatically initialize
2. **On first run**: A Google Sheet named `Weather_Portal_Analytics` will be created
3. **Check your Google Drive**: You should see the spreadsheet
4. **Access dashboard**: Go to your app URL and add `/📊_Admin_Analytics` at the end
   - Example: `https://your-app.streamlit.app/📊_Admin_Analytics`

---

## 📊 Using the Analytics Dashboard

### **Accessing the Dashboard:**

1. Open your app
2. Look for the page selector in the sidebar
3. Click "📊 Admin Analytics"
4. Enter your admin password
5. View your analytics!

### **Dashboard Features:**

#### **Summary Metrics**
- Total Visits
- Data Fetches
- Downloads

#### **Tabs:**

1. **📅 Overview**
   - Visits over time (line chart)
   - Recent visits table

2. **🌍 Data Sources**
   - Data source distribution (pie chart)
   - Usage count (bar chart)
   - Usage over time (line chart)
   - Popular parameters
   - Recent data fetches

3. **⬇️ Downloads**
   - Export format distribution
   - Downloads by data source
   - Downloads over time
   - Total rows downloaded
   - Recent downloads

4. **📊 Raw Data**
   - Full data tables
   - Export to Excel option

---

## 🔧 Technical Details

### **How It Works:**

1. **Google Sheets as Database**
   - Three worksheets: Visits, Data_Sources, Downloads
   - Automatic creation on first run
   - Real-time updates

2. **Analytics Module** (`utils/analytics.py`)
   - `Analytics` class handles all tracking
   - Uses `gspread` library
   - Silently fails if not configured (won't break app)

3. **Tracking in App** (`app.py`)
   - Visit tracking on page load
   - Data source tracking after successful fetch
   - Download tracking on button click

4. **Admin Dashboard** (`pages/1_📊_Admin_Analytics.py`)
   - Password protection via Streamlit secrets
   - Plotly visualizations
   - Pandas data processing

### **Data Structure:**

**Visits Sheet:**
```
Timestamp | Session_ID | User_Country | User_City
```

**Data_Sources Sheet:**
```
Timestamp | Session_ID | Data_Source | Parameters | Locations_Count | Date_Range
```

**Downloads Sheet:**
```
Timestamp | Session_ID | Data_Source | Format | Rows_Count | Locations_Count
```

---

## 🔒 Security & Privacy

### **What's Tracked:**
- ✅ Anonymous session IDs
- ✅ Timestamps
- ✅ Data source selections
- ✅ Download formats

### **What's NOT Tracked:**
- ❌ Personal information
- ❌ IP addresses
- ❌ Email addresses
- ❌ User names
- ❌ Actual data content

### **Access Control:**
- Admin dashboard is password-protected
- Google Sheet can only be accessed by your service account
- No public access to analytics data

---

## 🎨 Customization

### **Change Admin Password:**

Update in Streamlit Cloud secrets:
```toml
admin_password = "NewPassword123"
```

### **Disable Analytics:**

If you want to disable analytics temporarily:

1. Remove or comment out these lines in `app.py`:
```python
# analytics.track_visit()
# analytics.track_data_source_usage(...)
# analytics.track_download(...)
```

### **Custom Visualizations:**

Edit `pages/1_📊_Admin_Analytics.py` to add your own charts or metrics.

---

## 📈 Example Insights You Can Get

- **Most Popular Data Sources**: See which data sources users prefer
- **Peak Usage Times**: Identify when users are most active
- **Popular Parameters**: Know which weather parameters are in demand
- **Download Preferences**: See which export formats are most popular
- **Location Trends**: Track how many locations users typically select
- **Date Range Patterns**: Understand typical date ranges users request

---

## 🐛 Troubleshooting

### **"Analytics not enabled" message:**
- Check Google Sheets API is enabled
- Check Google Drive API is enabled
- Verify your service account credentials are in Streamlit secrets

### **"Password incorrect":**
- Check `admin_password` in Streamlit secrets
- Ensure no extra spaces or quotes

### **Data not showing:**
- Wait a few seconds for Google Sheets to sync
- Refresh the analytics page
- Check the Google Sheet exists in your Drive

### **Charts not loading:**
- Ensure `plotly>=5.18.0` is in requirements.txt
- Check browser console for errors
- Try clearing browser cache

---

## 📝 Updates to Your App

### **New Files Created:**
1. `utils/analytics.py` - Analytics tracking module
2. `pages/1_📊_Admin_Analytics.py` - Admin dashboard page
3. `ANALYTICS_SETUP.md` - This guide

### **Modified Files:**
1. `app.py` - Added analytics tracking
2. `requirements.txt` - Added gspread, google-auth, plotly

### **No Changes Required:**
- Your existing Earth Engine credentials work for analytics
- No new API keys needed
- No additional costs

---

## 🎯 Next Steps

1. ✅ Enable Google Sheets API & Drive API
2. ✅ Set admin password in Streamlit secrets
3. ✅ Save and restart your app
4. ✅ Visit the app to initialize analytics
5. ✅ Access the admin dashboard
6. ✅ Start getting insights!

---

## 💡 Tips

- **Check analytics weekly** to understand usage patterns
- **Export data** regularly for long-term storage
- **Monitor popular parameters** to improve default selections
- **Track download formats** to prioritize export options
- **Use insights** to guide feature development

---

## 🔗 Resources

- [Google Cloud Console](https://console.cloud.google.com/)
- [Streamlit Cloud](https://share.streamlit.io/)
- [gspread Documentation](https://docs.gspread.org/)
- [Plotly Documentation](https://plotly.com/python/)

---

## ✅ Summary

You now have a complete analytics system that:
- 📊 Tracks all user interactions automatically
- 🔒 Protects data with password authentication
- 📈 Provides beautiful visualizations
- 💾 Stores data in Google Sheets (free & reliable)
- 🎯 Gives you actionable insights

**No coding required after setup!** Just enable the APIs, set your password, and you're ready to go.

---

**Created by Victor Iko-ojo Idakwo (RTP, MNITP, MGEOSON)**  
Weather Data Portal • Powered by Google Earth Engine
