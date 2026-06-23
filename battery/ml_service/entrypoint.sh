#!/bin/bash
set -e

# Path to the BentoML model store index
MODEL_NAME="battery_load_predictor"

echo "🔍 Checking for model '$MODEL_NAME' in BentoML store..."

# Export PYTHONPATH to include the src directory for imports
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Check if the model exists in the local store
if bentoml models list | grep -q "$MODEL_NAME"; then
    echo "✅ Model found. Starting BentoML service..."
else
    echo "⚠️ Model not found. Starting consolidated training routine..."

    # Run the consolidated training and registration script
    python src/train_model.py

    echo "✅ Training and registration complete. Starting BentoML service..."
fi

# Start the BentoML service (now using src.api:BatteryMLService)
exec bentoml serve src.api:BatteryMLService --host 0.0.0.0 --port 8002
