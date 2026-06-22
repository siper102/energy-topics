import logging
from datetime import datetime
import pandas as pd
import requests
import os
from data.energy_data_provider import LoadProvider

logger = logging.getLogger(__name__)


class ForecastLoadDataProvider(LoadProvider):
    """
    Provides load predictions by fetching temperature forecasts and
    querying the ML service.
    """

    def __init__(self, lat: float, lon: float, ml_service_url: str = None):
        self.lat = lat
        self.lon = lon
        self.ml_service_url = ml_service_url or os.getenv(
            "ML_SERVICE_URL", "http://ml_service:8002"
        )

    def fetch_data(
        self, start_time: datetime, end_time: datetime, resolution_minutes: int
    ) -> pd.DataFrame:
        """
        Main interface to fetch load data. Uses ML service for predictions.
        """
        # 1. Fetch Temperature Forecasts
        df_weather = self._fetch_temperature_forecast(start_time, end_time)

        # 2. Prepare Feature Matrix for ML Service
        # The ML model expects [temp_c, hour, dayofweek, month]
        features = []
        for idx, row in df_weather.iterrows():
            features.append(
                [
                    float(row["temp_c"]),
                    float(idx.hour),
                    float(idx.dayofweek),
                    float(idx.month),
                ]
            )

        # 3. Request Predictions from ML Service
        try:
            # We call the consolidated BentoML 'predict' endpoint
            response = requests.post(
                f"{self.ml_service_url}/predict",
                json={"features_list": features},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            predictions = data["forecasts"]
        except Exception as e:
            raise RuntimeError(f"ML Service prediction failed: {str(e)}")

        # 4. Assemble Resulting DataFrame
        df_weather["load_kw"] = predictions

        # 5. Final Resampling and Filtering
        freq = f"{resolution_minutes}min"
        df_result = df_weather[["load_kw"]].resample(freq).interpolate(method="linear")

        return df_result.loc[start_time:end_time].round(3)

    def _fetch_temperature_forecast(
        self, start_time: datetime, end_time: datetime
    ) -> pd.DataFrame:
        """
        Private helper to fetch temperature data from Open-Meteo.
        Automatically switches between Forecast and Archive APIs based on dates.
        """
        now = datetime.now()
        # If the start_time is more than 14 days ago, we must use the Archive API
        use_archive = (now - start_time).days > 14

        if use_archive:
            url = "https://archive-api.open-meteo.com/v1/archive"
        else:
            url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "hourly": "temperature_2m",
            "timezone": "UTC",
            "start_date": start_time.strftime("%Y-%m-%d"),
            "end_date": end_time.strftime("%Y-%m-%d"),
        }

        try:
            logger.info(
                f"📡 Fetching temperature from {url} ({start_time.date()} to {end_time.date()})..."
            )
            response = requests.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            res_data = response.json()
            hourly = res_data["hourly"]

            df = pd.DataFrame(
                {
                    "time": pd.to_datetime(hourly["time"]),
                    "temp_c": hourly["temperature_2m"],
                }
            )
            df.set_index("time", inplace=True)
            return df
        except Exception as e:
            raise RuntimeError(
                f"Weather data fetch failed ({'Archive' if use_archive else 'Forecast'}): {str(e)}"
            )
