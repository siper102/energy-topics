import os
import logging
import psycopg
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

        # 2. Ingest
        _run_ingestion(start_date, end_date, setup_id)
        
        # 3. Optimize
        _run_optimization(setup_id, alpha, grid_fee)
        
        # 4. Final Success Update
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

def _run_ingestion(start_date: str, end_date: str, setup_id: int):
    """Internal ingestion logic."""
    logger.info(f"📥 Starting internal ingestion for setup {setup_id} ({start_date} to {end_date})")
    
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
        raise ValueError("No data extracted during ingestion phase.")

    pipeline.load(data, setup_id=setup_id)
    return len(data)

def _run_optimization(setup_id: int, alpha: float, grid_fee: float):
    """Internal optimization logic."""
    logger.info(f"📊 Starting internal optimization for setup {setup_id}")
    pipeline = BatteryOptimizationPipeline(db_dsn=DB_DSN)
    results = pipeline.run(setup_id=setup_id, alpha=alpha, grid_fee=grid_fee)
    return len(results)

