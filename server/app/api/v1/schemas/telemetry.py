"""
Pydantic schemas for telemetry data validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TelemetryRequest(BaseModel):
    """Request schema for per-minute battery telemetry."""
    
    device_id: str = Field(..., description="Unique device identifier (Android ID)")
    timestamp_utc: datetime = Field(..., description="UTC timestamp of reading")
    session_id: Optional[str] = Field(None, description="Current monitoring session ID")
    
    # Battery state
    level_percent: int = Field(..., ge=0, le=100, description="Battery level percentage")
    temperature_c: float = Field(..., description="Battery temperature in Celsius")
    voltage_v: float = Field(..., ge=0, description="Battery voltage")
    current_ma: int = Field(..., description="Current flow in mA (negative = discharging)")
    is_charging: bool = Field(..., description="Whether battery is charging")
    power_mw: float = Field(..., ge=0, description="Power in milliwatts")
    
    # Health metrics
    health_percent: float = Field(..., ge=0, le=100, description="Battery health percentage")
    cycle_count: int = Field(..., ge=0, description="Number of charge cycles")
    actual_capacity_mah: float = Field(..., ge=0, description="Estimated full capacity in mAh")
    stress_score: float = Field(..., ge=0, le=100, description="Current stress score")
    
    # Device info
    manufacturer: str = Field(..., description="Device manufacturer")
    model: str = Field(..., description="Device model")
    
    # Foreground app (optional)
    foreground_package: Optional[str] = Field(None, description="Foreground app package name")
    foreground_app: Optional[str] = Field(None, description="Foreground app display name")


class TelemetryResponse(BaseModel):
    """Response schema for telemetry ingestion."""
    
    status: str = Field(..., description="Status of the request")
    timestamp: datetime = Field(..., description="Timestamp of the ingested reading")
    message: Optional[str] = Field(None, description="Additional information")


class TelemetryStatsResponse(BaseModel):
    """Response schema for telemetry statistics."""
    
    total_readings: int = Field(..., description="Total number of readings in database")
    unique_devices: int = Field(..., description="Number of unique devices")
    first_reading: Optional[datetime] = Field(None, description="Timestamp of oldest reading")
    last_reading: Optional[datetime] = Field(None, description="Timestamp of newest reading")