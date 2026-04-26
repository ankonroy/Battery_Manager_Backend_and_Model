import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import torch
import torch.nn as nn
import torch.optim as optim
import mlflow
import mlflow.pytorch
import mlflow.sklearn
from model.models.anomaly.autoencoder import Autoencoder

def train_isolation_forest(X: pd.DataFrame):
    """
    Trains an Isolation Forest model for session-level anomaly detection.
    """
    with mlflow.start_run(run_name="IsolationForest_Training"):
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(X)
        
        # Log to MLflow
        mlflow.sklearn.log_model(model, "isolation_forest")
        print("Isolation Forest trained.")
        return model

def train_autoencoder(X: np.ndarray, epochs=50, batch_size=32):
    """
    Trains a PyTorch Autoencoder for curve-level anomaly detection.
    """
    input_dim = X.shape[1]
    model = Autoencoder(input_dim)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Convert data to PyTorch tensors
    X_tensor = torch.tensor(X, dtype=torch.float32)
    
    with mlflow.start_run(run_name="Autoencoder_Training"):
        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            output = model(X_tensor)
            loss = criterion(output, X_tensor)
            loss.backward()
            optimizer.step()
            
            if (epoch+1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
                mlflow.log_metric("loss", loss.item(), step=epoch)
        
        mlflow.pytorch.log_model(model, "autoencoder")
        return model

if __name__ == "__main__":
    print("Anomaly Detection training scripts ready.")
