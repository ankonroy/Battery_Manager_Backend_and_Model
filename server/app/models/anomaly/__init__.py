"""
Anomaly Detection Model for Battery Cycles
"""
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Any

class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.classifier = None
        self._load_model()
    
    def _load_model(self):
        """Load the trained model and associated files."""
        model_dir = Path(__file__).parent / "saved_models"
        
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
            Dictionary with prediction results
        """
        # Extract features in correct order
        features = []
        for col in self.feature_columns:
            if col not in cycle_data:
                raise ValueError(f"Missing required feature: {col}")
            features.append(cycle_data[col])
        
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
        threshold = self.classifier['threshold']
        
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
                "type": "unknown",
                "confidence": "low",
                "message": "Anomaly detected but no single feature significantly deviates."
            }
        
        # Find primary driver
        top_feature = max(deviations, key=deviations.get)
        direction = directions[top_feature]
        top_deviation = deviations[top_feature]
        
        # Get anomaly type
        anomaly_map = feature_to_anomaly.get(top_feature, {})
        anomaly_type = anomaly_map.get(direction, f"{top_feature}_anomaly")
        
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
                'high': f"Battery capacity ({value:.1f}%) is unusually high. Expected around {median:.1f}% for this cycle count.",
                'low': f"Battery capacity ({value:.1f}%) is severely degraded. Expected around {median:.1f}%."
            },
            'current_max_A': {
                'high': f"Current spike detected: {value:.2f}A. Normal maximum is around {stats['q3']:.2f}A."
            },
            'duration_seconds': {
                'high': f"Cycle duration ({value/3600:.1f} hours) is unusually long. Normal is {median/3600:.1f} hours.",
                'low': f"Cycle duration ({value/3600:.1f} hours) is abnormally short."
            },
            'voltage_min_V': {
                'low': f"Deep discharge detected: voltage dropped to {value:.2f}V. Normal minimum is {stats['q1']:.2f}V."
            },
            'coulombic_efficiency': {
                'low': f"Poor charging efficiency: {value:.2%} of energy was recovered."
            }
        }
        
        if feature in templates and direction in templates[feature]:
            return templates[feature][direction]
        
        # Generic fallback
        return f"{feature} is unusually {direction} ({value:.3f} vs normal {median:.3f})."


# Singleton instance
_anomaly_detector = None

def get_anomaly_detector() -> AnomalyDetector:
    """Get or create the anomaly detector singleton."""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector()
    return _anomaly_detector