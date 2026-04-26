import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import mlflow
import mlflow.pytorch
from model.models.tte.lstm_model import TTEForecaster

def prepare_sequences(data, sequence_length):
    """
    Prepares data for LSTM by creating sequences.
    """
    sequences = []
    labels = []
    for i in range(len(data) - sequence_length):
        sequences.append(data[i:i+sequence_length, :-1])
        labels.append(data[i+sequence_length, -1])
    return np.array(sequences), np.array(labels)

def train_tte_model(X: np.ndarray, y: np.ndarray, sequence_length=10, epochs=100, batch_size=32):
    """
    Trains an LSTM for time-to-empty (TTE) forecasting.
    """
    input_dim = X.shape[2]
    model = TTEForecaster(input_dim, 64)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Convert to tensors
    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.float32).view(-1, 1)
    
    with mlflow.start_run(run_name="TTE_LSTM_Training"):
        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            outputs = model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
            
            if (epoch+1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
                mlflow.log_metric("loss", loss.item(), step=epoch)
                
        mlflow.pytorch.log_model(model, "tte_model")
        return model

if __name__ == "__main__":
    print("TTE Forecasting model script ready.")
