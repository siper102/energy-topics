import logging
import pandas as pd
from optimization.model_factory import create_microgrid_model, Hyperparameters
from optimization.solver import run_optimization_and_get_results
from optimization.database_connector import load_data, save_data

logger = logging.getLogger(__name__)

class BatteryOptimizationPipeline:
    def __init__(self, db_dsn: str):
        self.db_dsn = db_dsn

    def run(self, setup_id: int, alpha: float, grid_fee: float):
        # 1. Load Data
        logger.info(f"📥 Loading data for setup_id={setup_id}...")
        time_series, battery_params = load_data(setup_id=setup_id)
        
        # 2. Build Model
        logger.info(f"📝 Building model for setup_id={setup_id} (alpha={alpha}, fee={grid_fee})...")
        hyper_params = Hyperparameters(alpha=alpha, grid_fee=grid_fee)
        model = create_microgrid_model(
            time_series=time_series,
            battery_params=battery_params,
            hyper_params=hyper_params
        )
        
        # 3. Solve
        logger.info("🚀 Running solver...")
        solution = run_optimization_and_get_results(model=model)
        
        # 4. Save Results
        logger.info("💾 Saving results to database...")
        save_data(solution, setup_id=setup_id)
        
        return solution
