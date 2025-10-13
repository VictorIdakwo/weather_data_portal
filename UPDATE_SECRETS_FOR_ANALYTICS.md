# 🔐 Quick Guide: Update Streamlit Secrets for Analytics

## What You Need to Add

Add this **one line** to your existing Streamlit Cloud secrets:

```toml
admin_password = "YourSecurePassword123"
```

---

## Step-by-Step Instructions

### 1. Go to Streamlit Cloud
👉 https://share.streamlit.io/

### 2. Find Your App
Look for: `VictorIdakwo/weather_data_portal`

### 3. Open Settings
Click the **⋮** (three dots) → **Settings**

### 4. Go to Secrets Tab
Click on **"Secrets"**

### 5. Add Admin Password
You should see your existing `gee_credentials` section. Add the admin password **at the bottom**:

```toml
[gee_credentials]
type = "service_account"
project_id = "ee-victoridakwo"
private_key_id = "9cfb0950436b25d51f238ebcb5e1040ee9ab5db3"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
client_email = "heatindex-analytics@ee-victoridakwo.iam.gserviceaccount.com"
client_id = "102740711274882741563"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/heatindex-analytics%40ee-victoridakwo.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

admin_password = "YourSecurePassword123"
```

### 6. Choose a Strong Password
Replace `"YourSecurePassword123"` with your own secure password.

**Examples of strong passwords:**
- `"WeatherPortal2024!Admin"`
- `"eHA_Analytics#Secure@2024"`
- `"MyDataDashboard_2024!"`

### 7. Save
Click **"Save"** button

### 8. Wait for Restart
Your app will automatically restart (takes ~30-60 seconds)

---

## ✅ You're Done!

Now you can access the analytics dashboard:

1. Go to your app
2. Click **"📊 Admin Analytics"** in the sidebar
3. Enter your admin password
4. View your analytics!

---

## 🔒 Security Tips

- **Don't share** your admin password
- **Use a unique password** (not the same as other accounts)
- **Change it periodically** for better security
- **Remember it** - you'll need it to access analytics

---

## 🆘 Need Help?

If you forget your password:
1. Go back to Streamlit Cloud secrets
2. Change the `admin_password` value
3. Save and restart the app

That's it! Simple and secure.
