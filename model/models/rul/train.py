import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import pandas as pd
import numpy as np
import mlflow

def train_rul_model(data_path: str):
    """
    Trains an XGBoost model for Remaining Useful Life (RUL) prediction.
    """
    # Load and preprocess
    df = pd.read_csv(data_path)
    # Placeholder feature engineering
    X = df.drop(columns=['rul_cycles'])
    y = df['rul_cycles']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    with mlflow.start_run():
        model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        
        # Log to MLflow
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("learning_rate", 0.05)
        mlflow.log_metric("mae", mae)
        mlflow.xgboost.log_model(model, "rul_model")
        
        print(f"Model trained with MAE: {mae}")
        return model

if __name__ == "__main__":
    # This would be called with a path to processed training data
    print("RUL training script ready.")
