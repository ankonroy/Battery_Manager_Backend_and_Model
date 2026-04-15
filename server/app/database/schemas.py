"""
SQLAlchemy models for battery telemetry data.
"""
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    String,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP

from app.database.connection import Base


class BatteryTelemetryRaw(Base):
    """Raw per-minute battery telemetry."""
    
    __tablename__ = "battery_telemetry_raw"
    __table_args__ = (
        PrimaryKeyConstraint("time", "device_id"),
        {"schema": "battery_data"}
    )
    
    time = Column(TIMESTAMP(timezone=True), nullable=False)
    device_id = Column(String(64), nullable=False)
    session_id = Column(String(128), nullable=True)
    
    # Battery state
    level_percent = Column(Integer)
    temperature_c = Column(Float)
    voltage_v = Column(Float)
    current_ma = Column(Integer)
    is_charging = Column(Boolean)
    power_mw = Column(Float)
    
    # Health metrics
    health_percent = Column(Float)
    cycle_count = Column(Integer)
    actual_capacity_mah = Column(Float)
    stress_score = Column(Float)
    
    # Device info
    manufacturer = Column(String(64))
    model = Column(String(64))
    
    # Foreground app
    foreground_package = Column(String(256))
    foreground_app = Column(String(256))