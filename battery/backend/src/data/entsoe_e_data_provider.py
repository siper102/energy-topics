from entsoe import EntsoePandasClient
import pandas as pd
from datetime import datetime
from data.energy_data_provider import PriceProvider

class ENTSOEPriceProvider(PriceProvider):
    def __init__(self, api_key: str, country_code: str = "DE_LU"):
        self.client = EntsoePandasClient(api_key=api_key)
        self.country_code = country_code

    def fetch_day_ahead_data(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
        """Fetches raw day-ahead prices."""
        return self.client.query_day_ahead_prices(self.country_code, start=start, end=end)

    def fetch_intraday_data(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
        """Fetches raw intraday prices (Intraday Auction)."""
        # For DE/LU, query_intraday_prices requires a 'sequence' argument (typically 1 for IDA1)
        return self.client.query_intraday_prices(self.country_code, start=start, end=end, sequence=1)

    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int) -> pd.DataFrame:
        """
        Fetches day-ahead prices from ENTSO-E and formats them for the pipeline.
        """
        # ENTSO-E API expects timezone-aware timestamps. 
        start = pd.Timestamp(start_time).tz_localize('UTC')
        end = pd.Timestamp(end_time).tz_localize('UTC')

        prices = self.fetch_day_ahead_data(start, end)
        
        # Convert to DataFrame and handle index
        df = pd.DataFrame(prices, columns=['price_buy'])
        df.index.name = 'time'
        
        # Convert EUR/MWh to USD/kWh
        df['price_buy'] = (df['price_buy'] * 1.05) / 1000.0
        df['price_sell'] = df['price_buy'] * 0.9
        
        # Resample and cleanup
        df = df.resample(f'{resolution_minutes}min').ffill()
        df = df.loc[start:end]
        df.index = df.index.tz_localize(None)
        
        return df.round(4)
