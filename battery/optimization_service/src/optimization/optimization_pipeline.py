from optimization.model_factory import create_microgrid_model
from optimization.solver import run_optimization_and_get_results
from optimization.database_connector import load_data, save_data
from optimization.model_factory import Hyperparameters

### Battery Parameter class

### Hyperparameters
hyper_params = Hyperparameters(alpha=0.001, grid_fee=0.01)

class OptimizationPipeline:
    def __init__(self, hyper_params: Hyperparameters, setup_id: int):
        self.hyper_params = hyper_params
        self.setup_id = setup_id

    def run_pipeline(self):
        time_series, battery_params = load_data(setup_id=self.setup_id)
        model = create_microgrid_model(
            time_series=time_series,
            battery_params=battery_params,
            hyper_params=self.hyper_params
        )
        solution = run_optimization_and_get_results(model=model)
        save_data(solution, setup_id=self.setup_id)

if __name__ == "__main__":
    # Default to setup_id=1 for legacy/manual runs if not specified
    pipeline = OptimizationPipeline(hyper_params=hyper_params, setup_id=1)
    pipeline.run_pipeline()