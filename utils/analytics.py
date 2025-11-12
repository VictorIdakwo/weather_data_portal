"""
Analytics tracking module for Weather Data Portal
Tracks page visits, data source usage, and downloads
"""

import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json


class Analytics:
    """Analytics tracker using Google Sheets as backend"""
    
    def __init__(self, credentials_dict=None):
        """
        Initialize analytics with Google Sheets credentials
        
        Args:
            credentials_dict: Google service account credentials
        """
        self.client = None
        self.sheet = None
        self.enabled = False
        
        if credentials_dict:
            try:
                self._initialize_sheets(credentials_dict)
                self.enabled = True
            except Exception as e:
                # Silently fail if analytics can't be initialized
                pass
        else:
            pass
    
    def _initialize_sheets(self, credentials_dict):
        """Initialize Google Sheets client"""
        # Define the scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Create credentials
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )
        
        # Authorize the client
        self.client = gspread.authorize(credentials)
        
        # Try to get the analytics spreadsheet
        # First try by sheet ID if available (for organizational accounts)
        sheet_id = "1m9fnG-kLaYPGLsq3jFf_yEoJhOMCETesP4r-DeROezE"
        try:
            self.sheet = self.client.open_by_key(sheet_id)
        except Exception as e1:
            # Try by name as fallback
            try:
                self.sheet = self.client.open("Weather_Portal_Analytics")
            except gspread.exceptions.SpreadsheetNotFound:
                # Last resort: try to create new spreadsheet
                self.sheet = self.client.create("Weather_Portal_Analytics")
                self.sheet.share('', perm_type='anyone', role='reader')
                self._setup_worksheets()
    
    def _setup_worksheets(self):
        """Setup the analytics worksheets"""
        if not self.sheet:
            return
        
        # Create worksheets for different metrics
        worksheets = {
            'Visits': ['Timestamp', 'Session_ID', 'User_Country', 'User_City'],
            'Data_Sources': ['Timestamp', 'Session_ID', 'Data_Source', 'Parameters', 'Locations_Count', 'Date_Range'],
            'Downloads': ['Timestamp', 'Session_ID', 'Data_Source', 'Format', 'Rows_Count', 'Locations_Count']
        }
        
        for sheet_name, headers in worksheets.items():
            try:
                worksheet = self.sheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.sheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
                worksheet.append_row(headers)
    
    def _get_session_id(self):
        """Get or create a unique session ID"""
        if 'analytics_session_id' not in st.session_state:
            st.session_state.analytics_session_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return st.session_state.analytics_session_id
    
    def _get_user_location(self):
        """Try to get user's location using IP geolocation with multiple fallbacks and accuracy checks"""
        import requests
        
        # Try multiple services with different strengths
        services = [
            {
                'name': 'ipinfo',
                'url': 'https://ipinfo.io/json',
                'country_key': 'country',
                'city_key': 'city',
                'priority': 1  # Most accurate for general use
            },
            {
                'name': 'ipapi',
                'url': 'http://ip-api.com/json/',
                'country_key': 'country',
                'city_key': 'city', 
                'priority': 2  # Good accuracy, shows ISP info
            },
            {
                'name': 'ipwhois',
                'url': 'https://ipwhois.app/json/',
                'country_key': 'country',
                'city_key': 'city',
                'priority': 3
            },
            {
                'name': 'ipapi_co',
                'url': 'https://ipapi.co/json/',
                'country_key': 'country_name',
                'city_key': 'city',
                'priority': 4
            }
        ]
        
        results = []
        
        # Try all services and collect results
        for service in services:
            try:
                response = requests.get(service['url'], timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    # Check if response has error
                    if data.get('error') or data.get('status') == 'fail':
                        continue
                    
                    country = data.get(service['country_key'], 'Unknown')
                    city = data.get(service['city_key'], 'Unknown')
                    
                    if country and country != 'Unknown':
                        results.append({
                            'service': service['name'],
                            'country': country,
                            'city': city,
                            'priority': service['priority'],
                            'data': data  # Keep full response for debugging
                        })
                        
                        # If we get a high-priority accurate result, use it
                        if service['priority'] <= 2:
                            # Add some validation for known accurate services
                            if service['name'] == 'ipinfo' or service['name'] == 'ipapi':
                                return country, city
            
            except Exception as e:
                # Try next service
                continue
        
        # If we have multiple results, try to pick the most consistent one
        if results:
            # Sort by priority (lower number = higher priority)
            results.sort(key=lambda x: x['priority'])
            
            # Use the highest priority result
            best_result = results[0]
            
            # Debug info for tracking location detection issues
            if len(results) > 1:
                # Log discrepancies for analysis (only in debug mode)
                countries = [r['country'] for r in results]
                if len(set(countries)) > 1:
                    # Multiple different countries detected - this indicates potential issues
                    service_countries = [f"{r['service']}:{r['country']}" for r in results[:3]]
                    debug_info = f"Location mismatch: {', '.join(service_countries)}"
                    # Store in session state for potential display in debug mode
                    if 'location_debug' not in st.session_state:
                        st.session_state.location_debug = []
                    st.session_state.location_debug.append(debug_info)
            
            return best_result['country'], best_result['city']
        
        return "Unknown", "Unknown"
    
    def debug_location_detection(self):
        """
        Debug function to test location detection and show results from all services
        Returns detailed results for troubleshooting
        """
        import requests
        
        services = [
            {
                'name': 'ipinfo',
                'url': 'https://ipinfo.io/json',
                'country_key': 'country',
                'city_key': 'city'
            },
            {
                'name': 'ipapi',
                'url': 'http://ip-api.com/json/',
                'country_key': 'country',
                'city_key': 'city'
            },
            {
                'name': 'ipwhois',
                'url': 'https://ipwhois.app/json/',
                'country_key': 'country',
                'city_key': 'city'
            },
            {
                'name': 'ipapi_co',
                'url': 'https://ipapi.co/json/',
                'country_key': 'country_name',
                'city_key': 'city'
            }
        ]
        
        results = {}
        
        for service in services:
            try:
                response = requests.get(service['url'], timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    country = data.get(service['country_key'], 'Unknown')
                    city = data.get(service['city_key'], 'Unknown')
                    
                    results[service['name']] = {
                        'success': True,
                        'country': country,
                        'city': city,
                        'ip': data.get('ip', data.get('query', 'Unknown')),
                        'isp': data.get('isp', data.get('org', 'Unknown')),
                        'full_data': data
                    }
                else:
                    results[service['name']] = {
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    }
            except Exception as e:
                results[service['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def track_visit(self):
        """Track a page visit"""
        if not self.enabled or not self.sheet:
            return
        
        try:
            worksheet = self.sheet.worksheet('Visits')
            session_id = self._get_session_id()
            country, city = self._get_user_location()
            
            # Only track once per session
            if 'visit_tracked' not in st.session_state:
                worksheet.append_row([
                    datetime.now().isoformat(),
                    session_id,
                    country,
                    city
                ])
                st.session_state.visit_tracked = True
        except Exception as e:
            # Silently fail
            pass
    
    def track_data_source_usage(self, data_source, parameters, locations_count, date_range):
        """
        Track data source usage
        
        Args:
            data_source: Name of the data source
            parameters: List of parameters selected
            locations_count: Number of locations
            date_range: Date range string
        """
        if not self.enabled or not self.sheet:
            return
        
        try:
            worksheet = self.sheet.worksheet('Data_Sources')
            session_id = self._get_session_id()
            
            worksheet.append_row([
                datetime.now().isoformat(),
                session_id,
                data_source,
                ', '.join(parameters) if isinstance(parameters, list) else str(parameters),
                locations_count,
                date_range
            ])
        except Exception as e:
            # Silently fail
            pass
    
    def track_download(self, data_source, export_format, rows_count, locations_count):
        """
        Track data download
        
        Args:
            data_source: Name of the data source
            export_format: Export format (CSV, JSON, etc.)
            rows_count: Number of rows in the export
            locations_count: Number of locations
        """
        if not self.enabled or not self.sheet:
            return
        
        try:
            worksheet = self.sheet.worksheet('Downloads')
            session_id = self._get_session_id()
            
            worksheet.append_row([
                datetime.now().isoformat(),
                session_id,
                data_source,
                export_format,
                rows_count,
                locations_count
            ])
        except Exception as e:
            # Silently fail
            pass
    
    def get_stats_summary(self):
        """
        Get analytics summary
        
        Returns:
            dict: Summary statistics
        """
        if not self.enabled or not self.sheet:
            return None
        
        try:
            # Get visits
            visits_ws = self.sheet.worksheet('Visits')
            visits_data = visits_ws.get_all_records()
            
            # Get data source usage
            sources_ws = self.sheet.worksheet('Data_Sources')
            sources_data = sources_ws.get_all_records()
            
            # Get downloads
            downloads_ws = self.sheet.worksheet('Downloads')
            downloads_data = downloads_ws.get_all_records()
            
            return {
                'total_visits': len(visits_data),
                'total_data_fetches': len(sources_data),
                'total_downloads': len(downloads_data),
                'visits_df': pd.DataFrame(visits_data),
                'sources_df': pd.DataFrame(sources_data),
                'downloads_df': pd.DataFrame(downloads_data)
            }
        except Exception as e:
            return None


def init_analytics():
    """
    Initialize analytics from Streamlit secrets or environment
    
    Returns:
        Analytics: Analytics instance
    """
    try:
        # Try to get credentials from Streamlit secrets
        if hasattr(st, 'secrets'):
            if 'gee_credentials' in st.secrets:
                credentials = dict(st.secrets['gee_credentials'])
                return Analytics(credentials)
        
        # Try to load from local file (for development)
        import os
        creds_path = "ee_credentials.json"
        if os.path.exists(creds_path):
            with open(creds_path, 'r') as f:
                credentials = json.load(f)
            return Analytics(credentials)
        
        return Analytics()  # Return disabled analytics
    except Exception as e:
        return Analytics()  # Return disabled analytics
