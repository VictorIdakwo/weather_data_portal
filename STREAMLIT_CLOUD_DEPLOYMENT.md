# 🚀 Streamlit Cloud Deployment Guide

Complete guide to deploy your Weather Data Portal to Streamlit Cloud with Google Earth Engine credentials.

---

## 📋 Prerequisites

1. ✅ GitHub repository: https://github.com/VictorIdakwo/weather_data_portal.git
2. ✅ Streamlit Cloud account (free): https://streamlit.io/cloud
3. ✅ Google Earth Engine credentials (JSON format)

---

## 🌐 Step 1: Deploy to Streamlit Cloud

### **1.1 Go to Streamlit Cloud**
- Visit: https://share.streamlit.io/
- Click **"New app"**

### **1.2 Connect Your Repository**
- **Repository:** `VictorIdakwo/weather_data_portal`
- **Branch:** `main`
- **Main file path:** `app.py`

### **1.3 Click "Deploy"**
Wait for initial deployment (will show error about missing credentials - this is expected!)

---

## 🔐 Step 2: Add Earth Engine Credentials

### **2.1 Access App Settings**
1. After deployment, click on your app
2. Click the **"⋮"** menu (three dots) in the top right
3. Select **"Settings"**
4. Go to **"Secrets"** tab

### **2.2 Add Your GEE Credentials**

Copy and paste your Google Earth Engine credentials in this **exact format**:

```toml
# .streamlit/secrets.toml format for Streamlit Cloud

[gee_credentials]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = """-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY_CONTENT_HERE
-----END PRIVATE KEY-----
"""
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

### **2.3 Important Notes:**
- ⚠️ Use **triple quotes** `"""` around the private key
- ⚠️ Keep the line breaks in the private key
- ⚠️ Replace ALL placeholder values with your actual credentials
- ⚠️ The format is **TOML**, not JSON

### **2.4 Example Structure:**

```toml
[gee_credentials]
type = "service_account"
project_id = "ee-yourproject"
private_key_id = "abc123def456..."
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
(your full private key here, keep line breaks)
...VZAscmLkFFDhieJWtXaoEa8=
-----END PRIVATE KEY-----
"""
client_email = "your-service@ee-yourproject.iam.gserviceaccount.com"
client_id = "123456789012345678901"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service%40ee-yourproject.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

### **2.5 Save Secrets**
1. Click **"Save"** at the bottom
2. Streamlit will automatically restart your app
3. Wait ~1-2 minutes for the app to reload

---

## ✅ Step 3: Verify Deployment

### **3.1 Check App Status**
- Your app should now be running without errors
- The main page should load successfully

### **3.2 Test Earth Engine Data Sources**

**Test MODIS:**
1. Select **"MODIS"** as data source
2. Choose **"LST_Day"** parameter
3. Select a location (e.g., Nigeria → Lagos)
4. Click **"Fetch Weather Data"**
5. ✅ Should return real satellite data

**Test CHIRPS:**
1. Select **"CHIRPS"** as data source
2. Choose **"precipitation"** parameter
3. Select locations
4. Click **"Fetch Weather Data"**
5. ✅ Should return precipitation data

**Test ERA5-Land:**
1. Select **"ERA5"** as data source
2. Choose parameters
3. Select locations
4. Click **"Fetch Weather Data"**
5. ✅ Should return climate data

### **3.3 Test Other Features**
- ✅ NASA POWER (no credentials needed)
- ✅ OpenWeather (if you add API key as secret)
- ✅ Multi-country selection
- ✅ LGA selection for Nigeria
- ✅ Data export (CSV, Excel, etc.)

---

## 🔧 Optional: Add OpenWeather API Key

If you want to use OpenWeather API, add this to your secrets:

```toml
# OpenWeather API Key (optional)
openweather_api_key = "your-openweather-api-key-here"
```

Then update the app to read from secrets:
```python
# In app.py, update OpenWeather key input
openweather_api_key = st.secrets.get("openweather_api_key", "")
```

---

## 📱 Step 4: Share Your App

### **4.1 Get Your App URL**
Your app will be available at:
```
https://your-username-weather-data-portal-app-xxx.streamlit.app
```

### **4.2 Share the URL**
- Share with colleagues
- Add to your LinkedIn profile
- Include in research papers
- Use for data collection

### **4.3 Custom Domain (Optional)**
Streamlit Cloud allows custom domains on paid plans.

---

## 🛠️ Troubleshooting

### **Problem: "No Earth Engine credentials found"**

**Solution:**
1. Check secrets are properly formatted in TOML
2. Ensure `[gee_credentials]` section header is present
3. Verify triple quotes around private key
4. Save and wait for app to restart

### **Problem: "Earth Engine initialization failed"**

**Solution:**
1. Verify your service account has Earth Engine access
2. Check project_id matches your GEE project
3. Ensure private_key has correct line breaks
4. Try redeploying the app

### **Problem: "Module not found" errors**

**Solution:**
1. Check `requirements.txt` is in repository root
2. Verify all dependencies are listed
3. Redeploy app (Streamlit will reinstall packages)

### **Problem: App is slow or times out**

**Solution:**
1. Reduce date range (use <90 days)
2. Select fewer locations (start with 1-2)
3. Use NASA POWER first (fastest, no auth)
4. MODIS/CHIRPS/ERA5 need more time for first request

### **Problem: Private key format errors**

**Solution:**
```toml
# WRONG - Don't escape newlines
private_key = "-----BEGIN PRIVATE KEY-----\nMIIE..."

# CORRECT - Use triple quotes and preserve line breaks
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAo...
...
-----END PRIVATE KEY-----
"""
```

---

## 🎯 How It Works

### **Local Development:**
- App reads credentials from `ee_credentials.json` file
- File is in `.gitignore` (not pushed to GitHub)
- Safe for local testing

### **Streamlit Cloud:**
- App reads credentials from `st.secrets['gee_credentials']`
- Secrets stored securely in Streamlit Cloud
- Never exposed in code or logs

### **Code (Already Updated):**
```python
def load_ee_credentials():
    try:
        # First, try Streamlit Cloud secrets (for deployment)
        if hasattr(st, 'secrets') and 'gee_credentials' in st.secrets:
            return dict(st.secrets['gee_credentials'])
        
        # Fallback to local file (for development)
        creds_path = "ee_credentials.json"
        if os.path.exists(creds_path):
            with open(creds_path, 'r') as f:
                return json.load(f)
        
        return None
    except Exception as e:
        st.sidebar.warning(f"Error loading credentials")
        return None
```

---

## 📊 Deployment Checklist

### **Before Deployment:**
- ✅ Code pushed to GitHub
- ✅ `requirements.txt` includes all dependencies
- ✅ `.gitignore` excludes credentials
- ✅ App works locally

### **During Deployment:**
- ✅ Connected GitHub repository
- ✅ Selected correct branch (main)
- ✅ Specified app.py as main file
- ✅ Added GEE credentials to secrets
- ✅ Saved secrets and restarted app

### **After Deployment:**
- ✅ App loads without errors
- ✅ Tested MODIS data source
- ✅ Tested CHIRPS data source
- ✅ Tested ERA5 data source
- ✅ Tested NASA POWER
- ✅ Tested location selection
- ✅ Tested data export

---

## 🎓 TOML Format Guide

### **What is TOML?**
TOML (Tom's Obvious, Minimal Language) is Streamlit Cloud's secrets format.

### **Key Rules:**
```toml
# Comments start with #
key = "simple value"
number = 123

# Section headers in square brackets
[section_name]
key1 = "value1"
key2 = "value2"

# Multi-line strings use triple quotes
long_text = """
Line 1
Line 2
Line 3
"""

# No commas between items!
```

### **Your GEE Credentials Template:**
```toml
[gee_credentials]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_KEY_ID"
private_key = """-----BEGIN PRIVATE KEY-----
YOUR_FULL_PRIVATE_KEY_WITH_LINE_BREAKS
-----END PRIVATE KEY-----
"""
client_email = "YOUR_SERVICE_ACCOUNT_EMAIL"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"
universe_domain = "googleapis.com"
```

---

## 🔒 Security Best Practices

### **DO:**
- ✅ Use Streamlit Cloud secrets for credentials
- ✅ Keep local `ee_credentials.json` in `.gitignore`
- ✅ Never commit credentials to Git
- ✅ Rotate credentials periodically
- ✅ Use service accounts (not personal accounts)

### **DON'T:**
- ❌ Commit credentials to GitHub
- ❌ Share credentials in chat/email
- ❌ Hardcode credentials in code
- ❌ Store credentials in public files
- ❌ Use same credentials for multiple apps

---

## 📈 Performance Tips

### **For Best Performance:**
1. **Start Small:** Test with 1-2 locations first
2. **Date Ranges:** Use <30 days for faster results
3. **NASA POWER:** Fastest, use for quick testing
4. **MODIS/CHIRPS:** Need ~30-60 seconds
5. **ERA5:** Can take ~60-90 seconds

### **Caching (Future Enhancement):**
Consider adding Streamlit caching:
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_weather_data(...):
    # Your data fetching code
```

---

## 🎉 Success!

Once deployed, your app will be:
- ✅ **Publicly accessible** via URL
- ✅ **Secure** (credentials protected)
- ✅ **Fast** (Streamlit Cloud infrastructure)
- ✅ **Scalable** (handles multiple users)
- ✅ **Professional** (shareable URL)

### **Your Live App:**
```
https://victoridakwo-weather-data-portal-app.streamlit.app
(or similar)
```

---

## 📞 Support

### **Streamlit Cloud Help:**
- Docs: https://docs.streamlit.io/streamlit-community-cloud
- Forum: https://discuss.streamlit.io/
- Status: https://status.streamlit.io/

### **App Issues:**
- Check GitHub repository
- Review documentation files
- Test locally first

---

## 🚀 Ready to Deploy?

1. **Push latest code** (already done ✅)
2. **Go to Streamlit Cloud**: https://share.streamlit.io/
3. **Click "New app"**
4. **Connect repository**: `VictorIdakwo/weather_data_portal`
5. **Add secrets** (copy from your local `ee_credentials.json`)
6. **Deploy!**

---

**Created by:** Victor Iko-ojo Idakwo (RTP, MNITP, MGEOSON)  
**Repository:** https://github.com/VictorIdakwo/weather_data_portal.git  
**Status:** Ready for Streamlit Cloud Deployment ✅

---

# 🌍 Let's Make Your Portal Live! 🌍
