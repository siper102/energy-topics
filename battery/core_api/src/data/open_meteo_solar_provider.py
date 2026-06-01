from data.energy_data_provider import SolarProvider
from datetime import datetime
import pandas as pd
import requests


class OpenMeteoSolarProvider(SolarProvider):
    """
    Fetches real-time solar forecasts from Open-Meteo.
    Calculates plane-of-array tilted irradiance automatically on the server.
    """
    def __init__(self, lat: float, lon: float, peak_power_kw: float, tilt: float = 35, azimuth: float = 0):
        self.lat = lat
        self.lon = lon
        self.peak_power_kw = peak_power_kw
        self.tilt = tilt
        self.azimuth = azimuth
        # Open-Meteo doesn't require an API key for non-commercial use
        self.url = "https://archive-api.open-meteo.com/v1/archive"

    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int = 60) -> pd.DataFrame:
        # 1. Map parameters to Open-Meteo's format
        # Note: Open-Meteo assumes 0 = South, 90 = West, -90 = East
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "start_date": start_str,
            "end_date": end_str,
            "hourly": "global_tilted_irradiance",
            "tilt": self.tilt,
            "azimuth": self.azimuth,
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
            "gti": hourly["global_tilted_irradiance"] # W/m^2 on your tilted panels
        })
        df.set_index("time", inplace=True)

        # 3. Convert Irradiance to Power (kW)
        # Standard test condition assumes 1000 W/m^2 yields 100% of peak power capacity.
        # We also apply a standard 14% performance loss factor (inverter, cabling, dirt)
        loss_factor = 0.86 
        df["solar_kw"] = (df["gti"] / 1000.0) * self.peak_power_kw * loss_factor
        # 4. Clean up, filter to requested window, and match resolution
        df_final = df[["solar_kw"]].loc[start_time:end_time]
        freq = f"{resolution_minutes}min"

        return df_final.resample(freq).interpolate(method="linear").round(3)

