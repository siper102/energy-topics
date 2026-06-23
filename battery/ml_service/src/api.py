import bentoml
import torch
import numpy as np
from pydantic import BaseModel
from typing import List
from model_factory import LoadPredictor

torch.serialization.add_safe_globals([LoadPredictor])


class PredictionResponse(BaseModel):
    forecasts: List[float]


# 2. Define the BentoML Service
@bentoml.service(
    name="battery_ml_service",
    resources={"cpu": "500m"},
    traffic={"timeout": 10},
)
class BatteryMLService:
    def __init__(self):
        # Load the latest model from the store
        self.bento_model = bentoml.models.get("battery_load_predictor:latest")

        # Load using native torch.load from the BentoML model store path
        self.model = torch.load(
            self.bento_model.path_of("model.pth"), weights_only=False
        )
        self.model.eval()

        # Retrieve the scaler from custom_objects
        self.scaler = self.bento_model.custom_objects.get("scaler")
        print(f"✅ Loaded model and scaler from BentoML store: {self.bento_model.tag}")

    @bentoml.api
    def predict(self, features_list: List[List[float]]) -> PredictionResponse:
        """Batch point-estimate load forecast for multiple sets of features."""
        feat_np = np.array(features_list, dtype=np.float32)
        if self.scaler:
            feat_np = self.scaler.transform(feat_np)

        inputs = torch.from_numpy(feat_np)
        with torch.no_grad():
            # The model is expected to output a tensor of shape (batch_size, 1) or (batch_size,)
            # We flatten it to get a list of floats
            predictions = self.model(inputs).numpy().flatten()

        return PredictionResponse(forecasts=predictions.tolist())
