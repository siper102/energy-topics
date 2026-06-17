import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import psycopg
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

    def load(self, df: pd.DataFrame, setup_id: int, table_name: str = "sensor_telemetry"):
        """Loads data into TimescaleDB using ultra-fast COPY with atomic UPSERT."""
        if df.empty:
            logger.warning("DataFrame is empty. Nothing to load.")
            return

        logger.info(f"Loading {len(df)} rows into {table_name} for setup_id {setup_id}...")
        
        df_reset = df.reset_index()
        df_reset.rename(columns={'index': 'time'}, inplace=True)
        df_reset['setup_id'] = setup_id
        
        # Match schema: time, setup_id, load_kw, solar_kw, price_buy_usd_per_kwh, price_sell_usd_per_kwh, temp_c
        df_db_ready = df_reset[['time', 'setup_id', 'load_kw', 'solar_kw', 'price_buy', 'price_sell', 'temp_c']].rename(
            columns={
                'price_buy': 'price_buy_usd_per_kwh',
                'price_sell': 'price_sell_usd_per_kwh'
            }
        )
        
        records = df_db_ready.values.tolist()

        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    # ATOMIC UPSERT STRATEGY: 
                    # Use a temp table to stage data, then INSERT ... ON CONFLICT
                    temp_table = f"temp_{table_name}"
                    cur.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {table_name} INCLUDING ALL) ON COMMIT DROP;")

                    columns_str = ", ".join(df_db_ready.columns)
                    copy_query = f"COPY {temp_table} ({columns_str}) FROM STDIN"
                    
                    with cur.copy(copy_query) as copy:
                        for row in records:
                            copy.write_row(row)
                    
                    # Perform the atomic UPSERT
                    update_cols = [col for col in df_db_ready.columns if col not in ['time', 'setup_id']]
                    set_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])

                    upsert_query = f"""
                        INSERT INTO {table_name} ({columns_str})
                        SELECT {columns_str} FROM {temp_table}
                        ON CONFLICT (time, setup_id) DO UPDATE
                        SET {set_clause};
                    """
                    cur.execute(upsert_query)
                    conn.commit()
            logger.info("Load complete! ✅ (Atomic UPSERT)")
            
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
    load_p = ForecastLoadDataProvider(
        lat=51.26,
        lon=6.84,
        ml_service_url=ML_SERVICE_URL
    )
    solar_p = OpenMeteoSolarProvider(
        lat=51.26, 
        lon=6.84, 
        peak_power_kw=5.0,  # 5.0 kWp is a standard size (approx. 12-15 physical panels)
        tilt=35,            # 30° to 45° is optimal for mid-latitudes to capture sun year-round
        azimuth=0           # MANDATORY for Open-Meteo to face due South!
    )
    price_p = ENTSOEPriceProvider(API_KEY) 
    
    pipeline = SensorETLPipeline(
        db_dsn=DB_DSN,
        load_provider=load_p,
        solar_provider=solar_p,
        price_provider=price_p
    )
    
    # Define time window
    start = datetime(2025, 6, 1)
    end = datetime(2025, 6, 5)
    
    # Run the Pipeline
    data = pipeline.extract(start, end, res_minutes=60)
    pipeline.load(data, table_name="sensor_telemetry")
