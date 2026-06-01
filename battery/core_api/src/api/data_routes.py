import os
import logging
import psycopg
import pandas as pd
from datetime import datetime, timedelta
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

# Global state for ingestion status (simplification for step-by-step)
ingestion_status = {"status": "IDLE", "message": "", "last_run": None}

def run_ingestion(start_date: str, end_date: str):
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
        pipeline = SensorETLPipeline(
            db_dsn=DB_DSN,
            load_provider=MockLoadProvider(),
            solar_provider=OpenMeteoSolarProvider(lat=51.26, lon=6.84, peak_power_kw=5.0),
            price_provider=ENTSOEPriceProvider(API_KEY)
        )
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Adjust end to the end of that day (23:59:59) for a full range
        end = end.replace(hour=23, minute=59, second=59)
        
        logger.info(f"Triggering ingestion: {start} to {end}")
        data = pipeline.extract(start, end)
        
        if data.empty:
            msg = f"Data extraction returned 0 records for range {start_date} to {end_date}."
            logger.warning(msg)
            ingestion_status["status"] = "FAILURE"
            ingestion_status["message"] = msg
            return

        pipeline.load(data)
        success_msg = f"Successfully ingested {len(data)} records for {start_date} to {end_date}."
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
    background_tasks.add_task(run_ingestion, request.start_date, request.end_date)
    return {"message": "Data ingestion triggered in the background."}

@router.get("/dashboard-data")
async def get_dashboard_data():
    """
    Fetches the latest telemetry and dispatch plans for the dashboard.
    """
    DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5432/battery")
    
    try:
        with psycopg.connect(DB_DSN) as conn:
            # Fetch telemetry
            query_telemetry = """
            SELECT time, load_kw, solar_kw, price_buy_usd_per_kwh, price_sell_usd_per_kwh 
            FROM sensor_telemetry 
            ORDER BY time ASC;
            """
            df_telemetry = pd.read_sql(query_telemetry, conn)
            
            # Fetch dispatch plans
            query_plans = """
            SELECT target_time, cmd_charge_kw, cmd_discharge_kw, expected_soc_kwh, expected_grid_buy_kw, expected_grid_sell_kw
            FROM dispatch_plans
            ORDER BY target_time ASC;
            """
            df_plans = pd.read_sql(query_plans, conn)
            
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
