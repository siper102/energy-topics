import os
import logging
import pandas as pd
from optimization.model_factory import create_microgrid_model, Hyperparameters
from optimization.solver import run_optimization_and_get_results
from optimization.database_connector import load_data, save_data

logger = logging.getLogger(__name__)

hyper_params = Hyperparameters(alpha=0.001, grid_fee=0.01)

class OptimizationPipeline:
    def __init__(self, hyper_params: Hyperparameters, setup_id: int):
        self.hyper_params = hyper_params
        self.setup_id = setup_id

    def run_pipeline(self):
        # 1. Load Data
        # load_data fetches from sensor_telemetry which already contains 
        # ML-generated forecasts for load_kw (via the core_api ingestion).
        time_series, battery_params = load_data(setup_id=self.setup_id)
        
        # 2. Build Model
        # Since we use the loaded load_kw directly, we don't need to call 
        # the ML service here anymore.
        logger.info(f"📝 Building DETERMINISTIC model for setup_id={self.setup_id}...")
        model = create_microgrid_model(
            time_series=time_series,
            battery_params=battery_params,
            hyper_params=self.hyper_params
        )
        
        # 3. Solve
        solution = run_optimization_and_get_results(model=model)
        
        # 4. Save Results
        save_data(solution, setup_id=self.setup_id)

if __name__ == "__main__":
    # Ensure logging is configured when running directly
    logging.basicConfig(level=logging.INFO)
    pipeline = OptimizationPipeline(hyper_params=hyper_params, setup_id=1)
    pipeline.run_pipeline()
