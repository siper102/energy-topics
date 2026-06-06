import torch
import torch.nn as nn
import os

class LoadPredictor(nn.Module):
    def __init__(self, input_size: int = 5, hidden_size: int = 64, output_size: int = 1):
        """
        DNN for Load Prediction.
        Default input_size=5 (solar_kw, temp_c, hour, dayofweek, month)
        """
        super(LoadPredictor, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

def load_model(path: str = "ml_service/data/model.pth", input_size: int = 5) -> LoadPredictor:
    """
    Loads the trained model from the specified path.
    """
    model = LoadPredictor(input_size=input_size)
    if os.path.exists(path):
        model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))
        print(f"✅ Loaded model weights from {path}")
    else:
        print(f"⚠️ Warning: Model path {path} not found. Using uninitialized model.")
    
    model.eval()
    return model
