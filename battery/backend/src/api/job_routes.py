import os
import logging
import psycopg
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from worker import celery_app
from celery.result import AsyncResult

router = APIRouter()
logger = logging.getLogger(__name__)

DB_DSN = os.getenv("DB_DSN", "postgresql://postgres:postgres@timescaledb:5432/battery")

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
                
                cur.execute(f"SELECT COUNT(*) as total_count FROM jobs {where_clause}", params)
                total = cur.fetchone()['total_count']

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
                        real_end = datetime.combine(job['end_date'], datetime.max.time())
                        cur.execute("""
                            SELECT SUM(p.expected_grid_sell_kw * t.price_sell_usd_per_kwh - p.expected_grid_buy_kw * t.price_buy_usd_per_kwh) as profit
                            FROM dispatch_plans p
                            JOIN sensor_telemetry t ON p.target_time = t.time AND p.setup_id = t.setup_id
                            WHERE p.setup_id = %s AND p.target_time >= %s AND p.target_time <= %s
                        """, (job['setup_id'], job['start_date'], real_end))
                        res = cur.fetchone()
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

@router.post("/trigger-full")
async def trigger_full_job(request: JobCreate):
    try:
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO jobs (setup_id, type, status, start_date, end_date, alpha, grid_fee) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                    (request.setup_id, 'FULL_RUN', 'PENDING', request.start_date, request.end_date, request.alpha, request.grid_fee)
                )
                job_id = cur.fetchone()[0]
                conn.commit()
        
        celery_app.send_task(
            "tasks.run_full_job_task",
            args=[job_id, request.setup_id, request.start_date, request.end_date, request.alpha, request.grid_fee]
        )
        return {"message": "Full job triggered", "job_id": job_id}
    except Exception as e:
        logger.error(f"Failed to trigger full job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    response = {"task_id": task_id, "status": res.status}
    if res.ready():
        if res.successful():
            response["result"] = res.result
        else:
            response["error"] = str(res.result)
    return response
