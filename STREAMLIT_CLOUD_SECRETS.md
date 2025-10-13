# 🔐 Streamlit Cloud Secrets Configuration

## What to Add to Your Streamlit Cloud Secrets

Your existing secrets already have `gee_credentials`. You just need to add **one line** for the analytics admin password.

---

## 📝 Updated Secrets Configuration

Your Streamlit Cloud secrets should look like this:

```toml
admin_password = "YourSecurePassword123"

[gee_credentials]
type = "service_account"
project_id = "ee-victoridakwo"
private_key_id = "9cfb0950436b25d51f238ebcb5e1040ee9ab5db3"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDnMR7Cvp6F3Upa\nfuM2poleICJxnJTZ/f8n5jWfYJGMOfJNgez/eSJWub4UVxZtdyp6SlfwtqnM93By\ntkv+ZaFDOCUoXmsMtFqBJ5H3TaaMtnXXPpdx19v1g5VDXQn9J5yYm7eBtobbQOqr\nK41eMuP9xwgO9dbujLH14BwV2XvKnZPQw6xc3LhCpcS1a3x9KM31qqVsLiwtfP2+\nswKPh9lDC8mOc1nKpWwOsi0XIBUacD3Pe7VJsGUawEu261MApFd7h7piDseuqPx4\nfbIFUiVDIaRpqGZRoIgl9Avd+vV5Foue2rYSxfFyTXi3+mqsyo8AtYxG7vcQ6+Lv\nelZWrh81AgMBAAECggEAT15ipBLS0zwUQZscH+/uatz3Vi+ePnRfe3Ah6pQ5g32F\nPKylE1OfwUxFADChp3TopVEOfboH8zDjbs48qppzUWNeBkzbzWHBTGOsTc1fpyEg\ntYNsdI3ZmqDQxm6TdlB6Bz42MpbaFz1jEt6BytwHv2Dr2E73ua+djL6ihbHDONxX\nDYRPQY1235cqOgRBpkMvzPutnxWqBB5DKXT8RLeKfsNdul2IOyI9Nn5o94X1hpl5\nI0QZiZrA3ayoISMKOCHW8zqp/NIXnGy2zarKmKnNPp/4gukZQ93tNdI6xXEerNbO\n53zBuYSu2ZNgV54XS8Cj44el7ruJaB5lXZkQFuQxJQKBgQD1pulb/QKQaQzXyW6B\neFpyy/HlzmQQbzQDTfkTROLlVIZUMeHcgFlF3TITlSMSZDY2evRflQrVbZRaVcSl\naqe4cNYARbHrF8LBX3cLHbaRNKa3lvC5iJPOzq/7o5hhl+wAdrbwhxa7LKr/3rQi\nID6KZGnVHvSA6S99tlUmh9C01wKBgQDw7kWgCQzoynmmDknJqk4ZcKjqGB05wBRl\nY1UXleE1t634jmb5Lkddymrczi2bT54JDSCRgHxAseYpf+HEYtFn1WQxYkI1dZdm\nRiU+w/dm8rzK3DvyC5xIbPh7akzd1r/i79gGJf334ca5ZdZA+Q0NRHjZDDitKWko\nYjRhXGs+0wKBgCCyRa9Dvtqf0ODL49SBw3AyKxFOZk01r/OcpkFlUtn5ZSPBu/FQ\neBFvfqHSoOdqxTh9Jxety9JakntvnQvzZT2Mbz98B1FmSTrZzQuCufEb0/Dtuz7G\nqf3FzvCsdrTOts/c/T6IjIL/UAdcihdcuVZMRTXjt+GMqBCQe0b0ntfjAoGARIs1\nSbtpbc004LZN7c7C21/+3mKv5d8srk+dRNGCOfsgxocU6q1s5lURI/KQbRAwoNiY\nPGz2bJ1wIrxcKbgHZWgDUj1nIrhqs1EfhYTRHPvQFFKlx03gT4aZBtuONMrE2rZr\nmgwy/dPA6rv7QY7ZVL33N6DPeww9+5w81LorVLsCgYEAnKgIcvQl011PS3xMSFS5\nDleVtxJ0jIQNPU5NX/xBgbESCtXB/E474y7USPLc8cYc8xPhgiS9Aa0OVyfP0gxl\nSsEONS5r3aAw2ym2UZnAwKavQfOR3T1wkP/mmJZXbbG5x3/tUL4NGCMf/vQraX0/\nVZAscmLkFFDhieJWtXaoEa8=\n-----END PRIVATE KEY-----\n"
client_email = "heatindex-analytics@ee-victoridakwo.iam.gserviceaccount.com"
client_id = "102740711274882741563"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/heatindex-analytics%40ee-victoridakwo.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

---

## 🚀 Steps to Update

1. **Go to Streamlit Cloud**: https://share.streamlit.io/
2. **Find your app**: `VictorIdakwo/weather_data_portal`
3. **Click** the ⋮ (three dots) → **Settings**
4. **Go to "Secrets" tab**
5. **Add this ONE line at the top** (before `[gee_credentials]`):
   ```toml
   admin_password = "YourSecurePassword123"
   ```
6. **Replace** `"YourSecurePassword123"` with your own secure password
7. **Click "Save"**
8. **Wait for automatic restart** (~30 seconds)

---

## 🔑 Choose a Strong Password

Examples:
- `"WeatherPortal2024!Admin"`
- `"eHA_Analytics#Secure@2024"`  
- `"MyAnalyticsDashboard_2024!"`

**Important:** Remember this password - you'll need it to access the analytics dashboard!

---

## ✅ What's Already Configured

- ✅ Google Sheets API enabled
- ✅ Google Drive API enabled
- ✅ Analytics spreadsheet created and shared
- ✅ All worksheets set up (Visits, Data_Sources, Downloads)
- ✅ Code deployed to GitHub

---

## 📊 Accessing Analytics After Deployment

1. Go to your Streamlit Cloud app URL
2. Look for **"📊 Admin Analytics"** in the sidebar
3. Click it
4. Enter your admin password
5. View your analytics dashboard!

---

## 🎉 That's It!

After adding the admin password to secrets:
- Your app will restart automatically
- Analytics will start tracking immediately
- You can access the dashboard with your password
- Location data will be captured for all visitors

**No other changes needed!** The app is ready to go. 🚀
