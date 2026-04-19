"""Pydantic schemas for API requests and responses."""
from app.api.v1.schemas.battery import (
    AnomalyRequest,
    AnomalyResponse,
    AnomalyExplanation,
    CycleAnomalyRequest,
    CycleAnomalyResponse,
    CycleAnomalyExplanation,
    SessionUpload,
    InferencePing,
    InferenceResponse,
    RULResponse,
    TTEResponse,
    ChargingAdviceResponse,
)
from app.api.v1.schemas.telemetry import (
    TelemetryRequest,
    TelemetryResponse,
    TelemetryStatsResponse,
)
from app.api.v1.schemas.advice import (
    AdviceRequest,
    AdviceResponse,
    FeatureAdviceRequest,
    AutoAdviceRequest,
    AutoAdviceResponse,
    AdviceHealthResponse,
)

__all__ = [
    # Anomaly schemas
    "AnomalyRequest",
    "AnomalyResponse",
    "AnomalyExplanation",
    "CycleAnomalyRequest",
    "CycleAnomalyResponse",
    "CycleAnomalyExplanation",
    # Inference schemas
    "SessionUpload",
    "InferencePing",
    "InferenceResponse",
    "RULResponse",
    "TTEResponse",
    "ChargingAdviceResponse",
    # Telemetry schemas
    "TelemetryRequest",
    "TelemetryResponse",
    "TelemetryStatsResponse",
    # Advice schemas
    "AdviceRequest",
    "AdviceResponse",
    "FeatureAdviceRequest",
    "AutoAdviceRequest",
    "AutoAdviceResponse",
    "AdviceHealthResponse",
]