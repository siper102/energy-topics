# 📈 Quant Phase: Predictive Modeling & Stochastic Optimization

This plan evolves BatteryOpt into an uncertainty-aware microgrid management system, focusing on Load prediction and robust optimization against intraday price volatility.

## Phase 1: The ML Prediction Service (`ml_service/`)
We move away from synthetic load data to a dedicated machine learning service.
- **Service Isolation:** Create a standalone service using PyTorch for high-performance inference.
- **Load Predictor (DNN):** 
    - **Architecture:** PyTorch Feed-forward Neural Network or LSTM.
    - **Inputs:** Historical load, Weather (Temp, Irradiance), and Temporal features.
    - **Scenario Generation:** Instead of a point forecast, the service will produce **$N$ possible load paths** (scenarios) to represent uncertainty.
- **Training Pipeline:** logic in `core_api` to feed historical telemetry to the `ml_service`.

## Phase 2: Stochastic Optimization (Intraday Robustness)
Transition from deterministic optimization to a model that handles uncertainty around ENTSO-E Day-Ahead (DA) prices.
- **Intraday Uncertainty:** While DA prices are known, real-time delivery often deviates. We will model the **Intraday Spread** (DA vs. Real-time) as a stochastic variable.
- **Multi-Scenario Solver:**
    - **Input:** $N$ Load scenarios from the `ml_service` and a distribution of Intraday price spreads.
    - **Objective:** Optimize a *single* dispatch plan that maximizes expected profit across all scenarios.
    - **Risk Mitigation:** Add a penalty for "Empty Battery" states in high-price/low-solar scenarios.

## Phase 3: Data Enrichment for ML
Before training, we need a "Golden Dataset":
- **Weather Historicals:** Extend the `OpenMeteoSolarProvider` to fetch historical weather via the Open-Meteo API.
- **Intraday Data:** Extend the `ENTSOEPriceProvider` to fetch actual delivery/settlement prices to calculate historical volatility relative to DA prices.

## Phase 4: Quant Infrastructure & Backtesting
- **Backtesting Engine:** Walk through historical data day-by-day.
    - Predict Load (ML Service) -> Optimize (Stoch. Solver) -> Calculate Realized Profit (using actual Intraday prices).
- **Comparison:** Compare "Deterministic Hindsight" vs. "Stochastic Forward" performance.

---

## 🛠️ Immediate Next Steps
1.  **Initialize `ml_service`:** Folder structure, Dockerfile, and PyTorch boilerplate.
2.  **Scenario Generator:** Implement a "Jittered Load" generator in the ML service as a baseline for the stochastic optimizer.
3.  **Upgrade Optimizer:** Refactor the Pyomo model to accept multiple scenarios.
