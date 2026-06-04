import os
import logging
import psycopg
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import httpx

router = APIRouter()
logger = logging.getLogger(__name__)

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@localhost:5432/battery")
OPTIMIZATION_SERVICE_URL = os.getenv("OPTIMIZATION_SERVICE_URL", "http://optimization_api:8001")

class JobCreate(BaseModel):
    start_date: str
    end_date: str
    setup_id: int
    alpha: float = 0.001
    grid_fee: float = 0.01

class JobResponse(BaseModel):
    id: int
    setup_id: Optional[int]
    type: str
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    alpha: Optional[float]
    grid_fee: Optional[float]
    created_at: datetime
    finished_at: Optional[datetime]
    error_message: Optional[str] = None
    net_profit: Optional[float] = None

class PaginatedJobsResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int

@router.get("/", response_model=PaginatedJobsResponse)
async def list_jobs(setup_id: Optional[int] = None, page: int = 1, page_size: int = 7):
    try:
        offset = (page - 1) * page_size
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                where_clause = "WHERE setup_id = %s" if setup_id else ""
                params = (setup_id,) if setup_id else ()
                
                # Get total count
                cur.execute(f"SELECT COUNT(*) as total_count FROM jobs {where_clause}", params)
                total = cur.fetchone()['total_count']

                # Get paginated jobs
                query = f"""
                    SELECT id, setup_id, type, status, start_date, end_date, alpha, grid_fee, created_at, finished_at, error_message 
                    FROM jobs {where_clause} 
                    ORDER BY start_date DESC NULLS LAST, created_at DESC 
                    LIMIT %s OFFSET %s
                """
                cur.execute(query, (*params, page_size, offset))
                jobs = cur.fetchall()
                
                for job in jobs:
                    if job['status'] == 'SUCCESS' and job.get('start_date') and job.get('end_date') and job.get('setup_id'):
                        # Align with data_routes.py: end_date should include the full day
                        # Convert date to datetime at end of day
                        real_end = datetime.combine(job['end_date'], datetime.max.time())
                        
                        cur.execute("""
                            SELECT SUM(p.expected_grid_sell_kw * t.price_sell_usd_per_kwh - p.expected_grid_buy_kw * t.price_buy_usd_per_kwh) as profit
                            FROM dispatch_plans p
                            JOIN sensor_telemetry t ON p.target_time = t.time AND p.setup_id = t.setup_id
                            WHERE p.setup_id = %s AND p.target_time >= %s AND p.target_time <= %s
                        """, (job['setup_id'], job['start_date'], real_end))
                        res = cur.fetchone()
                        # Note: This SUM assumes hourly data (delta_t = 1.0)
                        job['net_profit'] = float(res['profit']) if res and res['profit'] else 0.0
                    else:
                        job['net_profit'] = None
                        
                return {
                    "jobs": jobs,
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def poll_optimization_status(client: httpx.AsyncClient, task_id: str, timeout_seconds: int = 300):
    """Polls the optimization service until the task is complete."""
    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
        response = await client.get(f"{OPTIMIZATION_SERVICE_URL}/status/{task_id}")
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        
        if status == "SUCCESS":
            return data
        if status == "FAILURE":
            raise Exception(f"Optimization task failed: {data.get('error', 'Unknown error')}")
        
        await asyncio.sleep(2)
    raise Exception("Optimization task timed out.")

async def run_full_job_task(job_id: int, setup_id: int, start_date: str, end_date: str, alpha: float, grid_fee: float):
    try:
        # 1. Update status to RUNNING
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'RUNNING' WHERE id = %s", (job_id,))
                conn.commit()
        
        # 2. Run Ingestion
        from api.data_routes import run_ingestion
        await asyncio.to_thread(run_ingestion, start_date, end_date, setup_id)
        
        # 3. Trigger Optimization and Poll
        async with httpx.AsyncClient() as client:
            # Trigger
            response = await client.post(
                f"{OPTIMIZATION_SERVICE_URL}/solve",
                json={"alpha": alpha, "grid_fee": grid_fee, "setup_id": setup_id},
                timeout=30.0
            )
            response.raise_for_status()
            task_id = response.json().get("task_id")
            
            # Poll
            await poll_optimization_status(client, task_id)
            
            # 4. Final Success Update
            with psycopg.connect(DB_DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE jobs SET status = 'SUCCESS', finished_at = NOW() WHERE id = %s", (job_id,))
                    conn.commit()

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        try:
            with psycopg.connect(DB_DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE jobs SET status = 'FAILURE', error_message = %s, finished_at = NOW() WHERE id = %s", (str(e), job_id))
                    conn.commit()
        except Exception as db_e:
            logger.error(f"Failed to update job status to FAILURE: {db_e}")

@router.post("/trigger-full")
async def trigger_full_job(request: JobCreate, background_tasks: BackgroundTasks):
    try:
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO jobs (setup_id, type, status, start_date, end_date, alpha, grid_fee) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                    (request.setup_id, 'FULL_RUN', 'PENDING', request.start_date, request.end_date, request.alpha, request.grid_fee)
                )
                job_id = cur.fetchone()[0]
                conn.commit()
        
        background_tasks.add_task(run_full_job_task, job_id, request.setup_id, request.start_date, request.end_date, request.alpha, request.grid_fee)
        return {"message": "Full job triggered", "job_id": job_id}
    except Exception as e:
        logger.error(f"Failed to trigger full job: {e}")
        raise HTTPException(status_code=500, detail=str(e))
