from entsoe import EntsoePandasClient
import pandas as pd
from datetime import datetime
from data.energy_data_provider import PriceProvider

class ENTSOEPriceProvider(PriceProvider):
    def __init__(self, api_key: str, country_code: str = "DE_LU"):
        self.client = EntsoePandasClient(api_key=api_key)
        self.country_code = country_code

    def fetch_data(self, start_time: datetime, end_time: datetime, resolution_minutes: int) -> pd.DataFrame:
        """
        Fetches day-ahead prices from ENTSO-E.
        """
        # ENTSO-E API expects timezone-aware timestamps. 
        # We assume input is UTC or we convert to market time.
        start = pd.Timestamp(start_time).tz_localize('UTC')
        end = pd.Timestamp(end_time).tz_localize('UTC')

        prices = self.client.query_day_ahead_prices(self.country_code, start=start, end=end)
        
        # Convert to DataFrame and handle index
        df = pd.DataFrame(prices, columns=['price_buy'])
        df.index.name = 'time'
        
        # In many European markets, prices are in EUR/MWh. 
        # Let's assume we want USD/kWh for our model. 
        # Approx: 1 EUR = 1.05 USD. 1 MWh = 1000 kWh.
        # price_usd_per_kwh = (price_eur_per_mwh * 1.05) / 1000
        df['price_buy'] = (df['price_buy'] * 1.05) / 1000.0
        
        # Add a spread for selling (simplification)
        df['price_sell'] = df['price_buy'] * 0.9
        
        # Resample to the desired resolution if needed
        df = df.resample(f'{resolution_minutes}min').ffill()
        
        # Ensure we only return the requested time window and strip timezone for DB
        df = df.loc[start:end]
        df.index = df.index.tz_localize(None)
        
        return df.round(4)
