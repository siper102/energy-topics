from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd

class EnergyDataProvider(ABC):
    """
    Abstract interface for fetching time-series energy data.
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
        
        Returns a Pandas DataFrame indexed by time.
        """
        pass

class LoadProvider(EnergyDataProvider):
    """Specific interface for Load data (load_kw)."""
    @abstractmethod
    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int) -> pd.DataFrame:
        """Should return a DataFrame with column 'load_kw'."""
        pass

class SolarProvider(EnergyDataProvider):
    """Specific interface for Solar data (solar_kw)."""
    @abstractmethod
    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int) -> pd.DataFrame:
        """Should return a DataFrame with column 'solar_kw'."""
        pass

class PriceProvider(EnergyDataProvider):
    """Specific interface for Price data (price_buy, price_sell)."""
    @abstractmethod
    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int) -> pd.DataFrame:
        """Should return a DataFrame with columns 'price_buy' and 'price_sell'."""
        pass
