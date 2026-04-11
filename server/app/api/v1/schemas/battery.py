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
from typing import List, Optional
from datetime import datetime

class SessionUpload(BaseModel):
    # Device identity
    device_id: str
    manufacturer: str
    model: str
    design_capacity_mah: int

    # Session summary
    session_type: str # "charge" or "discharge"
    start_soc_pct: int
    end_soc_pct: int
    duration_minutes: float
    mah_transferred: float
    session_timestamp_utc: datetime

    # Session quality signals
    avg_current_ma: float
    avg_temp_c: float
    max_temp_c: float
    avg_voltage_v: float
    current_cv: float
    capacity_estimate_mah: float
    health_pct: float
    cycle_count: int
    stress_score: float

    # Downsampled curve data
    voltage_samples: List[float] = Field(..., min_items=20, max_items=20)
    current_samples: List[float] = Field(..., min_items=20, max_items=20)

class InferencePing(BaseModel):
    device_id: str
    current_health_pct: float
    current_cycle_count: int
    current_capacity_mah: float
    sessions_last_30_days: int
    current_soc_pct: int
    current_drain_rate_mah_hr: float
    local_hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)

class RULResponse(BaseModel):
    cycles_median: int
    cycles_low: int
    cycles_high: int
    months_estimate: float
    top_degradation_driver: str

class AnomalyResponse(BaseModel):
    score: float
    type: str
    explanation: Optional[str] = None

class TTEResponse(BaseModel):
    tte_minutes_ml: int
    predicted_soc_in_2h: int
    predicted_soc_in_4h: int

class ChargingAdviceResponse(BaseModel):
    habit_archetype: str
    longevity_score: int
    top_recommendation: str
    projected_health_12mo_current: float
    projected_health_12mo_improved: float

class InferenceResponse(BaseModel):
    rul: RULResponse
    anomaly: AnomalyResponse
    time_to_empty: TTEResponse
    charging_advice: ChargingAdviceResponse
