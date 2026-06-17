import os
import logging
import psycopg
import asyncio
from datetime import datetime
from worker import celery_app
from optimization.optimization_pipeline import BatteryOptimizationPipeline
from data.extract_data import SensorETLPipeline
from data.forecast_load_provider import ForecastLoadDataProvider
from data.open_meteo_solar_provider import OpenMeteoSolarProvider
from data.entsoe_e_data_provider import ENTSOEPriceProvider

logger = logging.getLogger(__name__)

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@timescaledb:5432/battery")
ENTSOE_API_KEY = os.getenv("ENTSOE_API_KEY")

@celery_app.task(name="tasks.run_ingestion_task")
def run_ingestion_task(start_date: str, end_date: str, setup_id: int):
    """Extraction and Loading pipeline."""
    logger.info(f"🚀 Starting ingestion for setup {setup_id} ({start_date} to {end_date})")
    
    try:
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT lat, lon, peak_power_kw, tilt, azimuth FROM setups WHERE id = %s", (setup_id,))
                setup_row = cur.fetchone()
                if not setup_row:
                    raise ValueError(f"Setup ID {setup_id} not found")
                
                lat, lon, peak_power, tilt, azimuth = setup_row

        pipeline = SensorETLPipeline(
            db_dsn=DB_DSN,
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
        
        data = pipeline.extract(start, end)
        if data.empty:
            raise ValueError("No data extracted")

        pipeline.load(data, setup_id=setup_id)
        return {"status": "SUCCESS", "records": len(data)}
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

@celery_app.task(name="tasks.run_optimization_task")
def run_optimization_task(alpha: float, grid_fee: float, setup_id: int):
    """Runs the battery optimization model."""
    logger.info(f"🚀 Starting optimization for setup {setup_id} (alpha={alpha}, fee={grid_fee})")
    pipeline = BatteryOptimizationPipeline(db_dsn=DB_DSN)
    try:
        results = pipeline.run(setup_id=setup_id, alpha=alpha, grid_fee=grid_fee)
        return {"status": "SUCCESS", "results_count": len(results)}
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise

@celery_app.task(name="tasks.run_full_job_task")
def run_full_job_task(job_id: int, setup_id: int, start_date: str, end_date: str, alpha: float, grid_fee: float):
    """Orchestrates ingestion and optimization."""
    logger.info(f"🚀 Starting full job {job_id} for setup {setup_id}")
    
    try:
        # 1. Update status to RUNNING
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'RUNNING' WHERE id = %s", (job_id,))
                conn.commit()

        # 2. Ingest
        run_ingestion_task(start_date, end_date, setup_id)
        
        # 3. Optimize
        run_optimization_task(alpha, grid_fee, setup_id)
        
        # 4. Success
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'SUCCESS', finished_at = NOW() WHERE id = %s", (job_id,))
                conn.commit()
        
        return {"status": "SUCCESS"}

    except Exception as e:
        logger.error(f"Full job {job_id} failed: {e}")
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'FAILURE', error_message = %s, finished_at = NOW() WHERE id = %s", (str(e), job_id))
                conn.commit()
        raise
