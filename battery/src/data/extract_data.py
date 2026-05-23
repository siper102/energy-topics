import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import psycopg
import pandas as pd
from mock_energy_data_provider import MockLoadProvider
from open_meteo_solar_provider import OpenMeteoSolarProvider
from entsoe_e_data_provider import ENTSOEPriceProvider
from energy_data_provider import LoadProvider, SolarProvider, PriceProvider

# 1. Setup Professional Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SensorETLPipeline:
    def __init__(
        self, 
        db_dsn: str, 
        load_provider: LoadProvider,
        solar_provider: SolarProvider,
        price_provider: PriceProvider
    ):
        self.db_dsn = db_dsn
        self.load_provider = load_provider
        self.solar_provider = solar_provider
        self.price_provider = price_provider

    def extract(self, start_time: datetime, end_time: datetime, res_minutes: int = 60) -> pd.DataFrame:
        """Extracts data from all three providers and merges them."""
        logger.info(f"Extracting data from {start_time} to {end_time}...")
        try:
            # 1. Fetch from individual providers
            df_load = self.load_provider.fetch_data(start_time, end_time, res_minutes)
            df_solar = self.solar_provider.fetch_data(start_time, end_time, res_minutes)
            df_price = self.price_provider.fetch_data(start_time, end_time, res_minutes)
            
            # 2. Merge all data on the time index
            # We use an inner join to ensure we only have complete records
            df_combined = df_load.join([df_solar, df_price], how='inner')
            
            logger.info(f"Extracted and merged {len(df_combined)} records.")
            return df_combined
            
        except Exception as e:
            logger.error(f"Failed to extract and merge data: {e}")
            raise

    def load(self, df: pd.DataFrame, table_name: str = "sensor_telemetry"):
        """Loads data into TimescaleDB using ultra-fast COPY."""
        if df.empty:
            logger.warning("DataFrame is empty. Nothing to load.")
            return

        logger.info(f"Loading {len(df)} rows into {table_name}...")
        
        df_reset = df.reset_index()
        df_reset.rename(columns={'index': 'time'}, inplace=True)
        
        # Match schema: time, load_kw, solar_kw, price_buy_usd_per_kwh, price_sell_usd_per_kwh
        df_db_ready = df_reset[['time', 'load_kw', 'solar_kw', 'price_buy', 'price_sell']].rename(
            columns={
                'price_buy': 'price_buy_usd_per_kwh',
                'price_sell': 'price_sell_usd_per_kwh'
            }
        )
        
        records = df_db_ready.values.tolist()

        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    columns_str = ", ".join(df_db_ready.columns)
                    copy_query = f"COPY {table_name} ({columns_str}) FROM STDIN"
                    
                    with cur.copy(copy_query) as copy:
                        for row in records:
                            copy.write_row(row)
                    
                    conn.commit()
            logger.info("Load complete! ✅")
            
        except psycopg.Error as e:
            logger.error(f"Database error during load: {e}")
            raise

# ==========================================
# EXECUTION BLOCK
# ==========================================
if __name__ == "__main__":
    load_dotenv()
    
    DB_DSN = os.getenv(
        "DB_DSN", 
        "postgresql://postgres:postgres@localhost:5432/battery"
    )
    API_KEY = os.getenv("ENTSOE_API_KEY")
    
    if not API_KEY:
        logger.error("ENTSOE_API_KEY not found. Please set it in your .env file.")
        exit(1)
    
    # 2. Select your providers here (The core request: DECAPPING!)
    # We can now mix and match easily
    load_p = MockLoadProvider()
    solar_p = OpenMeteoSolarProvider(
        lat=51.26, 
        lon=6.84, 
        peak_power_kw=0.5, 
        tilt=35, 
        azimuth=0
    )
    price_p = ENTSOEPriceProvider(API_KEY) 
    
    pipeline = SensorETLPipeline(
        db_dsn=DB_DSN,
        load_provider=load_p,
        solar_provider=solar_p,
        price_provider=price_p
    )
    
    # Define time window
    start = datetime(2025, 2, 1)
    end = datetime(2025, 2, 5)
    
    # Run the Pipeline
    data = pipeline.extract(start, end, res_minutes=60)
    pipeline.load(data, table_name="sensor_telemetry")
