import logging
from fastapi import APIRouter
from pydantic import BaseModel
from worker import celery_app
from celery.result import AsyncResult

router = APIRouter()
logger = logging.getLogger(__name__)

class OptimizationRequest(BaseModel):
    alpha: float = 0.001
    grid_fee: float = 0.01
    setup_id: int

@router.post("/trigger")
async def trigger_optimization(request: OptimizationRequest):
    """
    Triggers an asynchronous optimization job.
    """
    task = celery_app.send_task(
        "tasks.run_optimization_task",
        args=[request.alpha, request.grid_fee, request.setup_id]
    )
    return {"task_id": task.id, "status": "PENDING"}

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    Checks the status of a specific optimization task.
    """
    res = AsyncResult(task_id, app=celery_app)
    response = {"task_id": task_id, "status": res.status}
    if res.ready():
        if res.successful():
            response["result"] = res.result
        else:
            response["error"] = str(res.result)
    return response
