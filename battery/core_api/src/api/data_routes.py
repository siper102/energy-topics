import os
import logging
import psycopg
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from data.extract_data import SensorETLPipeline
from data.mock_energy_data_provider import MockLoadProvider
from data.open_meteo_solar_provider import OpenMeteoSolarProvider
from data.entsoe_e_data_provider import ENTSOEPriceProvider

router = APIRouter()
logger = logging.getLogger(__name__)

class IngestRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    setup_id: int

# Global state for ingestion status (simplification for step-by-step)
ingestion_status = {"status": "IDLE", "message": "", "last_run": None}

def run_ingestion(start_date: str, end_date: str, setup_id: int):
    """Background task to run the ETL pipeline."""
    global ingestion_status
    ingestion_status["status"] = "RUNNING"
    ingestion_status["last_run"] = datetime.now().isoformat()
    
    DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5432/battery")
    API_KEY = os.getenv("ENTSOE_API_KEY")
    
    if not API_KEY:
        error_msg = "ENTSOE_API_KEY not found."
        logger.error(error_msg)
        ingestion_status["status"] = "FAILURE"
        ingestion_status["message"] = error_msg
        return

    try:
        # Fetch setup parameters
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT lat, lon, peak_power_kw, tilt, azimuth FROM setups WHERE id = %s", (setup_id,))
                setup_row = cur.fetchone()
                if not setup_row:
                    raise ValueError(f"Setup ID {setup_id} not found")
                
                lat, lon, peak_power, tilt, azimuth = setup_row

        pipeline = SensorETLPipeline(
            db_dsn=DB_DSN,
            load_provider=MockLoadProvider(),
            solar_provider=OpenMeteoSolarProvider(
                lat=float(lat), 
                lon=float(lon), 
                peak_power_kw=float(peak_power),
                tilt=float(tilt),
                azimuth=float(azimuth)
            ),
            price_provider=ENTSOEPriceProvider(API_KEY)
        )
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Adjust end to the end of that day (23:59:59) for a full range
        end = end.replace(hour=23, minute=59, second=59)
        
        logger.info(f"Triggering ingestion for setup {setup_id}: {start} to {end}")
        data = pipeline.extract(start, end)
        
        if data.empty:
            msg = f"Data extraction returned 0 records for setup {setup_id} in range {start_date} to {end_date}."
            logger.warning(msg)
            ingestion_status["status"] = "FAILURE"
            ingestion_status["message"] = msg
            return

        pipeline.load(data, setup_id=setup_id)
        success_msg = f"Successfully ingested {len(data)} records for setup {setup_id} ({start_date} to {end_date})."
        logger.info(success_msg)
        ingestion_status["status"] = "SUCCESS"
        ingestion_status["message"] = success_msg
        
    except Exception as e:
        error_msg = f"Background ingestion failed: {str(e)}"
        logger.error(error_msg)
        ingestion_status["status"] = "FAILURE"
        ingestion_status["message"] = error_msg

@router.get("/ingest/status")
async def get_ingest_status():
    """Returns the status of the last ingestion run."""
    return ingestion_status

@router.post("/ingest")
async def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Triggers the data extraction and loading pipeline.
    """
    background_tasks.add_task(run_ingestion, request.start_date, request.end_date, request.setup_id)
    return {"message": "Data ingestion triggered in the background."}

@router.get("/dashboard-data")
async def get_dashboard_data(setup_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """
    Fetches the latest telemetry and dispatch plans for the dashboard.
    Filtering by setup_id is mandatory. Optional filtering by date range.
    """
    DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5432/battery")
    
    try:
        with psycopg.connect(DB_DSN) as conn:
            # Build queries with setup filtering
            where_telemetry = "WHERE setup_id = %s"
            where_plans = "WHERE setup_id = %s"
            params_telemetry = [setup_id]
            params_plans = [setup_id]
            
            if start_date and end_date:
                # Align with ingestion logic: end_date string should include the full day
                # We append the time to ensure we catch everything until 23:59:59
                real_end = f"{end_date} 23:59:59"
                where_telemetry += " AND time >= %s AND time <= %s"
                where_plans += " AND target_time >= %s AND target_time <= %s"
                params_telemetry.extend([start_date, real_end])
                params_plans.extend([start_date, real_end])
            
            query_telemetry = f"""
            SELECT time, load_kw, solar_kw, price_buy_usd_per_kwh, price_sell_usd_per_kwh 
            FROM sensor_telemetry 
            {where_telemetry}
            ORDER BY time ASC;
            """
            
            query_plans = f"""
            SELECT target_time, cmd_charge_kw, cmd_discharge_kw, expected_soc_kwh, expected_grid_buy_kw, expected_grid_sell_kw
            FROM dispatch_plans
            {where_plans}
            ORDER BY target_time ASC;
            """
            
            df_telemetry = pd.read_sql(query_telemetry, conn, params=params_telemetry)
            df_plans = pd.read_sql(query_plans, conn, params=params_plans)
            
            # Merge on time
            df_telemetry['time'] = pd.to_datetime(df_telemetry['time'])
            df_plans['target_time'] = pd.to_datetime(df_plans['target_time'])
            
            # Convert to list of dicts for JSON response
            return {
                "telemetry": df_telemetry.to_dict(orient="records"),
                "plans": df_plans.to_dict(orient="records")
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
