import json
import tempfile
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
        self._temp_dir = tempfile.TemporaryDirectory()
        self._paths = {
            "gas_curve": None,
            "power_curve": None,
            "model_params": None,
            "unit_params": None
        }

    def _write_json(self, data: Any, filename: str) -> str:
        path = os.path.join(self._temp_dir.name, filename)
        with open(path, 'w') as f:
            json.dump(data, f)
        return path

    def _write_csv(self, df: pd.DataFrame, filename: str) -> str:
        path = os.path.join(self._temp_dir.name, filename)
        df.to_csv(path)
        return path

    def load_parameters(self, model_params: Dict[str, Any], asset_params: Optional[Any] = None):
        """
        Load parameters. `asset_params` should be a list of facility parameters.
        """
        self._paths["model_params"] = self._write_json(model_params, "parameters.json")
        
        if asset_params:
            # asset_params might be a list of dicts or list of objects
            # Ensure it's serializable
            if hasattr(asset_params[0], 'to_dict'):
                data = [x.to_dict() for x in asset_params]
            else:
                data = asset_params
            self._paths["unit_params"] = self._write_json(data, "facility.json")

    def load_forward_curves(self, curves: Dict[str, pd.DataFrame]):
        """
        Expects keys: 'gas', 'power'
        """
        if 'gas' not in curves or 'power' not in curves:
            raise ValueError("TollingModel requires 'gas' and 'power' forward curves.")
        
        self._paths["gas_curve"] = self._write_csv(curves['gas'], "gas_curve.csv")
        self._paths["power_curve"] = self._write_csv(curves['power'], "power_curve.csv")

    def calculate_npv(self, num_paths: int = 10000) -> float:
        self._validate_inputs()
        return tolling_agreement_valuation.calculate_profit(
            self._paths["gas_curve"],
            self._paths["power_curve"],
            self._paths["model_params"],
            self._paths["unit_params"],
            num_paths
        )

    def get_sample_paths(self, num_paths: int = 100) -> Optional[np.ndarray]:
        # Note: sample_prices in Rust only needs model params, not unit params
        if not self._paths["gas_curve"] or not self._paths["power_curve"] or not self._paths["model_params"]:
             raise ValueError("Curves and Model Parameters must be loaded before sampling.")
             
        return tolling_agreement_valuation.sample_prices(
            self._paths["gas_curve"],
            self._paths["power_curve"],
            self._paths["model_params"],
            num_paths
        )

    def _validate_inputs(self):
        for name, path in self._paths.items():
            if path is None:
                raise ValueError(f"Missing input: {name} has not been loaded.")
            if not os.path.exists(path):
                 raise ValueError(f"File missing for {name} at {path}")

    def __del__(self):
        # Cleanup temp dir
        self._temp_dir.cleanup()
