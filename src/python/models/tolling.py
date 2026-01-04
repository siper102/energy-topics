import json
import os
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from interfaces.valuation_model import ValuationModel
import tolling_agreement_valuation

class TollingModel(ValuationModel):
    """
    Implementation of the Gas-Fired Tolling Agreement model.
    Uses a high-performance Rust backend for Monte Carlo simulation.
    """

    def __init__(self):
        self.gas_curve = None
        self.power_curve = None
        self.model_params = None
        self.unit_params = None

    def load_parameters(self, model_params: Any, asset_params: Optional[Any] = None):
        """
        Load parameters. 
        Expects `model_params` to be an instance of `tolling_agreement_valuation.ModelParameters`.
        Expects `asset_params` to be a list of `tolling_agreement_valuation.UnitParameter`.
        """
        self.model_params = model_params
        self.unit_params = asset_params

    def load_forward_curves(self, curves: Dict[str, pd.DataFrame]):
        """
        Expects keys: 'gas', 'power'. DataFrames must have a 'price' column.
        """
        if 'gas' not in curves or 'power' not in curves:
            raise ValueError("TollingModel requires 'gas' and 'power' forward curves.")
        
        # Extract values as numpy arrays (float64)
        self.gas_curve = np.ascontiguousarray(curves['gas']['price'].values, dtype=np.float64)
        self.power_curve = np.ascontiguousarray(curves['power']['price'].values, dtype=np.float64)

    def calculate_npv(self, num_paths: int = 10000) -> float:
        self._validate_inputs()
        return tolling_agreement_valuation.calculate_profit(
            self.gas_curve,
            self.power_curve,
            self.model_params,
            self.unit_params,
            num_paths
        )

    def get_sample_paths(self, num_paths: int = 100) -> Optional[np.ndarray]:
        # Note: sample_prices in Rust only needs model params, not unit params
        if self.gas_curve is None or self.power_curve is None or self.model_params is None:
             raise ValueError("Curves and Model Parameters must be loaded before sampling.")
             
        return tolling_agreement_valuation.sample_prices(
            self.gas_curve,
            self.power_curve,
            self.model_params,
            num_paths
        )

    def _validate_inputs(self):
        if self.gas_curve is None:
            raise ValueError("Missing input: gas_curve has not been loaded.")
        if self.power_curve is None:
            raise ValueError("Missing input: power_curve has not been loaded.")
        if self.model_params is None:
            raise ValueError("Missing input: model_params has not been loaded.")
        if self.unit_params is None:
            raise ValueError("Missing input: unit_params has not been loaded.")

