import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml_service:8002")

class LoadPredictionRequest(BaseModel):
    features: List[float]

class LoadTrajectoryRequest(BaseModel):
    features_list: List[List[float]]

@router.post("/predict/load")
async def predict_load(request: LoadPredictionRequest):
    """
    Proxies the load prediction request to the BentoML service.
    """
    async with httpx.AsyncClient() as client:
        try:
            # BentoML endpoint matches the method name
            response = await client.post(
                f"{ML_SERVICE_URL}/predict_load",
                json=request.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting ML service: {str(e)}")

@router.post("/predict/load/forecast")
async def predict_load_forecast(request: LoadTrajectoryRequest):
    """
    Proxies the load trajectory forecast request to the BentoML service.
    """
    async with httpx.AsyncClient() as client:
        try:
            # BentoML endpoint matches the method name
            response = await client.post(
                f"{ML_SERVICE_URL}/predict_load_forecast",
                json=request.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting ML service: {str(e)}")
