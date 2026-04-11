from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AnomalyRequest(BaseModel):
    """Request schema for anomaly detection."""
    cycle_number: int = Field(..., description="Current cycle count")
    current_mean_A: float = Field(..., description="Average current in Amperes")
    voltage_mean_V: float = Field(..., description="Average voltage in Volts")
    charge_capacity_Ah: float = Field(..., description="Charge capacity in Ah")
    discharge_capacity_Ah: float = Field(..., description="Discharge capacity in Ah")
    duration_seconds: float = Field(..., description="Cycle duration in seconds")
    soh_percent: float = Field(..., description="State of Health percentage")
    current_cv: float = Field(..., description="Current coefficient of variation")
    avg_power_W: float = Field(..., description="Average power in Watts")
    coulombic_efficiency: float = Field(..., description="Coulombic efficiency (0-1)")
    source_file_encoded: int = Field(..., description="Session identifier (encoded)")


class AnomalyExplanation(BaseModel):
    """Explanation for an anomaly."""
    type: str = Field(..., description="Type of anomaly detected")
    primary_driver: str = Field(..., description="Main feature causing the anomaly")
    direction: str = Field(..., description="Direction of deviation (high/low)")
    deviation_score: float = Field(..., description="How far from normal (in IQR units)")
    all_deviations: Optional[Dict[str, float]] = Field(None, description="All significant deviations")
    confidence: str = Field(..., description="Confidence level (high/medium/low)")
    message: str = Field(..., description="Human-readable explanation")


class AnomalyResponse(BaseModel):
    """Response schema for anomaly detection."""
    is_anomaly: bool = Field(..., description="Whether the cycle is anomalous")
    anomaly_score: float = Field(..., description="Anomaly score (lower = more anomalous)")
    confidence: str = Field(..., description="Overall confidence in the prediction")
    explanation: Optional[AnomalyExplanation] = Field(None, description="Explanation if anomalous")