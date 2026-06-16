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
    Proxies a single load prediction request to the consolidated BentoML 'predict' endpoint.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/predict",
                json={"features_list": [request.features]},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            # Return single value for backward compatibility with core_api callers
            return {"forecast": data["forecasts"][0]}
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting ML service: {str(e)}")

@router.post("/predict/load/forecast")
async def predict_load_forecast(request: LoadTrajectoryRequest):
    """
    Proxies the load trajectory forecast request to the consolidated BentoML 'predict' endpoint.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/predict",
                json={"features_list": request.features_list},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            # Return as 'forecast' (list) for backward compatibility
            return {"forecast": data["forecasts"]}
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error contacting ML service: {str(e)}")
