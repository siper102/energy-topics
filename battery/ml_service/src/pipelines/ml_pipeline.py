import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import os
import bentoml

# Import from local model_factory
from model_factory import create_load_predictor

def train_model(data_path: str = "data/training_data.parquet"):
    """
    Core training logic: Loads data, scales, trains, and returns (model, scaler).
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at {data_path}")

    print(f"📂 Loading training data from {data_path}...")
    df = pd.read_parquet(data_path)
    
    # 1. Feature Selection
    feature_cols = ['temp_c', 'hour', 'dayofweek', 'month']
    target_col = 'load_kw'
    
    X = df[feature_cols].values.astype(np.float32)
    y = df[target_col].values.reshape(-1, 1).astype(np.float32)
    
    # 2. Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("⚖️ Features scaled.")

    # 3. Prepare Data
    X_tensor = torch.from_numpy(X_scaled)
    y_tensor = torch.from_numpy(y)
    dataset = TensorDataset(X_tensor, y_tensor)
    train_loader = DataLoader(dataset, batch_size=64, shuffle=True)

    # 4. Model Setup
    model = create_load_predictor(input_size=len(feature_cols))
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 5. Training
    epochs = 20
    print(f"🚀 Training for {epochs} epochs...")
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        if (epoch + 1) % 5 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], Loss: {epoch_loss/len(train_loader):.4f}")

    model.eval()
    return model, scaler

def run_ml_pipeline(data_path: str = "data/training_data.parquet"):
    """
    Runs the full pipeline: trains the model and saves it to BentoML store.
    """
    model, scaler = train_model(data_path)

    # 6. Save to BentoML Store (New API for v1.4+)
    print("💾 Saving model to BentoML store...")
    with bentoml.models.create(
        "battery_load_predictor",
        custom_objects={"scaler": scaler},
    ) as bento_model:
        torch.save(model, bento_model.path_of("model.pth"))
    
    print("✅ Model saved to BentoML store as 'battery_load_predictor'.")

if __name__ == "__main__":
    run_ml_pipeline()
