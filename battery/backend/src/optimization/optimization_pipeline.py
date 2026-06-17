import logging
import pandas as pd
from optimization.model_factory import (
    create_microgrid_model,
    Hyperparameters,
    BatteryParams,
)
from optimization.solver import run_optimization_and_get_results

logger = logging.getLogger(__name__)


class BatteryOptimizationPipeline:
    """
    Battery Optimization Engine.
    Strictly focuses on building and solving the mathematical model.
    """

    def __init__(self):
        pass

    def run(
        self,
        setup_id: int,
        alpha: float,
        grid_fee: float,
        time_series: pd.DataFrame,
        battery_params: BatteryParams,
    ):
        """
        Runs the battery optimization model.
        Expects all data to be provided in-memory.
        """
        logger.info(
            f"📝 Building model for setup_id={setup_id} (alpha={alpha}, fee={grid_fee})..."
        )

        hyper_params = Hyperparameters(alpha=alpha, grid_fee=grid_fee)

        # Build the Pyomo model
        model = create_microgrid_model(
            time_series=time_series,
            battery_params=battery_params,
            hyper_params=hyper_params,
        )

        # Solve the model
        logger.info("🚀 Running solver...")
        solution = run_optimization_and_get_results(model=model)

        return solution
