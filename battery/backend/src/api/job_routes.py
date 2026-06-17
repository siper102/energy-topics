import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from worker import celery_app
from celery.result import AsyncResult
from sqlalchemy import func
from sqlmodel import Session, select
from database import get_session
from models import Job, JobBase

router = APIRouter()
logger = logging.getLogger(__name__)

class JobCreate(BaseModel):
    start_date: str
    end_date: str
    setup_id: int
    alpha: float = 0.001
    grid_fee: float = 0.01

class PaginatedJobsResponse(BaseModel):
    jobs: List[Job]
    total: int
    page: int
    page_size: int

@router.get("/", response_model=PaginatedJobsResponse)
async def list_jobs(
    setup_id: Optional[int] = None, 
    page: int = 1, 
    page_size: int = 7,
    session: Session = Depends(get_session)
):
    try:
        offset = (page - 1) * page_size
        
        # Base query
        statement = select(Job)
        if setup_id:
            statement = statement.where(Job.setup_id == setup_id)
            
        # Total count
        total_statement = select(func.count()).select_from(statement.subquery())
        total = session.exec(total_statement).one()

        # Paginated results
        statement = statement.order_by(Job.start_date.desc(), Job.created_at.desc()).offset(offset).limit(page_size)
        jobs = session.exec(statement).all()
        
        # Note: net_profit calculation is currently omitted for simplicity in this SQLModel view
        # We can add it back as a @property or a separate query if needed.
                        
        return {
            "jobs": jobs,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

@router.post("/trigger-full")
async def trigger_full_job(request: JobCreate, session: Session = Depends(get_session)):
    try:
        # Create Job entry using SQLModel
        new_job = Job(
            setup_id=request.setup_id,
            type='FULL_RUN',
            status='PENDING',
            start_date=datetime.strptime(request.start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(request.end_date, "%Y-%m-%d"),
            alpha=request.alpha,
            grid_fee=request.grid_fee
        )
        session.add(new_job)
        session.commit()
        session.refresh(new_job)
        
        # Trigger Celery
        celery_app.send_task(
            "tasks.run_full_job_task",
            args=[new_job.id, request.setup_id, request.start_date, request.end_date, request.alpha, request.grid_fee]
        )
        return {"message": "Full job triggered", "job_id": new_job.id}
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
