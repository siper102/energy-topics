import os
import logging
import psycopg
import pandas as pd
from datetime import datetime
from worker import celery_app
from optimization.optimization_pipeline import BatteryOptimizationPipeline
from database import load_battery_params, save_telemetry_data, save_dispatch_plan
from data.extract_data import SensorExtractPipeline
from data.forecast_load_provider import ForecastLoadDataProvider
from data.open_meteo_solar_provider import OpenMeteoSolarProvider
from data.entsoe_e_data_provider import ENTSOEPriceProvider

logger = logging.getLogger(__name__)

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@timescaledb:5432/battery")
ENTSOE_API_KEY = os.getenv("ENTSOE_API_KEY")

def _run_ingestion(start_date: str, end_date: str, setup_id: int) -> pd.DataFrame:
    """Internal ingestion logic. Returns DataFrame without writing to DB."""
    logger.info(f"📥 Starting in-memory ingestion for setup {setup_id} ({start_date} to {end_date})")
    
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT lat, lon, peak_power_kw, tilt, azimuth FROM setups WHERE id = %s", (setup_id,))
            setup_row = cur.fetchone()
            if not setup_row:
                raise ValueError(f"Setup ID {setup_id} not found")
            
            lat, lon, peak_power, tilt, azimuth = setup_row

    pipeline = SensorExtractPipeline(
        load_provider=ForecastLoadDataProvider(lat=float(lat), lon=float(lon)),
        solar_provider=OpenMeteoSolarProvider(
            lat=float(lat), 
            lon=float(lon), 
            peak_power_kw=float(peak_power),
            tilt=float(tilt),
            azimuth=float(azimuth)
        ),
        price_provider=ENTSOEPriceProvider(ENTSOE_API_KEY)
    )
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    
    df = pipeline.extract(start, end)
    if df.empty:
        raise ValueError("No data extracted during ingestion phase.")

    return df

def _run_optimization(setup_id: int, alpha: float, grid_fee: float, 
                      time_series: pd.DataFrame, battery_params):
    """Internal optimization logic. Uses in-memory data."""
    logger.info(f"📊 Starting in-memory optimization for setup {setup_id}")
    pipeline = BatteryOptimizationPipeline()
    df_results = pipeline.run(
        setup_id=setup_id, 
        alpha=alpha, 
        grid_fee=grid_fee,
        time_series=time_series,
        battery_params=battery_params
    )
    return df_results

@celery_app.task(name="tasks.run_full_job_task")
def run_full_job_task(job_id: int, setup_id: int, start_date: str, end_date: str, alpha: float, grid_fee: float):
    """Orchestrates ingestion and optimization as a single unit of work."""
    logger.info(f"🚀 Starting full job {job_id} for setup {setup_id}")
    
    try:
        # 1. Update status to RUNNING
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'RUNNING' WHERE id = %s", (job_id,))
                conn.commit()

        # 2. Fetch Battery Parameters (Physical Constraints)
        battery_params = load_battery_params(setup_id)

        # 3. Ingest Data (In-Memory)
        df_telemetry = _run_ingestion(start_date, end_date, setup_id)
        
        # 4. Optimize (In-Memory)
        df_results = _run_optimization(setup_id, alpha, grid_fee, df_telemetry, battery_params)
        
        # 5. Persistence Phase (Write both inputs and outputs to DB at once)
        logger.info(f"💾 Persistence phase for job {job_id}...")
        save_telemetry_data(df_telemetry, setup_id)
        save_dispatch_plan(df_results, setup_id)
        
        # 6. Final Success Update
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'SUCCESS', finished_at = NOW() WHERE id = %s", (job_id,))
                conn.commit()
        
        logger.info(f"✅ Job {job_id} completed successfully.")
        return {"status": "SUCCESS", "job_id": job_id}

    except Exception as e:
        logger.error(f"❌ Full job {job_id} failed: {e}")
        try:
            with psycopg.connect(DB_DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE jobs SET status = 'FAILURE', error_message = %s, finished_at = NOW() WHERE id = %s", 
                        (str(e), job_id)
                    )
                    conn.commit()
        except Exception as db_e:
            logger.error(f"Critical: Failed to update error status in DB: {db_e}")
        raise
