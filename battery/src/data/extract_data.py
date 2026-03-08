import os
import logging
from datetime import datetime, timedelta
import psycopg
import pandas as pd
from mock_energy_data_provider import MockEnergyDataProvider

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
        
        # Convert index (time) into a regular column so it can be exported
        df_reset = df.reset_index() 
        # Convert DataFrame to a list of tuples for psycopg
        records = df_reset.values.tolist()

        try:
            # psycopg3 syntax for context managers (auto-closes connection)
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    # Using PostgreSQL native COPY for massive speed boosts
                    copy_query = f"COPY {table_name} (time, load_kw, solar_kw, price_usd_per_kwh) FROM STDIN"
                    with cur.copy(copy_query) as copy:
                        for row in records:
                            copy.write_row(row)
                    
                    conn.commit() # Save the transaction
            logger.info("Load complete! ✅")
            
        except psycopg.Error as e:
            logger.error(f"Database error during load: {e}")
            raise

if __name__ == "__main__":
    DB_DSN = os.getenv(
        "DB_DSN", 
        "postgresql://postgres:postgres@localhost:5432/battery"
    )
    
    pipeline = SensorETLPipeline(db_dsn=DB_DSN)
    
    # Define time window
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    
    # Run the Pipeline
    data = pipeline.extract(start, end, res_minutes=60)
    pipeline.load(data, table_name="sensor_telemetry")