import pandas as pd
import numpy as np
from datetime import datetime

class MockEnergyDataProvider:
    """
    Generates a larger, more complex synthetic dataset.
    - Diversity: Adds cloudy/sunny day variations.
    - Seasonality: Weekend vs. Weekday load profiles.
    - Scale: Easily handles months of data at high resolution.
    """
    
    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int = 15) -> pd.DataFrame:
        freq = f'{resolution_minutes}min'
        time_index = pd.date_range(start=start_time, end=end_time, freq=freq, inclusive='left')
        n_periods = len(time_index)
        
        df = pd.DataFrame(index=time_index)
        hour_of_day = df.index.hour
        day_of_week = df.index.dayofweek # 0=Monday, 6=Sunday
        # Unique integer for each day to sync weather across the same day
        day_identifier = df.index.dayofyear + (365 * (df.index.year - df.index.year[0]))

        # --- 1. Weather Variation (Solar Multiplier) ---
        # Randomly decide if a day is 'Sunny' (1.0), 'Partly Cloudy' (0.5), or 'Overcast' (0.1)
        np.random.seed(42) # For reproducible "weather"
        daily_weather = np.random.choice([1.0, 0.5, 0.2], size=day_identifier.max() + 1)
        weather_multiplier = daily_weather[day_identifier]

        # --- 2. Solar Generation ---
        solar_base = np.where(
            (hour_of_day >= 6) & (hour_of_day <= 18),
            np.sin(np.pi * (hour_of_day - 6) / 12) * 5.0,
            0.0
        )
        # Apply weather and some high-frequency cloud noise
        df['solar_kw'] = np.clip(
            (solar_base * weather_multiplier) + np.random.normal(0, 0.2, n_periods), 
            0, None
        )

        # --- 3. Demand (Load) ---
        # Weekends (5,6) have higher afternoon load; Weekdays have morning/evening peaks
        is_weekend = (day_of_week >= 5)
        load_curve = np.where(
            is_weekend,
            np.where((hour_of_day >= 10) & (hour_of_day <= 20), 3.5, 1.2), # Weekend: constant high-ish
            np.where((hour_of_day >= 7) & (hour_of_day <= 9) | (hour_of_day >= 17) & (hour_of_day <= 22), 4.5, 0.8) # Weekday peaks
        )
        df['load_kw'] = np.clip(load_curve + np.random.normal(0, 0.5, n_periods), 0.2, None)

        # --- 4. Prices (Buy/Sell) ---
        # Dynamic Buy: Afternoon peak $0.40, Night $0.10, Mid-day $0.20
        df['price_buy'] = 0.15 # Default
        df.loc[(hour_of_day >= 17) & (hour_of_day <= 21), 'price_buy'] = 0.40 # Evening Peak
        df.loc[(hour_of_day >= 1) & (hour_of_day <= 5), 'price_buy'] = 0.10   # Night Valley
        
        # Flat Sell rate
        df['price_sell'] = 0.08
        
        return df.round(3)