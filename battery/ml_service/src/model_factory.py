import torch
import torch.nn as nn


class LoadPredictor(nn.Module):
    def __init__(
        self, input_size: int = 4, hidden_size: int = 64, output_size: int = 1
    ):
        """
        DNN for Load Prediction.
        Default input_size=4 (temp_c, hour, dayofweek, month)
        """
        super(LoadPredictor, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


def create_load_predictor(
    input_size: int = 4, hidden_size: int = 64, output_size: int = 1
) -> LoadPredictor:
    """
    Factory function to create a LoadPredictor model instance.
    """
    return LoadPredictor(
        input_size=input_size, hidden_size=hidden_size, output_size=output_size
    )
