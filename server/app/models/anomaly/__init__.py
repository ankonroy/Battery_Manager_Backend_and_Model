"""
Cycle-Level Anomaly Detection Model for Battery Cycles.
Uses Isolation Forest trained on CALCE CX2_16 data.
"""
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Any


class AnomalyDetector:
    """Detects anomalous battery cycles and explains the cause."""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.classifier = None
        self._load_model()
    
    def _load_model(self):
        """Load the trained model and associated files."""
        model_dir = Path(__file__).parent / "saved_models"
        
        required_files = [
            "isolation_forest_app.joblib",
            "scaler_app.joblib",
            "feature_columns_app.joblib",
            "anomaly_classifier.joblib"
        ]
        
        # Check if all files exist
        missing_files = [f for f in required_files if not (model_dir / f).exists()]
        if missing_files:
            raise FileNotFoundError(
                f"Missing model files in {model_dir}: {missing_files}\n"
                "Please copy the .joblib files from the notebook output directory."
            )
        
        self.model = joblib.load(model_dir / "isolation_forest_app.joblib")
        self.scaler = joblib.load(model_dir / "scaler_app.joblib")
        self.feature_columns = joblib.load(model_dir / "feature_columns_app.joblib")
        self.classifier = joblib.load(model_dir / "anomaly_classifier.joblib")
        
        print(f"✅ AnomalyDetector loaded with {len(self.feature_columns)} features")
    
    def predict(self, cycle_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict if a cycle is anomalous and explain why.
        
        Args:
            cycle_data: Dictionary with feature values
        
        Returns:
            Dictionary with prediction results matching CycleAnomalyResponse schema
        """
        # Validate all required features are present
        missing_features = [col for col in self.feature_columns if col not in cycle_data]
        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")
        
        # Extract features in correct order
        features = [cycle_data[col] for col in self.feature_columns]
        
        # Scale and predict
        features_scaled = self.scaler.transform([features])
        prediction = self.model.predict(features_scaled)[0]
        anomaly_score = self.model.score_samples(features_scaled)[0]
        
        is_anomaly = prediction == -1
        
        result = {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": float(anomaly_score),
            "confidence": self._get_confidence(anomaly_score)
        }
        
        # Add explanation if anomalous
        if is_anomaly:
            result["explanation"] = self._explain_anomaly(cycle_data)
        else:
            result["explanation"] = None
        
        return result
    
    def _get_confidence(self, score: float) -> str:
        """Convert anomaly score to confidence level."""
        if score < -0.25:
            return "high"
        elif score < -0.15:
            return "medium"
        else:
            return "low"
    
    def _explain_anomaly(self, cycle_data: Dict[str, float]) -> Dict[str, Any]:
        """Explain why a cycle is anomalous using feature deviation."""
        feature_stats = self.classifier['feature_stats']
        feature_to_anomaly = self.classifier['feature_to_anomaly']
        threshold = self.classifier.get('threshold', 2.0)
        
        deviations = {}
        directions = {}
        
        for feature, value in cycle_data.items():
            if feature in feature_stats:
                stats = feature_stats[feature]
                deviation = self._calculate_deviation(value, stats)
                
                if deviation > threshold:
                    deviations[feature] = deviation
                    directions[feature] = 'high' if value > stats['median'] else 'low'
        
        if not deviations:
            return {
                "type": "multivariate_anomaly",
                "primary_driver": "unknown",
                "direction": "unknown",
                "deviation_score": 0.0,
                "all_deviations": {},
                "confidence": "low",
                "message": "🔍 We noticed an unusual pattern in your battery behavior. This is usually temporary and resolves on its own."
            }
        
        # Find primary driver
        top_feature = max(deviations, key=deviations.get)
        direction = directions[top_feature]
        top_deviation = deviations[top_feature]
        
        # Get anomaly type
        anomaly_map = feature_to_anomaly.get(top_feature, {})
        anomaly_type = anomaly_map.get(direction, f"{top_feature}_{direction}_anomaly")
        
        # Generate human-readable message
        message = self._generate_message(
            top_feature, 
            direction, 
            cycle_data[top_feature],
            feature_stats[top_feature]
        )
        
        return {
            "type": anomaly_type,
            "primary_driver": top_feature,
            "direction": direction,
            "deviation_score": round(top_deviation, 2),
            "all_deviations": {k: round(v, 2) for k, v in deviations.items()},
            "confidence": "high" if top_deviation > 4.0 else "medium",
            "message": message
        }
    
    def _calculate_deviation(self, value: float, stats: Dict) -> float:
        """Calculate how many IQRs a value is from median."""
        median = stats['median']
        iqr = stats['iqr']
        
        if iqr == 0:
            return 0.0
        
        return abs(value - median) / iqr
    
    def _generate_message(self, feature: str, direction: str, 
                          value: float, stats: Dict) -> str:
        """Generate human-readable explanation message."""
        median = stats['median']
        
        templates = {
            'soh_percent': {
                'high': f"📊 Unusual battery capacity detected ({value:.1f}%). This can happen after a system update or battery calibration change.",
                'low': f"📉 Your battery capacity ({value:.1f}%) is lower than expected. This may indicate aging. Consider getting it checked."
            },
            'current_max_A': {
                'high': f"⚡ Power spike detected. Your phone drew more power than usual. Check your charger and cable."
            },
            'duration_seconds': {
                'high': f"⏱️ Your battery is taking longer to charge than expected ({value/3600:.1f} hours). This could be normal if you're using a slow charger.",
                'low': f"⚡ Your battery charged faster than usual. If this happens often, your battery capacity may have decreased."
            },
            'voltage_min_V': {
                'low': f"🪫 Battery drained unusually low ({value:.2f}V). Try to charge before your phone drops below 20% to preserve battery health."
            },
            'coulombic_efficiency': {
                'low': f"🔌 Your battery isn't charging efficiently. This usually means a loose cable or faulty charger. Try a different one."
            },
            'current_cv': {
                'high': f"🔋 Your charging current is fluctuating. This often happens with old or damaged cables."
            },
            'avg_power_W': {
                'high': f"📈 Unusually high power usage detected. Something may be running in the background.",
                'low': f"📉 Your phone is using less power than usual. This is fine if your phone was idle."
            }
        }
        
        if feature in templates and direction in templates[feature]:
            return templates[feature][direction]
        
        # Generic fallback
        # Generic fallback (around line 180)
        return f"We noticed something unusual with your battery's {feature}. This is usually temporary and nothing to worry about."
    
    def get_required_features(self) -> List[str]:
        """Return the list of features required for prediction."""
        return self.feature_columns.copy()
    
    def is_ready(self) -> bool:
        """Check if the model is loaded and ready."""
        return (self.model is not None and 
                self.scaler is not None and 
                self.feature_columns is not None and
                self.classifier is not None)


# Singleton instance
_anomaly_detector: Optional[AnomalyDetector] = None


def get_anomaly_detector() -> AnomalyDetector:
    """Get or create the anomaly detector singleton."""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector()
    return _anomaly_detector