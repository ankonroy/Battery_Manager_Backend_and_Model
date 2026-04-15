import torch
import torch.nn as nn

class TTEForecaster(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers=2):
        super(TTEForecaster, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1) # Output 1: Minutes until empty

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :]) # Take only the last prediction
        return out
