import pandas as pd
import numpy as np
from datetime import datetime
from energy_data_provider import LoadProvider, SolarProvider, PriceProvider

class MockLoadProvider(LoadProvider):
    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int) -> pd.DataFrame:
        freq = f'{resolution_minutes}min'
        time_index = pd.date_range(start=start_time, end=end_time, freq=freq, inclusive='left')
        n_periods = len(time_index)
        
        df = pd.DataFrame(index=time_index)
        hour_of_day = df.index.hour
        day_of_week = df.index.dayofweek
        
        is_weekend = (day_of_week >= 5)
        load_curve = np.where(
            is_weekend,
            np.where((hour_of_day >= 10) & (hour_of_day <= 20), 3.5, 1.2),
            np.where((hour_of_day >= 7) & (hour_of_day <= 9) | (hour_of_day >= 17) & (hour_of_day <= 22), 4.5, 0.8)
        )
        np.random.seed(42)
        df['load_kw'] = np.clip(load_curve + np.random.normal(0, 0.5, n_periods), 0.2, None)
        return df.round(3)

class MockSolarProvider(SolarProvider):
    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int) -> pd.DataFrame:
        freq = f'{resolution_minutes}min'
        time_index = pd.date_range(start=start_time, end=end_time, freq=freq, inclusive='left')
        n_periods = len(time_index)
        
        df = pd.DataFrame(index=time_index)
        hour_of_day = df.index.hour
        day_identifier = df.index.dayofyear + (365 * (df.index.year - df.index.year[0]))

        np.random.seed(42)
        daily_weather = np.random.choice([1.0, 0.5, 0.2], size=day_identifier.max() + 1)
        weather_multiplier = daily_weather[day_identifier]

        solar_base = np.where(
            (hour_of_day >= 6) & (hour_of_day <= 18),
            np.sin(np.pi * (hour_of_day - 6) / 12) * 5.0,
            0.0
        )
        df['solar_kw'] = np.clip(
            (solar_base * weather_multiplier) + np.random.normal(0, 0.2, n_periods), 
            0, None
        )
        return df.round(3)

class MockPriceProvider(PriceProvider):
    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int) -> pd.DataFrame:
        freq = f'{resolution_minutes}min'
        time_index = pd.date_range(start=start_time, end=end_time, freq=freq, inclusive='left')
        
        df = pd.DataFrame(index=time_index)
        hour_of_day = df.index.hour
        
        df['price_buy'] = 0.15
        df.loc[(hour_of_day >= 17) & (hour_of_day <= 21), 'price_buy'] = 0.40
        df.loc[(hour_of_day >= 1) & (hour_of_day <= 5), 'price_buy'] = 0.10
        
        df['price_sell'] = df['price_buy'] - 0.02
        return df.round(3)
