"""
Analytics tracking module for Weather Data Portal
Tracks page visits, data source usage, and downloads.

Security notes:
- Sheet ID is read from secrets / env, not hard-coded.
- Analytics credentials can be supplied separately from GEE credentials
  via st.secrets['analytics_credentials']; if absent, analytics is disabled
  unless ANALYTICS_ALLOW_GEE_FALLBACK is explicitly set.
- The analytics sheet is never auto-shared with 'anyone'. If the sheet
  does not exist, analytics is disabled rather than created publicly.
"""

import os
import json
from datetime import datetime

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd


# --- Configuration helpers ----------------------------------------------------

def _get_sheet_id():
    """Read the analytics Google Sheet ID from secrets or env.

    Returns None when not configured (in which case analytics is disabled).
    """
    # st.secrets access can raise if no secrets file exists locally
    try:
        if hasattr(st, "secrets"):
            if "analytics" in st.secrets and "sheet_id" in st.secrets["analytics"]:
                return st.secrets["analytics"]["sheet_id"]
            if "ANALYTICS_SHEET_ID" in st.secrets:
                return st.secrets["ANALYTICS_SHEET_ID"]
    except Exception:
        pass
    return os.environ.get("ANALYTICS_SHEET_ID")


def _allow_gee_fallback():
    """Whether GEE credentials may be used for analytics if no dedicated
    analytics credentials are configured. Off by default.
    """
    try:
        if hasattr(st, "secrets") and "analytics" in st.secrets:
            return bool(st.secrets["analytics"].get("allow_gee_fallback", False))
    except Exception:
        pass
    return os.environ.get("ANALYTICS_ALLOW_GEE_FALLBACK", "").lower() in ("1", "true", "yes")


# --- Analytics class ----------------------------------------------------------

class Analytics:
    """Analytics tracker using Google Sheets as backend.

    Disabled (no-op) unless both credentials and a sheet ID are configured.
    """

    def __init__(self, credentials_dict=None, sheet_id=None):
        self.client = None
        self.sheet = None
        self.enabled = False

        if not credentials_dict or not sheet_id:
            return

        try:
            self._initialize_sheets(credentials_dict, sheet_id)
            self.enabled = True
        except Exception:
            # Silently disable on any initialization failure.
            self.enabled = False

    def _initialize_sheets(self, credentials_dict, sheet_id):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",  # narrower than /drive
        ]
        credentials = Credentials.from_service_account_info(
            credentials_dict, scopes=scopes
        )
        self.client = gspread.authorize(credentials)

        # Strictly open an existing sheet by ID. Never create or share publicly.
        self.sheet = self.client.open_by_key(sheet_id)
        self._ensure_worksheets()

    def _ensure_worksheets(self):
        """Make sure the expected tabs exist; never alter sharing settings."""
        if not self.sheet:
            return

        worksheets = {
            "Visits": ["Timestamp", "Session_ID", "User_Country", "User_City"],
            "Data_Sources": [
                "Timestamp", "Session_ID", "Data_Source", "Parameters",
                "Locations_Count", "Date_Range",
            ],
            "Downloads": [
                "Timestamp", "Session_ID", "Data_Source", "Format",
                "Rows_Count", "Locations_Count",
            ],
        }
        for sheet_name, headers in worksheets.items():
            try:
                self.sheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                ws = self.sheet.add_worksheet(
                    title=sheet_name, rows=1000, cols=len(headers)
                )
                ws.append_row(headers)

    # --- Session + geolocation helpers --------------------------------------

    def _get_session_id(self):
        if "analytics_session_id" not in st.session_state:
            st.session_state.analytics_session_id = datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            )
        return st.session_state.analytics_session_id

    def _get_user_location(self):
        """Cache the IP-derived location in session to avoid hitting
        third-party services on every rerun."""
        if "analytics_user_location" in st.session_state:
            return st.session_state.analytics_user_location

        import requests
        services = [
            ("ipinfo", "https://ipinfo.io/json", "country", "city"),
            ("ipapi", "http://ip-api.com/json/", "country", "city"),
            ("ipwhois", "https://ipwhois.app/json/", "country", "city"),
            ("ipapi_co", "https://ipapi.co/json/", "country_name", "city"),
        ]
        for name, url, ck, cityk in services:
            try:
                r = requests.get(url, timeout=3)
                if r.status_code != 200:
                    continue
                data = r.json()
                if data.get("error") or data.get("status") == "fail":
                    continue
                country = data.get(ck) or "Unknown"
                city = data.get(cityk) or "Unknown"
                if country != "Unknown":
                    st.session_state.analytics_user_location = (country, city)
                    return country, city
            except Exception:
                continue

        st.session_state.analytics_user_location = ("Unknown", "Unknown")
        return "Unknown", "Unknown"

    # --- Tracking entry points ---------------------------------------------

    def track_visit(self):
        if not self.enabled or not self.sheet:
            return
        if st.session_state.get("visit_tracked"):
            return
        try:
            ws = self.sheet.worksheet("Visits")
            session_id = self._get_session_id()
            country, city = self._get_user_location()
            ws.append_row([datetime.now().isoformat(), session_id, country, city])
            st.session_state.visit_tracked = True
        except Exception:
            pass

    def track_data_source_usage(self, data_source, parameters, locations_count, date_range):
        if not self.enabled or not self.sheet:
            return
        try:
            ws = self.sheet.worksheet("Data_Sources")
            ws.append_row([
                datetime.now().isoformat(),
                self._get_session_id(),
                data_source,
                ", ".join(parameters) if isinstance(parameters, list) else str(parameters),
                locations_count,
                date_range,
            ])
        except Exception:
            pass

    def track_download(self, data_source, export_format, rows_count, locations_count):
        if not self.enabled or not self.sheet:
            return
        try:
            ws = self.sheet.worksheet("Downloads")
            ws.append_row([
                datetime.now().isoformat(),
                self._get_session_id(),
                data_source,
                export_format,
                rows_count,
                locations_count,
            ])
        except Exception:
            pass

    def get_stats_summary(self):
        if not self.enabled or not self.sheet:
            return None
        try:
            visits = self.sheet.worksheet("Visits").get_all_records()
            sources = self.sheet.worksheet("Data_Sources").get_all_records()
            downloads = self.sheet.worksheet("Downloads").get_all_records()
            return {
                "total_visits": len(visits),
                "total_data_fetches": len(sources),
                "total_downloads": len(downloads),
                "visits_df": pd.DataFrame(visits),
                "sources_df": pd.DataFrame(sources),
                "downloads_df": pd.DataFrame(downloads),
            }
        except Exception:
            return None


# --- Public initializer -------------------------------------------------------

def _load_analytics_credentials():
    """Prefer a dedicated `analytics_credentials` secret. Fall back to
    `gee_credentials` only if explicitly allowed. Otherwise return None.
    """
    # 1) Dedicated analytics credentials in Streamlit secrets
    try:
        if hasattr(st, "secrets") and "analytics_credentials" in st.secrets:
            return dict(st.secrets["analytics_credentials"])
    except Exception:
        pass

    # 2) Local file fallback for dev
    if os.path.exists("analytics_credentials.json"):
        try:
            with open("analytics_credentials.json", "r") as f:
                return json.load(f)
        except Exception:
            pass

    # 3) Optionally reuse GEE creds for analytics (off by default)
    if _allow_gee_fallback():
        try:
            if hasattr(st, "secrets") and "gee_credentials" in st.secrets:
                return dict(st.secrets["gee_credentials"])
        except Exception:
            pass
        if os.path.exists("ee_credentials.json"):
            try:
                with open("ee_credentials.json", "r") as f:
                    return json.load(f)
            except Exception:
                pass

    return None


def init_analytics():
    """Initialize analytics. Returns a disabled Analytics() if anything is
    missing — the rest of the app never has to branch on this.
    """
    try:
        sheet_id = _get_sheet_id()
        creds = _load_analytics_credentials() if sheet_id else None
        return Analytics(credentials_dict=creds, sheet_id=sheet_id)
    except Exception:
        return Analytics()
