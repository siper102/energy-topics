import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from data.forecast_load_provider import ForecastLoadDataProvider
from data.open_meteo_solar_provider import OpenMeteoSolarProvider
from data.entsoe_e_data_provider import ENTSOEPriceProvider
from data.energy_data_provider import LoadProvider, SolarProvider, PriceProvider

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml_service:5000")

class SensorExtractPipeline:
    """
    Pure data extraction pipeline. 
    Fetches and merges data from load, solar, and price providers into a single DataFrame.
    """
    def __init__(
        self, 
        load_provider: LoadProvider,
        solar_provider: SolarProvider,
        price_provider: PriceProvider
    ):
        self.load_provider = load_provider
        self.solar_provider = solar_provider
        self.price_provider = price_provider

    def extract(self, start_time: datetime, end_time: datetime, res_minutes: int = 60) -> pd.DataFrame:
        """Extracts data from all three providers and merges them into a DataFrame."""
        logger.info(f"Extracting data from {start_time} to {end_time}...")
        try:
            # 1. Fetch from individual providers
            # df_load contains ['load_kw', 'temp_c']
            df_load = self.load_provider.fetch_data(start_time, end_time, res_minutes)
            
            # df_solar contains ['solar_kw', 'temp_c']
            df_solar = self.solar_provider.fetch_data(start_time, end_time, res_minutes)
            
            # df_price contains ['price_buy', 'price_sell']
            df_price = self.price_provider.fetch_data(start_time, end_time, res_minutes)

            # 2. Handle redundant columns (temp_c is provided by both Load and Solar)
            # We keep the one from the Load provider as the primary source
            if 'temp_c' in df_solar.columns:
                df_solar = df_solar.drop(columns=['temp_c'])

            # 3. Merge all data on the time index
            # df_combined will now have: ['load_kw', 'temp_c', 'solar_kw', 'price_buy', 'price_sell']
            df_combined = df_load.join([df_solar, df_price], how='inner')
            
            logger.info(f"Extracted and merged {len(df_combined)} records. Columns: {list(df_combined.columns)}")
            return df_combined
            
        except Exception as e:
            logger.error(f"Failed to extract and merge data: {e}")
            raise

# ==========================================
# EXECUTION BLOCK (FOR TESTING)
# ==========================================
if __name__ == "__main__":
    load_dotenv()
    
    API_KEY = os.getenv("ENTSOE_API_KEY")
    if not API_KEY:
        logger.error("ENTSOE_API_KEY not found. Please set it in your .env file.")
        exit(1)
    
    pipeline = SensorExtractPipeline(
        load_provider=ForecastLoadDataProvider(lat=51.26, lon=6.84, ml_service_url=ML_SERVICE_URL),
        solar_provider=OpenMeteoSolarProvider(lat=51.26, lon=6.84, peak_power_kw=5.0),
        price_provider=ENTSOEPriceProvider(API_KEY)
    )
    
    start = datetime(2025, 6, 1)
    end = datetime(2025, 6, 2)
    
    data = pipeline.extract(start, end, res_minutes=60)
    print("--- Extracted Data Preview ---")
    print(data.head())
