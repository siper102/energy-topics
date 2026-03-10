import os
import logging
from datetime import datetime, timedelta
import psycopg
import pandas as pd
from mock_energy_data_provider import MockEnergyDataProvider

# 1. Setup Professional Logging (No more print statements!)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SensorETLPipeline:
    def __init__(self, db_dsn: str):
        self.db_dsn = db_dsn
        self.provider = MockEnergyDataProvider()

    def extract(self, start_time: datetime, end_time: datetime, res_minutes: int = 60) -> pd.DataFrame:
        """Extracts data from the provider."""
        logger.info(f"Extracting data from {start_time} to {end_time}...")
        try:
            df = self.provider.fetch_data(start_time, end_time, res_minutes)
            logger.info(f"Extracted {len(df)} records.")
            return df
        except Exception as e:
            logger.error(f"Failed to extract data: {e}")
            raise

    def load(self, df: pd.DataFrame, table_name: str = "sensor_telemetry"):
        """Loads data into TimescaleDB using ultra-fast COPY."""
        if df.empty:
            logger.warning("DataFrame is empty. Nothing to load.")
            return

        logger.info(f"Loading {len(df)} rows into {table_name}...")
        
        df_reset = df.reset_index()
        df_reset.rename(columns={'index': 'time'}, inplace=True)
        
        # 2. Defensively order AND rename columns to perfectly match the Database schema
        # We explicitly map the short Pandas names to the long Postgres names
        df_db_ready = df_reset[['time', 'load_kw', 'solar_kw', 'price_buy', 'price_sell']].rename(
            columns={
                'price_buy': 'price_buy_usd_per_kwh',
                'price_sell': 'price_sell_usd_per_kwh'
            }
        )
        
        # 3. Convert DataFrame to a list of lists for psycopg
        records = df_db_ready.values.tolist()

        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    # 4. DYNAMIC SQL MAGIC: Join the column names with commas
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
    # 2. Use Environment Variables for Secrets (Fallback to local for dev)
    # Notice the DB name is 'gdp_db' from your docker-compose, not 'battery'
    DB_DSN = os.getenv(
        "DB_DSN", 
        "postgresql://postgres:postgres@localhost:5432/battery"
    )
    
    pipeline = SensorETLPipeline(db_dsn=DB_DSN)
    
    # Define time window
    start = datetime(2026, 1, 1)
    end = datetime(2026, 1, 31)
    
    # Run the Pipeline
    data = pipeline.extract(start, end, res_minutes=60)
    pipeline.load(data, table_name="sensor_telemetry")