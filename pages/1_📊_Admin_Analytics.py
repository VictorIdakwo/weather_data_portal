"""
Admin Analytics Dashboard
Password-protected analytics dashboard for Weather Data Portal
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.analytics import init_analytics

# Page configuration
st.set_page_config(
    page_title="Admin Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

# Password protection
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Get admin password from secrets, fallback to default for local dev
        try:
            admin_pwd = st.secrets.get("admin_password", "admin123")
        except Exception:
            # If secrets file doesn't exist, use default
            admin_pwd = "admin123"
        
        if st.session_state["password"] == admin_pwd:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct
        return True


# Main app
def main():
    st.title("📊 Weather Data Portal - Analytics Dashboard")
    st.markdown("---")
    
    # Initialize analytics
    analytics = init_analytics()
    
    if not analytics.enabled:
        st.error("❌ Analytics not enabled. Please configure Google Sheets credentials.")
        st.info("Add the same Google service account credentials to Streamlit secrets.")
        return
    
    # Get analytics data
    with st.spinner("Loading analytics data..."):
        stats = analytics.get_stats_summary()
    
    if not stats:
        st.warning("⚠️ No analytics data available yet.")
        return
    
    # Display summary metrics
    st.header("📈 Summary Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Visits",
            value=stats['total_visits'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Data Fetches",
            value=stats['total_data_fetches'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="Downloads",
            value=stats['total_downloads'],
            delta=None
        )
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Overview", "🌍 Data Sources", "⬇️ Downloads", "📊 Raw Data"])
    
    with tab1:
        st.subheader("Visits Over Time")
        
        if not stats['visits_df'].empty:
            visits_df = stats['visits_df'].copy()
            visits_df['Date'] = pd.to_datetime(visits_df['Timestamp']).dt.date
            
            # Group by date
            daily_visits = visits_df.groupby('Date').size().reset_index(name='Visits')
            
            fig = px.line(
                daily_visits, 
                x='Date', 
                y='Visits',
                title='Daily Visits',
                labels={'Visits': 'Number of Visits', 'Date': 'Date'}
            )
            fig.update_traces(mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent visits table
            st.subheader("Recent Visits")
            recent_visits = visits_df.sort_values('Timestamp', ascending=False).head(20).copy()
            # Convert Session_ID to string to avoid overflow errors
            if 'Session_ID' in recent_visits.columns:
                recent_visits['Session_ID'] = recent_visits['Session_ID'].astype(str)
            st.dataframe(recent_visits, use_container_width=True)
        else:
            st.info("No visit data yet.")
    
    with tab2:
        st.subheader("Data Source Usage")
        
        if not stats['sources_df'].empty:
            sources_df = stats['sources_df'].copy()
            
            # Data source distribution
            source_counts = sources_df['Data_Source'].value_counts().reset_index()
            source_counts.columns = ['Data Source', 'Count']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    source_counts,
                    values='Count',
                    names='Data Source',
                    title='Data Source Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    source_counts,
                    x='Data Source',
                    y='Count',
                    title='Data Source Usage Count'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Usage over time
            sources_df['Date'] = pd.to_datetime(sources_df['Timestamp']).dt.date
            daily_usage = sources_df.groupby(['Date', 'Data_Source']).size().reset_index(name='Count')
            
            fig = px.line(
                daily_usage,
                x='Date',
                y='Count',
                color='Data_Source',
                title='Data Source Usage Over Time'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Popular parameters
            st.subheader("Popular Parameters")
            if 'Parameters' in sources_df.columns:
                all_params = []
                for params in sources_df['Parameters'].dropna():
                    all_params.extend([p.strip() for p in str(params).split(',')])
                
                if all_params:
                    param_counts = pd.Series(all_params).value_counts().head(10)
                    st.bar_chart(param_counts)
            
            # Recent data fetches
            st.subheader("Recent Data Fetches")
            recent_fetches = sources_df.sort_values('Timestamp', ascending=False).head(20).copy()
            # Convert Session_ID to string to avoid overflow errors
            if 'Session_ID' in recent_fetches.columns:
                recent_fetches['Session_ID'] = recent_fetches['Session_ID'].astype(str)
            st.dataframe(recent_fetches, use_container_width=True)
        else:
            st.info("No data source usage yet.")
    
    with tab3:
        st.subheader("Download Statistics")
        
        if not stats['downloads_df'].empty:
            downloads_df = stats['downloads_df'].copy()
            
            # Export format distribution
            format_counts = downloads_df['Format'].value_counts().reset_index()
            format_counts.columns = ['Format', 'Count']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    format_counts,
                    values='Count',
                    names='Format',
                    title='Export Format Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Downloads by data source
                source_downloads = downloads_df['Data_Source'].value_counts().reset_index()
                source_downloads.columns = ['Data Source', 'Count']
                
                fig = px.bar(
                    source_downloads,
                    x='Data Source',
                    y='Count',
                    title='Downloads by Data Source'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Downloads over time
            downloads_df['Date'] = pd.to_datetime(downloads_df['Timestamp']).dt.date
            daily_downloads = downloads_df.groupby('Date').size().reset_index(name='Downloads')
            
            fig = px.line(
                daily_downloads,
                x='Date',
                y='Downloads',
                title='Downloads Over Time'
            )
            fig.update_traces(mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)
            
            # Total rows downloaded
            if 'Rows_Count' in downloads_df.columns:
                total_rows = downloads_df['Rows_Count'].sum()
                st.metric("Total Rows Downloaded", f"{total_rows:,}")
            
            # Recent downloads
            st.subheader("Recent Downloads")
            recent_downloads = downloads_df.sort_values('Timestamp', ascending=False).head(20).copy()
            # Convert Session_ID to string to avoid overflow errors
            if 'Session_ID' in recent_downloads.columns:
                recent_downloads['Session_ID'] = recent_downloads['Session_ID'].astype(str)
            st.dataframe(recent_downloads, use_container_width=True)
        else:
            st.info("No downloads yet.")
    
    with tab4:
        st.subheader("Raw Analytics Data")
        
        # Prepare dataframes with Session_ID as string
        visits_raw = stats['visits_df'].copy()
        if 'Session_ID' in visits_raw.columns:
            visits_raw['Session_ID'] = visits_raw['Session_ID'].astype(str)
        
        sources_raw = stats['sources_df'].copy()
        if 'Session_ID' in sources_raw.columns:
            sources_raw['Session_ID'] = sources_raw['Session_ID'].astype(str)
        
        downloads_raw = stats['downloads_df'].copy()
        if 'Session_ID' in downloads_raw.columns:
            downloads_raw['Session_ID'] = downloads_raw['Session_ID'].astype(str)
        
        st.write("**Visits Data**")
        st.dataframe(visits_raw, use_container_width=True)
        
        st.write("**Data Source Usage**")
        st.dataframe(sources_raw, use_container_width=True)
        
        st.write("**Downloads Data**")
        st.dataframe(downloads_raw, use_container_width=True)
        
        # Export option
        if st.button("📥 Export All Analytics Data"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(f'analytics_export_{timestamp}.xlsx', engine='openpyxl') as writer:
                stats['visits_df'].to_excel(writer, sheet_name='Visits', index=False)
                stats['sources_df'].to_excel(writer, sheet_name='Data Sources', index=False)
                stats['downloads_df'].to_excel(writer, sheet_name='Downloads', index=False)
            
            st.success(f"✅ Analytics exported to analytics_export_{timestamp}.xlsx")


# Run the app
if check_password():
    main()
else:
    st.info("👆 Please enter the admin password to access the analytics dashboard.")
