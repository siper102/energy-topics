from model_factory import create_microgrid_model
from solver import run_optimization_and_get_results
from database_connector import load_data, save_data
from model_factory import Hyperparameters

### Battery Parameter class

### Hyperparameters
hyper_params = Hyperparameters(alpha=1.5)

class OptimizationPipeline:
    def __init__(self, hyper_params: Hyperparameters):
        self.hyper_params = hyper_params

    def run_pipeline(self):
        time_series, battery_params = load_data()
        model = create_microgrid_model(
            time_series=time_series,
            battery_params=battery_params,
            hyper_params=self.hyper_params
        )
        solution = run_optimization_and_get_results(model=model)
        save_data(solution)

if __name__ == "__main__":
    pipeline = OptimizationPipeline(hyper_params=hyper_params)
    pipeline.run_pipeline()