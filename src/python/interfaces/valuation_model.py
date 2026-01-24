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
    def calculate_daily_profits(self, num_paths: int = 10000, risk_free_rate: float = 0.0) -> np.ndarray:
        """
        Calculate daily profits for each simulation path.
        """
        pass

    @abstractmethod
    def calculate_greeks(self, num_paths: int = 10000, risk_free_rate: float = 0.0) -> Any:
        """
        Calculate Greeks (sensitivities) using AAD.
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
