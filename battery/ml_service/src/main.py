from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import torch
import joblib
import os
import numpy as np
from model.predictor import load_model
from model.data_generator import DataGenerator

app = FastAPI(title="BatteryOpt ML Prediction Service")

# Paths
MODEL_PATH = os.getenv("MODEL_PATH", "ml_service/data/model.pth")
SCALER_PATH = os.getenv("SCALER_PATH", "ml_service/data/scaler.joblib")

# Load model and scaler on startup
model = load_model(MODEL_PATH)
scaler = None
if os.path.exists(SCALER_PATH):
    scaler = joblib.load(SCALER_PATH)
    print(f"✅ Loaded scaler from {SCALER_PATH}")
else:
    print(f"⚠️ Warning: Scaler not found at {SCALER_PATH}. Predictions will be unscaled.")

class PredictionRequest(BaseModel):
    # Features: [solar_kw, temp_c, hour, dayofweek, month]
    features: List[float]

class TrajectoryRequest(BaseModel):
    # List of feature vectors for a sequence (e.g. 24 hours)
    features_list: List[List[float]]
    num_scenarios: Optional[int] = 5

class PredictionResponse(BaseModel):
    forecast: float

class ScenarioResponse(BaseModel):
    # num_scenarios x sequence_length
    scenarios: List[List[float]]

@app.get("/health")
def health():
    return {
        "status": "ok", 
        "service": "ml_service",
        "model_loaded": os.path.exists(MODEL_PATH),
        "scaler_loaded": scaler is not None
    }

@app.post("/predict/load", response_model=PredictionResponse)
async def predict_load(request: PredictionRequest):
    """
    Endpoint for point-estimate load forecasting.
    """
    if len(request.features) != 5:
        raise HTTPException(status_code=400, detail="Expected 5 features: [solar_kw, temp_c, hour, dayofweek, month]")

    feat_np = np.array([request.features], dtype=np.float32)
    if scaler:
        feat_np = scaler.transform(feat_np)
    
    inputs = torch.from_numpy(feat_np)
    with torch.no_grad():
        prediction = model(inputs)
    
    return PredictionResponse(forecast=float(prediction.item()))

@app.post("/predict/load/scenarios", response_model=ScenarioResponse)
async def predict_load_scenarios(request: TrajectoryRequest):
    """
    Generates multiple stochastic scenarios for a trajectory of features.
    """
    if not request.features_list:
        raise HTTPException(status_code=400, detail="Empty features_list provided.")

    # 1. Get base predictions for the entire trajectory
    feat_np = np.array(request.features_list, dtype=np.float32)
    if scaler:
        feat_np = scaler.transform(feat_np)
    
    inputs = torch.from_numpy(feat_np)
    with torch.no_grad():
        base_forecasts = model(inputs).numpy().flatten() # (N,)
    
    # 2. Generate stochastic scenarios
    n_steps = len(base_forecasts)
    n_scenarios = request.num_scenarios
    
    all_scenarios = []
    for _ in range(n_scenarios):
        # Generate AR(1) noise trajectory
        noise = DataGenerator.generate_ar1_noise(n_steps)
        # Add to base forecast and ensure positivity
        scenario = np.maximum(0.1, base_forecasts + noise)
        all_scenarios.append(scenario.tolist())
    
    return ScenarioResponse(scenarios=all_scenarios)
