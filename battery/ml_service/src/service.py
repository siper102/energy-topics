import bentoml
import torch
import numpy as np
from pydantic import BaseModel
from typing import List, Optional
from model.data_generator import DataGenerator

# 1. Define Request/Response Models
class PredictionRequest(BaseModel):
    features: List[float]

class TrajectoryRequest(BaseModel):
    features_list: List[List[float]]
    num_scenarios: Optional[int] = 5

class PredictionResponse(BaseModel):
    forecast: float

class ForecastResponse(BaseModel):
    forecast: List[float]

# 2. Define the BentoML Service
@bentoml.service(
    name="battery_ml_service",
    resources={"cpu": "500m"},
    traffic={"timeout": 10},
)
class BatteryMLService:
    def __init__(self):
        # Load the latest model from the store
        # This will now succeed because entrypoint.sh ensures it's trained
        self.bento_model = bentoml.models.get("battery_load_predictor:latest")
        self.model = bentoml.pytorch.load_model(self.bento_model)
        self.model.eval()
        
        # Retrieve the scaler from custom_objects
        self.scaler = self.bento_model.custom_objects.get("scaler")
        print(f"✅ Loaded model and scaler from BentoML store: {self.bento_model.tag}")

    @bentoml.api
    def predict_load(self, request: PredictionRequest) -> PredictionResponse:
        """Point-estimate load forecast for a single timestamp."""
        feat_np = np.array([request.features], dtype=np.float32)
        if self.scaler:
            feat_np = self.scaler.transform(feat_np)
        
        inputs = torch.from_numpy(feat_np)
        with torch.no_grad():
            prediction = self.model(inputs)
        
        return PredictionResponse(forecast=float(prediction.item()))

    @bentoml.api
    def predict_load_forecast(self, request: TrajectoryRequest) -> ForecastResponse:
        """Point-estimate trajectory forecast for a sequence of features."""
        feat_np = np.array(request.features_list, dtype=np.float32)
        if self.scaler:
            feat_np = self.scaler.transform(feat_np)
        
        inputs = torch.from_numpy(feat_np)
        with torch.no_grad():
            base_forecasts = self.model(inputs).numpy().flatten()
            
        return ForecastResponse(forecast=base_forecasts.tolist())
