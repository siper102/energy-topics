import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Get optimization service URL from environment
OPTIMIZATION_SERVICE_URL = os.getenv("OPTIMIZATION_SERVICE_URL", "http://optimization_api:8001")

class OptimizationRequest(BaseModel):
    alpha: float = 0.001
    grid_fee: float = 0.01
    setup_id: int

@router.post("/trigger")
async def trigger_optimization(request: OptimizationRequest):
    """
    Proxies the optimization request to the compute node.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{OPTIMIZATION_SERVICE_URL}/solve",
                json=request.model_dump()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting optimization service: {str(e)}")

@router.get("/status/{task_id}")
async def get_optimization_status(task_id: str):
    """
    Checks the status of a specific task on the compute node.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OPTIMIZATION_SERVICE_URL}/status/{task_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting optimization service: {str(e)}")
