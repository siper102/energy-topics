from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd

class EnergyDataProvider(ABC):
    """
    Abstract interface for fetching time-series energy data.
    Any future data source (CSV, API, Database) must implement this interface.
    """
    
    @abstractmethod
    def fetch_data(
        self, 
        start_time: datetime, 
        end_time: datetime, 
        resolution_minutes: int
    ) -> pd.DataFrame:
        """
        Fetches or generates energy data for a given time window.
        
        Returns a Pandas DataFrame with the following columns:
        - load_kw (float)
        - solar_kw (float)
        - price_usd_per_kwh (float)
        """
        pass