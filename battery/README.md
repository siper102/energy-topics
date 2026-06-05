# 🔋 BatteryOpt: Battery Storage Microgrid Optimization

BatteryOpt is a microservices-based platform designed to optimize the dispatch of battery energy storage systems (BESS) within microgrids. It combines real-time data ingestion (Market Prices, Solar, Load) with mathematical optimization to maximize net profit.

## 🏗️ Architecture Overview

The system consists of four primary components interacting via a centralized TimescaleDB instance and a Celery/Redis task queue.

### 1. 📂 Core API (`core_api/`)
*   **Role:** The central data orchestrator and management layer.
*   **Responsibilities:**
    *   Exposes endpoints for managing **Setups** (Physical configurations).
    *   Manages the **Data Ingestion Pipeline** (ETL) to fetch market prices (ENTSO-E), solar forecasts (Open-Meteo), and synthetic load data.
    *   Provides a REST API for the frontend to query historical performance and job statuses.
*   **Tech:** Python (FastAPI), Psycopg3, Pandas.

### 2. 🧠 Optimization Service (`optimization_service/`)
*   **Role:** The "Quant" engine.
*   **Responsibilities:**
    *   Runs as a background **Celery Worker**.
    *   Constructs and solves a high-fidelity **Pyomo** mathematical model for the microgrid.
    *   Considers constraints: Power limits, SoC dynamics, efficiency losses, and battery degradation (alpha penalty).
    *   Saves optimized dispatch plans back to the database.
*   **Tech:** Python, Pyomo, IPOPT Solver, Celery.

### 3. 💻 Frontend (`frontend/`)
*   **Role:** The operational control center.
*   **Responsibilities:**
    *   **Operations View:** Trigger new integrated ingestion + optimization jobs and monitor live progress.
    *   **Global Dashboard:** Analyze lifetime performance, revenue trends, and battery health.
    *   **Job Analysis:** Drill down into specific optimization runs with interactive charts.
*   **Tech:** React (TypeScript), Vite, Recharts, Axios.

### 4. 🗄️ Database & Infrastructure
*   **TimescaleDB:** A PostgreSQL-based time-series database for efficient storage of high-resolution sensor and planning data.
*   **Redis:** Serves as the message broker for the asynchronous optimization tasks.

---

## 🚀 Getting Started

### Prerequisites
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
*   An **ENTSO-E API Key** (set in `.env` as `ENTSOE_API_KEY`)

### Start Everything (Standard)
The entire stack is containerized for easy deployment:
```bash
docker-compose up --build
```
*   **Frontend:** [http://localhost:5173](http://localhost:5173)
*   **Core API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Development & Tooling

### VS Code Integration
The project includes a `.vscode/launch.json` for local development outside of Docker:
1.  **Frontend (Hot Reloading):** Start the `Frontend (Vite)` config to get instant UI updates while editing.
2.  **Simulation:** Use the `Generate Runs Script` config to trigger a sequence of historical optimization jobs.

### Automation Scripts
*   `scripts/generate_runs.py`: A utility script to backfill data and trigger optimizations for a sequence of dates.
