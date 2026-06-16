from datetime import datetime
import pandas as pd
import requests

class WeatherProvider:
    """
    Fetches weather data from Open-Meteo.
    Provides temperature time-series.
    """
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon
        # Open-Meteo archive API
        self.url = "https://archive-api.open-meteo.com/v1/archive"

    def fetch_temperature(self, start_time: datetime, end_time: datetime, resolution_minutes: int = 60) -> pd.DataFrame:
        """
        Fetches historical temperature data for the given coordinates and time window.
        Returns a DataFrame with 'temp_c' column, indexed by time.
        """
        # 1. Map parameters to Open-Meteo's format
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "start_date": start_str,
            "end_date": end_str,
            "hourly": "temperature_2m",
            "timezone": "UTC"
        }

        response = requests.get(self.url, params=params)
        if response.status_code != 200:
            raise RuntimeError(f"Open-Meteo API failed: {response.text}")
            
        res_data = response.json()
        hourly = res_data["hourly"]

        # 2. Parse into DataFrame
        df = pd.DataFrame({
            "time": pd.to_datetime(hourly["time"]),
            "temp_c": hourly["temperature_2m"]
        })
        df.set_index("time", inplace=True)
        
        # 3. Filter to requested window and match resolution
        df_final = df.loc[start_time:end_time]
        freq = f"{resolution_minutes}min"

        return df_final.resample(freq).interpolate(method="linear").round(3)
