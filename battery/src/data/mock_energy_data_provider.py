import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from energy_data_provider import EnergyDataProvider

class MockEnergyDataProvider(EnergyDataProvider):
    """
    Generates synthetic but somewhat realistic energy data for testing.
    - Solar: Bell curve during the day, 0 at night.
    - Load: Base load with an evening peak.
    - Prices: Fixed Time-of-Use (ToU) tariffs.
    """
    
    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int = 60) -> pd.DataFrame:
        # 1. Create the time index based on the requested window
        freq = f'{resolution_minutes}min'
        time_index = pd.date_range(start=start_time, end=end_time, freq=freq)
        n_periods = len(time_index)
        
        # Initialize DataFrame
        df = pd.DataFrame(index=time_index)
        hour_of_day = df.index.hour
        
        # 2. Generate Mock Solar (Sine wave from 6 AM to 6 PM + random cloud noise)
        # Using np.pi to create a nice curve that hits 0 at 6 and 18
        solar_curve = np.where(
            (hour_of_day >= 6) & (hour_of_day <= 18),
            np.sin(np.pi * (hour_of_day - 6) / 12) * 5.0, # Max 5 kW solar peak
            0.0
        )
        # Add random noise and ensure it doesn't drop below 0
        df['solar_kw'] = np.clip(solar_curve + np.random.normal(0, 0.5, n_periods), 0, None)
        
        # 3. Generate Mock Load (Higher in the evening + random activity noise)
        # Base load of 1.0 kW, bumps up to 4.0 kW between 5 PM and 10 PM
        load_curve = np.where((hour_of_day >= 17) & (hour_of_day <= 22), 4.0, 1.0)
        df['load_kw'] = np.clip(load_curve + np.random.normal(0, 0.4, n_periods), 0.2, None)
        
        # 4. Generate Mock Prices (Time of Use Tariffs)
        # Expensive ($0.35) during evening peak, cheap ($0.15) otherwise
        df['price_usd_per_kwh'] = np.where((hour_of_day >= 17) & (hour_of_day <= 21), 0.35, 0.15)
        
        # Round the values to make them look cleaner
        return df.round(3)

if __name__ == "__main__":
    # In your ETL pipeline, you just instantiate the specific provider you want to use
    provider: EnergyDataProvider = MockEnergyDataProvider()
    
    # Define your time window
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    
    # Fetch the data!
    simulated_data = provider.fetch_data(
        start_time=start, 
        end_time=end, 
        resolution_minutes=60  # Hourly data
    )
    
    print(simulated_data.head(24))