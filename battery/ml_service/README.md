# BatteryOpt ML Service 🧠

This service provides load forecasting capabilities for the microgrid optimization platform using Deep Learning. It handles the entire lifecycle from data acquisition and synthetic load generation to model training and serving via BentoML.

## 🌟 Key Features

- **Load Prediction**: DNN-based point estimates for electricity load.
- **Data Sourcing**: Historical weather data fetched from **OpenMeteo**.
- **Synthetic Load Generation**: Realistic load simulation via the `LoadSensor` component.
- **Automated Pipeline**: Integrated scripts for data generation, training, and registration.

## 🏗️ Model Architecture

The service uses a PyTorch-based Multi-Layer Perceptron (MLP):

- **Inputs (4)**: `temp_c`, `hour`, `dayofweek`, `month`.
- **Layers**: 3 Linear layers with ReLU activation.
- **Output (1)**: `load_kw` (Point estimate).

## 📉 Load Generation Mapping

The synthetic load $L(t)$ is generated using a multi-component model:

$$L(t) = \max(0.1, L_{base} + A(t) + T(Temp_t) + \eta_t)$$

### 1. Activity Component $A(t)$

Models diurnal human activity based on the hour of the day:

- **Morning Peak (07:00-09:00)**: $+2.0$ kW
- **Evening Peak (17:00-22:00)**: $+3.0$ kW
- **Daytime (09:00-17:00)**: $+1.0$ kW
- **Weekend Multiplier**: $0.8 \times A(t) + 0.5$

### 2. Thermal Component $T(Temp_t)$

Models HVAC demand based on ambient temperature:

- **Cooling**: $\max(0, (Temp_t - 22) \times 0.4)$
- **Heating**: $\max(0, (10 - Temp_t) \times 0.3)$

### 3. Stochastic Component $\eta_t$

Models unpredictable fluctuations using an **AR(1) Noise Process**:
$$\eta_t = \phi \cdot \eta_{t-1} + \epsilon_t, \quad \epsilon_t \sim \mathcal{N}(0, \sigma^2)$$
Default parameters: $\phi = 0.7$, $\sigma = 0.2$.

## 🔌 API Endpoints

- `POST /predict`: Batch point-estimate load forecast for one or more feature sets.
  - **Request Body**: `{"features_list": [[temp, hour, day, month], ...]}`
  - **Response**: `{"forecasts": [val1, val2, ...]}`

## 🛠️ Local Setup & Development

### 1. Training the Model

To fetch data from OpenMeteo, generate the load, and train the model in one go:

```bash
cd ml_service
export PYTHONPATH=src
.venv/bin/python src/train_model.py
```

### 2. Serving Locally

To start the BentoML prediction server:

```bash
cd ml_service
export PYTHONPATH=src
.venv/bin/bentoml serve src.api:BatteryMLService --reload --port 8002
```

### 3. Running via Entrypoint

The service includes a script that checks for an existing model and trains it if missing:

```bash
cd ml_service
./entrypoint.sh
```
