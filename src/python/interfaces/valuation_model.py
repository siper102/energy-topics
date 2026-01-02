from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

class ValuationModel(ABC):
    """
    Abstract Base Class for quantitative valuation models.
    Enforces a standard interface for loading data, calculating value, and retrieving diagnostics.
    """

    @abstractmethod
    def load_parameters(self, model_params: Dict[str, Any], asset_params: Optional[Dict[str, Any]] = None):
        """
        Load model and asset-specific parameters.
        """
        pass

    @abstractmethod
    def load_forward_curves(self, curves: Dict[str, pd.DataFrame]):
        """
        Load forward curves required for valuation.
        
        Args:
            curves: Dictionary mapping asset names (e.g., 'gas', 'power') to DataFrames.
        """
        pass

    @abstractmethod
    def calculate_npv(self, num_paths: int = 10000) -> float:
        """
        Calculate the Net Present Value (NPV) of the asset.
        
        Args:
            num_paths: Number of Monte Carlo paths (if applicable).
        """
        pass

    @abstractmethod
    def get_sample_paths(self, num_paths: int = 100) -> Optional[np.ndarray]:
        """
        Generate sample price paths for visualization.
        
        Returns:
            np.ndarray: Array of shape (Time, Assets, Paths) or None if not supported.
        """
        pass
