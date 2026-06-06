from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import torch
import joblib
import os
import numpy as np
from model.predictor import load_model

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

class PredictionResponse(BaseModel):
    forecast: float

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

    # 1. Convert to numpy and Scale
    feat_np = np.array([request.features], dtype=np.float32)
    if scaler:
        feat_np = scaler.transform(feat_np)
    
    # 2. Convert to tensor
    inputs = torch.from_numpy(feat_np)
    
    # 3. Predict
    with torch.no_grad():
        prediction = model(inputs)
    
    return PredictionResponse(forecast=float(prediction.item()))
