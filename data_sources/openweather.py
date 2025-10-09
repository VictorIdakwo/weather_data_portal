import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import os

# Available OpenWeather parameters
OPENWEATHER_PARAMETERS = {
    "Current/Forecast": {
        "temp": "Temperature (°C)",
        "feels_like": "Feels Like Temperature (°C)",
        "humidity": "Humidity (%)",
        "pressure": "Atmospheric Pressure (hPa)",
        "wind_speed": "Wind Speed (m/s)",
        "wind_deg": "Wind Direction (degrees)",
        "clouds": "Cloudiness (%)",
        "rain": "Rain Volume (mm)",
        "snow": "Snow Volume (mm)",
    },
    "Historical": {
        "temp": "Temperature (°C)",
        "feels_like": "Feels Like Temperature (°C)",
        "humidity": "Humidity (%)",
        "pressure": "Atmospheric Pressure (hPa)",
        "wind_speed": "Wind Speed (m/s)",
        "wind_deg": "Wind Direction (degrees)",
        "clouds": "Cloudiness (%)",
        "rain": "Rain Volume (mm)",
    },
}

TEMPORAL_RESOLUTIONS = ["Hourly", "Daily"]


def get_available_parameters() -> Dict[str, Dict[str, str]]:
    """Return available OpenWeather parameters grouped by category."""
    return OPENWEATHER_PARAMETERS


def get_temporal_resolutions() -> List[str]:
    """Return available temporal resolutions for OpenWeather."""
    return TEMPORAL_RESOLUTIONS


def fetch_openweather_data(
    locations: List[Tuple[float, float]],
    parameters: List[str],
    start_date: str,
    end_date: str,
    temporal_resolution: str,
    api_key: str,
) -> pd.DataFrame:
    """
    Fetch data from OpenWeather API for multiple locations.
    Note: Historical data requires a subscription. Free tier only provides current and forecast.
    
    Args:
        locations: List of (latitude, longitude) tuples
        parameters: List of parameter codes to fetch
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        temporal_resolution: 'Hourly' or 'Daily'
        api_key: OpenWeather API key
    
    Returns:
        DataFrame with fetched data
    """
    if not api_key:
        raise ValueError("OpenWeather API key is required")
    
    all_data = []
    
    # Calculate if we're requesting historical data
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    current_dt = datetime.now()
    
    # Check if dates are in the past (historical) or future (forecast)
    is_historical = end_dt < current_dt
    is_forecast = start_dt > current_dt
    
    for idx, (lat, lon) in enumerate(locations):
        try:
            location_data = []
            
            if is_historical:
                # Use One Call API 3.0 for historical data (requires subscription)
                # Note: Free tier users will get an error here
                print(f"⚠️ Attempting to fetch historical data for location {idx}")
                print(f"Note: Historical data requires OpenWeather One Call API 3.0 subscription")
                
                current_date = start_dt
                while current_date <= end_dt:
                    timestamp = int(current_date.timestamp())
                    url = (
                        f"https://api.openweathermap.org/data/3.0/onecall/timemachine?"
                        f"lat={lat}&lon={lon}&dt={timestamp}&appid={api_key}&units=metric"
                    )
                    
                    response = requests.get(url, timeout=30)
                    
                    # Check for subscription errors
                    if response.status_code == 401:
                        raise ValueError("❌ OpenWeather API Key Invalid. Please check your API key.")
                    elif response.status_code == 403:
                        raise ValueError("❌ Historical data requires OpenWeather One Call API 3.0 subscription (paid plan). Free tier only provides current weather + 7-day forecast.")
                    elif response.status_code == 429:
                        raise ValueError("❌ API rate limit exceeded. Please wait and try again.")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Check for error messages in response
                    if "message" in data and response.status_code != 200:
                        raise ValueError(f"OpenWeather API Error: {data['message']}")
                    
                    if "data" in data:
                        for hour_data in data["data"]:
                            record = {
                                "datetime": datetime.fromtimestamp(hour_data["dt"]),
                                "latitude": lat,
                                "longitude": lon,
                                "location_id": idx,
                            }
                            
                            # Extract requested parameters
                            for param in parameters:
                                if param in hour_data:
                                    record[param] = hour_data[param]
                                elif "main" in hour_data and param in hour_data["main"]:
                                    record[param] = hour_data["main"][param]
                                elif "wind" in hour_data and param in hour_data["wind"]:
                                    record[param] = hour_data["wind"][param]
                                elif param == "rain" and "rain" in hour_data:
                                    record[param] = hour_data["rain"].get("1h", 0)
                                elif param == "clouds" and "clouds" in hour_data:
                                    record[param] = hour_data["clouds"]
                            
                            location_data.append(record)
                    
                    current_date += timedelta(days=1)
            
            elif is_forecast:
                # Use One Call API for forecast
                url = (
                    f"https://api.openweathermap.org/data/2.5/onecall?"
                    f"lat={lat}&lon={lon}&appid={api_key}&units=metric"
                )
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Process hourly forecast
                if "hourly" in data and temporal_resolution == "Hourly":
                    for hour_data in data["hourly"]:
                        dt = datetime.fromtimestamp(hour_data["dt"])
                        if start_dt <= dt <= end_dt:
                            record = {
                                "datetime": dt,
                                "latitude": lat,
                                "longitude": lon,
                                "location_id": idx,
                            }
                            
                            for param in parameters:
                                if param in hour_data:
                                    record[param] = hour_data[param]
                                elif param == "rain" and "rain" in hour_data:
                                    record[param] = hour_data["rain"].get("1h", 0)
                            
                            location_data.append(record)
                
                # Process daily forecast
                if "daily" in data and temporal_resolution == "Daily":
                    for day_data in data["daily"]:
                        dt = datetime.fromtimestamp(day_data["dt"])
                        if start_dt <= dt <= end_dt:
                            record = {
                                "datetime": dt,
                                "latitude": lat,
                                "longitude": lon,
                                "location_id": idx,
                            }
                            
                            for param in parameters:
                                if param == "temp" and "temp" in day_data:
                                    record[param] = day_data["temp"].get("day")
                                elif param in day_data:
                                    record[param] = day_data[param]
                                elif param == "rain" and "rain" in day_data:
                                    record[param] = day_data["rain"]
                            
                            location_data.append(record)
            
            else:
                # Current weather
                url = (
                    f"https://api.openweathermap.org/data/2.5/weather?"
                    f"lat={lat}&lon={lon}&appid={api_key}&units=metric"
                )
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                record = {
                    "datetime": datetime.fromtimestamp(data["dt"]),
                    "latitude": lat,
                    "longitude": lon,
                    "location_id": idx,
                }
                
                # Extract requested parameters
                for param in parameters:
                    if "main" in data and param in data["main"]:
                        record[param] = data["main"][param]
                    elif "wind" in data and param in data["wind"]:
                        record[param] = data["wind"][param]
                    elif param == "clouds" and "clouds" in data:
                        record[param] = data["clouds"]["all"]
                    elif param == "rain" and "rain" in data:
                        record[param] = data["rain"].get("1h", 0)
                
                location_data.append(record)
            
            if location_data:
                all_data.extend(location_data)
        
        except Exception as e:
            print(f"Error fetching OpenWeather data for location {idx} ({lat}, {lon}): {str(e)}")
            continue
    
    if all_data:
        df = pd.DataFrame(all_data)
        df = df.sort_values(["location_id", "datetime"]).reset_index(drop=True)
        return df
    else:
        return pd.DataFrame()
