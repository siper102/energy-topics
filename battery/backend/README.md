# BatteryOpt Optimization Service ⚖️

The compute engine for solving complex energy dispatch problems under uncertainty.

## 🌟 Key Features
- **Deterministic Optimization**: Standard MILP/NLP solver for known load/prices.
- **Stochastic Optimization**: Minimizes **Expected Cost** across multiple load scenarios (Phase 2).
- **Asynchronous Processing**: Uses Celery and Redis to handle long-running optimization tasks.
- **Robustness**: Integrated fallback to deterministic solving if the ML service is unavailable.

## 🧠 Optimization Model (Pyomo)
The service formulates a mathematical program solved via **IPOPT**:
- **Objective**: $\min \mathbb{E} [ \sum_{t} (\text{Energy Cost}_t + \text{Grid Fee}_t + \text{Degradation}_t) ]$
- **Decision Variables**: Battery Charge/Discharge, Grid Buy/Sell.
- **State Variable**: Battery State of Charge (SoC).
- **Constraints**: 
    - Power balance at every time step (Kirchhoff’s Current Law).
    - Battery energy dynamics (efficiency-aware).
    - Hardware physical limits (max power, capacity).

## 🗄️ Database Integration
- **Inputs**: Fetches `sensor_telemetry` (load, solar, prices, temperature) from TimescaleDB.
- **Outputs**: Atomic UPSERT of the optimal `dispatch_plans` back to the database.

## 🔌 API Endpoints
- `POST /solve`: Triggers a new optimization task (returns `task_id`).
- `GET /status/{task_id}`: Polls the status and retrieves results of a job.

## 🏗️ Architecture
- **API**: FastAPI
- **Worker**: Celery (Distributed Task Queue)
- **Broker**: Redis
- **Modeling**: Pyomo (Python Optimization Modeling Objects)
- **Solver**: IPOPT (Interior Point Optimizer)
