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
        return self.client.query_day_ahead_prices(
            self.country_code, start=start, end=end
        )

    def fetch_intraday_data(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
        """Fetches raw intraday prices (Intraday Auction)."""
        # For DE/LU, query_intraday_prices requires a 'sequence' argument (typically 1 for IDA1)
        return self.client.query_intraday_prices(
            self.country_code, start=start, end=end, sequence=1
        )

    def fetch_data(
        self, start_time: datetime, end_time: datetime, resolution_minutes: int
    ) -> pd.DataFrame:
        """
        Fetches day-ahead prices and realized intraday prices from ENTSO-E and formats them.
        """
        import logging

        logger = logging.getLogger(__name__)

        # ENTSO-E API expects timezone-aware timestamps.
        start = pd.Timestamp(start_time).tz_localize("UTC")
        end = pd.Timestamp(end_time).tz_localize("UTC")

        # 1. Fetch Day-Ahead (planning) prices
        prices = self.fetch_day_ahead_data(start, end)
        df_da = pd.DataFrame(prices, columns=["price_buy"])
        df_da.index.name = "time"

        # 2. Fetch Intraday (realized) prices
        try:
            id_prices = self.fetch_intraday_data(start, end)
            df_id = pd.DataFrame(id_prices, columns=["realized_price_buy"])
            df_id.index.name = "time"
        except Exception as e:
            logger.warning(
                f"Failed to fetch intraday prices from ENTSO-E: {e}. Falling back to Day-Ahead prices."
            )
            df_id = pd.DataFrame(index=df_da.index)
            df_id["realized_price_buy"] = df_da["price_buy"]

        # 3. Merge DA and ID prices
        df = df_da.join(df_id, how="outer")

        # Fill any gaps
        df["price_buy"] = df["price_buy"].ffill().bfill()
        df["realized_price_buy"] = df["realized_price_buy"].fillna(df["price_buy"])

        # Convert EUR/MWh to USD/kWh
        df["price_buy"] = (df["price_buy"] * 1.05) / 1000.0
        df["price_sell"] = df["price_buy"] * 0.9

        df["realized_price_buy"] = (df["realized_price_buy"] * 1.05) / 1000.0
        df["realized_price_sell"] = df["realized_price_buy"] * 0.9

        # Resample and cleanup
        df = df.resample(f"{resolution_minutes}min").ffill()
        df = df.loc[start:end]
        df.index = df.index.tz_localize(None)

        return df.round(4)
