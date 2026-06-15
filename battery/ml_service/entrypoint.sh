#!/bin/bash
set -e

# Path to the BentoML model store index (approximate check)
MODEL_NAME="battery_load_predictor"

echo "🔍 Checking for model '$MODEL_NAME' in BentoML store..."

# We use bentoml models list to check if the model exists
if bentoml models list | grep -q "$MODEL_NAME"; then
    echo "✅ Model found. Starting BentoML service..."
else
    echo "⚠️ Model not found. Starting automatic training pipeline..."
    
    # 1. Run Data Pipeline
    echo "📥 Running Data Pipeline..."
    python src/data_pipeline.py
    
    # 2. Run ML Pipeline
    echo "🧠 Running ML Pipeline..."
    python src/ml_pipeline.py
    
    echo "✅ Training complete. Starting BentoML service..."
fi

# Start the BentoML service
exec bentoml serve src.service:BatteryMLService --host 0.0.0.0 --port 8002
