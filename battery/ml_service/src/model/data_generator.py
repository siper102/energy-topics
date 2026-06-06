import numpy as np
import pandas as pd
from datetime import datetime

class DataGenerator:
    """
    Generates synthetic load data based on weather and temporal features.
    Logic: Load = Base + Activity(Time) + Thermal(Temp) + Noise
    """
    def __init__(self, base_load: float = 0.5):
        self.base_load = base_load

    def generate_realistic_load(self, df: pd.DataFrame) -> pd.Series:
        """
        Input DF must have 'temp_c' and a DateTime index.
        """
        n = len(df)
        hour = df.index.hour
        dayofweek = df.index.dayofweek
        temp = df['temp_c'].values

        # 1. Activity Pattern (Diurnal)
        # Morning spike (7-9), Evening plateau (17-22)
        activity = np.zeros(n)
        activity += np.where((hour >= 7) & (hour <= 9), 2.0, 0)
        activity += np.where((hour >= 17) & (hour <= 22), 3.0, 0)
        # Baseline activity during day
        activity += np.where((hour > 9) & (hour < 17), 1.0, 0)
        
        # Weekend adjustment (shift load later)
        is_weekend = (dayofweek >= 5)
        activity = np.where(is_weekend, activity * 0.8 + 0.5, activity)

        # 2. Thermal Component
        # Cooling: increases above 22C
        cooling = np.maximum(0, (temp - 22) * 0.4)
        # Heating: increases below 10C
        heating = np.maximum(0, (10 - temp) * 0.3)
        thermal = cooling + heating

        # 3. Autoregressive Noise (AR1)
        # Ensures that load is continuous and not just random spikes
        noise = np.zeros(n)
        epsilon = np.random.normal(0, 0.2, n)
        phi = 0.7 # correlation with previous step
        for i in range(1, n):
            noise[i] = phi * noise[i-1] + epsilon[i]

        load = self.base_load + activity + thermal + noise
        
        # Ensure non-negative
        return pd.Series(np.maximum(0.1, load), index=df.index, name="load_kw")

if __name__ == "__main__":
    # Example usage:
    # df_weather = ... (from OpenMeteo)
    # gen = DataGenerator()
    # df_weather['load_kw'] = gen.generate_realistic_load(df_weather)
    pass
