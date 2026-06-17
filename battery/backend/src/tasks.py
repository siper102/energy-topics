import os
import logging
import pandas as pd
from datetime import datetime
from sqlmodel import Session
from worker import celery_app
from models import Job, Setup
from database import (
    engine,
    load_battery_params,
    save_telemetry_data,
    save_dispatch_plan,
)
from optimization.optimization_pipeline import BatteryOptimizationPipeline
from data.extract_data import SensorExtractPipeline
from data.forecast_load_provider import ForecastLoadDataProvider
from data.open_meteo_solar_provider import OpenMeteoSolarProvider
from data.entsoe_e_data_provider import ENTSOEPriceProvider

logger = logging.getLogger(__name__)

ENTSOE_API_KEY = os.getenv("ENTSOE_API_KEY")


def _run_ingestion(start_date: str, end_date: str, setup_id: int) -> pd.DataFrame:
    """Internal ingestion logic. Returns DataFrame without writing to DB."""
    logger.info(
        f"📥 Starting in-memory ingestion for setup {setup_id} ({start_date} to {end_date})"
    )

    with Session(engine) as session:
        setup = session.get(Setup, setup_id)
        if not setup:
            raise ValueError(f"Setup ID {setup_id} not found")

        # We use the lat/lon from the DB here!
        lat, lon = float(setup.lat), float(setup.lon)
        peak_power = float(setup.peak_power_kw)
        tilt, azimuth = float(setup.tilt), float(setup.azimuth)

    pipeline = SensorExtractPipeline(
        load_provider=ForecastLoadDataProvider(lat=lat, lon=lon),
        solar_provider=OpenMeteoSolarProvider(
            lat=lat, lon=lon, peak_power_kw=peak_power, tilt=tilt, azimuth=azimuth
        ),
        price_provider=ENTSOEPriceProvider(ENTSOE_API_KEY),
    )

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    df = pipeline.extract(start, end)
    if df.empty:
        raise ValueError("No data extracted during ingestion phase.")

    return df


def _run_optimization(
    setup_id: int,
    alpha: float,
    grid_fee: float,
    time_series: pd.DataFrame,
    battery_params,
):
    """Internal optimization logic. Uses in-memory data."""
    logger.info(f"📊 Starting in-memory optimization for setup {setup_id}")
    pipeline = BatteryOptimizationPipeline()
    df_results = pipeline.run(
        setup_id=setup_id,
        alpha=alpha,
        grid_fee=grid_fee,
        time_series=time_series,
        battery_params=battery_params,
    )
    return df_results


@celery_app.task(name="tasks.run_full_job_task")
def run_full_job_task(
    job_id: int,
    setup_id: int,
    start_date: str,
    end_date: str,
    alpha: float,
    grid_fee: float,
):
    """Orchestrates ingestion and optimization as a single unit of work."""
    logger.info(f"🚀 Starting full job {job_id} for setup {setup_id}")

    try:
        # 1. Update status to RUNNING
        with Session(engine) as session:
            job = session.get(Job, job_id)
            if job:
                job.status = "RUNNING"
                session.add(job)
                session.commit()

        # 2. Fetch Battery Parameters (Physical Constraints)
        battery_params = load_battery_params(setup_id)

        # 3. Ingest Data (In-Memory)
        df_telemetry = _run_ingestion(start_date, end_date, setup_id)

        # 4. Optimize (In-Memory)
        df_results = _run_optimization(
            setup_id, alpha, grid_fee, df_telemetry, battery_params
        )

        # 5. Persistence Phase (Write both inputs and outputs to DB at once)
        logger.info(f"💾 Persistence phase for job {job_id}...")
        save_telemetry_data(df_telemetry, setup_id)
        save_dispatch_plan(df_results, setup_id)

        # 6. Final Success Update
        with Session(engine) as session:
            job = session.get(Job, job_id)
            if job:
                job.status = "SUCCESS"
                job.finished_at = datetime.utcnow()
                session.add(job)
                session.commit()

        logger.info(f"✅ Job {job_id} completed successfully.")
        return {"status": "SUCCESS", "job_id": job_id}

    except Exception as e:
        logger.error(f"❌ Full job {job_id} failed: {e}")
        try:
            with Session(engine) as session:
                job = session.get(Job, job_id)
                if job:
                    job.status = "FAILURE"
                    job.error_message = str(e)
                    job.finished_at = datetime.utcnow()
                    session.add(job)
                    session.commit()
        except Exception as db_e:
            logger.error(f"Critical: Failed to update error status in DB: {db_e}")
        raise
