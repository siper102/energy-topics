import os
import sys
from datetime import datetime
import pandas as pd

# Add core_api/src to path to reuse providers
sys.path.append(os.path.join(os.getcwd(), "core_api", "src"))

from data.open_meteo_solar_provider import OpenMeteoSolarProvider
from model.data_generator import DataGenerator

def run_data_pipeline(output_path: str = "ml_service/data/training_data.parquet"):
    """
    1. Fetches historical weather (Solar + Temp)
    2. Generates synthetic load
    3. Adds temporal features
    4. Saves to Parquet
    """
    print("🚀 Starting Data Pipeline for ML...")
    
    # Configuration
    lat, lon = 51.26, 6.84
    peak_power = 5.0
    start = datetime(2023, 1, 1)
    end = datetime(2024, 12, 31)
    
    # 1. Fetch Weather
    weather_p = OpenMeteoSolarProvider(lat, lon, peak_power)
    print(f"📡 Fetching weather data from {start.date()} to {end.date()}...")
    df = weather_p.fetch_data(start, end)
    
    # 2. Generate Load
    print("🧠 Generating synthetic realistic load...")
    gen = DataGenerator()
    df['load_kw'] = gen.generate_realistic_load(df)
    
    # 3. Add temporal features for the DNN
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.dayofweek
    df['month'] = df.index.month
    
    # 4. Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path)
    print(f"✅ Data Pipeline complete. Saved to {output_path}")

if __name__ == "__main__":
    run_data_pipeline()
