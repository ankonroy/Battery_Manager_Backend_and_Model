import os
import joblib
import pandas as pd
import numpy as np
from typing import Any, Dict
from app.core.config import settings

class MLModel:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or settings.RUL_MODEL_PATH
        self.features_path = settings.RUL_FEATURES_PATH
        self.model = None
        self.features = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        """Loads the trained XGBoost model and features."""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"✅ RUL Model loaded from {self.model_path}")
            else:
                print(f"❌ Model file not found at {self.model_path}")
                self.is_loaded = False
                return
            
            if os.path.exists(self.features_path):
                self.features = joblib.load(self.features_path)
                print(f"✅ Features loaded: {self.features}")
                self.is_loaded = True
            else:
                print(f"❌ Features file not found at {self.features_path}")
                self.is_loaded = False
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.is_loaded = False

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Runs prediction on the given features using the trained model."""
        if not self.is_loaded or self.model is None:
            return self._mock_predict(features)
        
        try:
            # Create DataFrame with correct feature order
            input_df = pd.DataFrame([features])[self.features]
            
            # Predict
            rul = self.model.predict(input_df)[0]
            rul = max(0, int(rul))
            
            return {
                "rul_cycles": rul,
                "confidence": "high" if rul > 100 else "medium",
                "error": None
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            return self._mock_predict(features)

    def predict_from_battery_data(self, soh_percent: float, cycle_number: int, 
                                   avg_temperature_c: float, duration_seconds: int) -> Dict[str, Any]:
        """Predict RUL from basic battery parameters."""
        # Create features dictionary with reasonable defaults
        features_dict = {
            'cycle_number': cycle_number,
            'soh_percent': soh_percent,
            'avg_temperature_c': avg_temperature_c,
            'max_temperature_c': avg_temperature_c + 2,
            'duration_seconds': duration_seconds,
            'degradation_rate': 0.1,
            'soh_ma5': soh_percent,
            'temp_ma5': avg_temperature_c,
            'cycles_so_far': cycle_number,
            'soh_loss_so_far': 100 - soh_percent,
            'log_cycle': np.log1p(cycle_number),
            'sqrt_cycle': np.sqrt(cycle_number),
            'temp_range': 4.0,
        }
        
        return self.predict(features_dict)

    def _mock_predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Mock prediction for fallback when model is not available."""
        soh = features.get("soh_percent", 100.0)
        cycles = features.get("cycle_number", 0)
        rul = max(0, int((soh - 70) / 0.05))  # Rough estimate
        
        return {
            "rul_cycles": rul,
            "confidence": "low",
            "error": "Model not loaded, using fallback prediction"
        }

# Global instance
ml_model = MLModel()