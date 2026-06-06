# BatteryOpt ML Service 🧠

This service provides load forecasting capabilities for the microgrid optimization platform using Deep Learning.

## 🌟 Key Features
- **Load Prediction**: DNN-based point estimates for electricity load.
- **Stochastic Scenarios**: Generation of multiple load trajectories using AR(1) autoregressive noise to model uncertainty.
- **Synthetic Data Generation**: Realistic load simulation based on weather (temperature) and temporal patterns.
- **Automated Training**: Pipeline for training on the "Golden Dataset" stored in Parquet format.

## 🏗️ Model Architecture
The service uses a PyTorch-based Multi-Layer Perceptron (MLP):
- **Inputs (5)**: `solar_kw`, `temp_c`, `hour`, `dayofweek`, `month`.
- **Layers**: 3 Linear layers with ReLU activation.
- **Output (1)**: `load_kw` (Point estimate).

For stochastic forecasting, the service applies an **AR(1) Noise Process** ($\phi=0.7$) to the base predictions to create realistic, continuous deviations from the expected path.

## 📊 Datasets
- **Golden Dataset**: Stored at `ml_service/data/training_data.parquet`.
- **Scaler**: `ml_service/data/scaler.joblib` (StandardScaler).
- **Model Weights**: `ml_service/data/model.pth`.

## 🔌 API Endpoints
- `GET /health`: Checks if model and scaler are loaded.
- `POST /predict/load`: Returns a single point estimate.
- `POST /predict/load/scenarios`: Returns $N$ stochastic trajectories for a given feature sequence.

## 🛠️ Development
To train the model manually:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python src/model/train.py
```
