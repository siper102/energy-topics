import httpx
import os
import logging
import pandas as pd
from optimization.model_factory import create_microgrid_model, create_stochastic_microgrid_model, Hyperparameters
from optimization.solver import run_optimization_and_get_results
from optimization.database_connector import load_data, save_data

logger = logging.getLogger(__name__)

# Config
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml_service:8002")

hyper_params = Hyperparameters(alpha=0.001, grid_fee=0.01)

class OptimizationPipeline:
    def __init__(self, hyper_params: Hyperparameters, setup_id: int):
        self.hyper_params = hyper_params
        self.setup_id = setup_id

    def _get_load_forecast(self, time_series: pd.DataFrame) -> list:
        """
        Calls the ML service to get a point-estimate load forecast based on 
        the provided weather and temporal features.
        """
        # Prepare features: [solar_kw, temp_c, hour, dayofweek, month]
        features = []
        for idx, row in time_series.iterrows():
            features.append([
                float(row['solar_kw']),
                float(row['temp_c']),
                int(idx.hour),
                int(idx.dayofweek),
                int(idx.month)
            ])
        
        try:
            logger.info(f"📡 Requesting load forecast from ML service at {ML_SERVICE_URL}...")
            response = httpx.post(
                f"{ML_SERVICE_URL}/predict",
                json={"features_list": features},
                timeout=20.0
            )
            response.raise_for_status()
            data = response.json()
            return data['forecasts']
        except Exception as e:
            logger.error(f"❌ Failed to fetch forecast from ML service: {e}")
            logger.warning("Falling back to using existing DB load_kw.")
            return None

    def run_pipeline(self):
        # 1. Load Data
        time_series, battery_params = load_data(setup_id=self.setup_id)
        
        # 2. Get Point-Estimate Forecast
        forecast = self._get_load_forecast(time_series)
        if forecast:
            logger.info(f"📈 Updating load_kw with ML forecast (length: {len(forecast)})")
            time_series['load_kw'] = forecast

        # 3. Build Model (Currently only Deterministic since load scenarios are removed)
        logger.info(f"📝 Building DETERMINISTIC model for setup_id={self.setup_id}...")
        model = create_microgrid_model(
            time_series=time_series,
            battery_params=battery_params,
            hyper_params=self.hyper_params
        )
        
        # 4. Solve
        solution = run_optimization_and_get_results(model=model)
        
        # 5. Save Results
        save_data(solution, setup_id=self.setup_id)

if __name__ == "__main__":
    pipeline = OptimizationPipeline(hyper_params=hyper_params, setup_id=1)
    pipeline.run_pipeline()