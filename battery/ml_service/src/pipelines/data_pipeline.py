import os
from datetime import datetime

from external_data.weather_provider import WeatherProvider
from external_data.data_generator import DataGenerator

def run_data_pipeline(output_path: str = "data/training_data.parquet"):
    """
    1. Fetches historical temperature
    2. Generates synthetic load
    3. Adds temporal features
    4. Saves to Parquet
    """
    print("🚀 Starting Data Pipeline for ML...")
    
    # Configuration
    lat, lon = 51.26, 6.84
    start = datetime(2023, 1, 1)
    end = datetime(2024, 12, 31)
    
    # 1. Fetch Temperature
    weather_p = WeatherProvider(lat, lon)
    print(f"📡 Fetching temperature data from {start.date()} to {end.date()}...")
    df = weather_p.fetch_temperature(start, end)
    
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
