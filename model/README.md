# Battery Manager ML Models

This directory contains the machine learning models and training pipeline for the Battery Manager application.

## Directory Structure

- `data/`: Raw and processed datasets (NASA, CALCE, Stanford, etc.)
- `features/`: Feature engineering and signal processing logic.
- `models/`: Specific model architectures and training/inference scripts:
  - `rul/`: Remaining Useful Life prediction (XGBoost)
  - `anomaly/`: Anomaly detection (Isolation Forest & Autoencoder)
  - `tte/`: Time-to-Empty forecasting (LSTM)
  - `clustering/`: User habit archetypes (K-Means)
- `training/`: Master training orchestration and experiment tracking with MLflow.
- `inference/`: Unified prediction interface for the backend.
- `utils/`: Metrics, visualization, and constants.
- `notebooks/`: Exploration and prototyping.

## Getting Started

1.  Install dependencies: `pip install -r requirements.txt`
2.  Place datasets in `data/raw/`
3.  Run preprocessing: `python -m model.features.engineering`
4.  Train models: `python -m model.training.pipeline`
