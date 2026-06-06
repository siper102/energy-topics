import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import os
import joblib

# Use absolute imports relative to src
from model.predictor import LoadPredictor

def train_model(data_path: str = "ml_service/data/training_data.parquet", model_save_path: str = "ml_service/data/model.pth", scaler_save_path: str = "ml_service/data/scaler.joblib"):
    """
    Trains the LoadPredictor DNN using the Golden Dataset.
    """
    if not os.path.exists(data_path):
        print(f"❌ Error: Data file not found at {data_path}")
        return

    print(f"📂 Loading training data from {data_path}...")
    df = pd.read_parquet(data_path)
    
    # 1. Feature Engineering: Define inputs and target
    feature_cols = ['solar_kw', 'temp_c', 'hour', 'dayofweek', 'month']
    target_col = 'load_kw'
    
    X = df[feature_cols].values.astype(np.float32)
    y = df[target_col].values.reshape(-1, 1).astype(np.float32)
    
    # 2. Preprocessing: Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Save scaler for inference
    os.makedirs(os.path.dirname(scaler_save_path), exist_ok=True)
    joblib.dump(scaler, scaler_save_path)
    print(f"⚖️ Scaler saved to {scaler_save_path}")

    # 3. Prepare PyTorch Tensors & DataLoader
    X_tensor = torch.from_numpy(X_scaled)
    y_tensor = torch.from_numpy(y)
    
    dataset = TensorDataset(X_tensor, y_tensor)
    train_loader = DataLoader(dataset, batch_size=64, shuffle=True)

    # 4. Initialize Model, Loss, and Optimizer
    input_size = len(feature_cols)
    output_size = 1 # Point estimate for now
    model = LoadPredictor(input_size=input_size, output_size=output_size)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 5. Training Loop
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

    # 6. Save Model weights
    torch.save(model.state_dict(), model_save_path)
    print(f"💾 Model weights saved to {model_save_path}")

if __name__ == "__main__":
    train_model()
