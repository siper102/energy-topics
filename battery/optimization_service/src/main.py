from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from worker import celery_app
from tasks import run_optimization_task
from celery.result import AsyncResult

app = FastAPI(title="Optimization Service")

class OptimizationRequest(BaseModel):
    alpha: float = 0.001
    grid_fee: float = 0.01

class TaskResponse(BaseModel):
    task_id: str
    status: str

@app.get("/")
def read_root():
    return {"message": "Battery Optimization Compute Node"}

@app.post("/solve", response_model=TaskResponse)
def trigger_optimization(request: OptimizationRequest):
    """
    Triggers an asynchronous optimization job.
    """
    task = run_optimization_task.delay(
        alpha=request.alpha,
        grid_fee=request.grid_fee
    )
    return {"task_id": task.id, "status": "PENDING"}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    """
    Checks the status of a specific optimization task.
    """
    res = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": res.status,
    }
    
    if res.ready():
        if res.successful():
            response["result"] = res.result
        else:
            response["error"] = str(res.result)
            
    return response
