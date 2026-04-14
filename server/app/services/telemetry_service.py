"""
Service layer for telemetry data operations.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.schemas import BatteryTelemetryRaw
from app.api.v1.schemas.telemetry import TelemetryRequest


class TelemetryService:
    """Service for handling battery telemetry data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def save_reading(self, data: TelemetryRequest) -> BatteryTelemetryRaw:
        """
        Save a single battery telemetry reading to the database.
        """
        reading = BatteryTelemetryRaw(
            time=data.timestamp_utc,
            device_id=data.device_id,
            session_id=data.session_id,
            level_percent=data.level_percent,
            temperature_c=data.temperature_c,
            voltage_v=data.voltage_v,
            current_ma=data.current_ma,
            is_charging=data.is_charging,
            power_mw=data.power_mw,
            health_percent=data.health_percent,
            cycle_count=data.cycle_count,
            actual_capacity_mah=data.actual_capacity_mah,
            stress_score=data.stress_score,
            manufacturer=data.manufacturer,
            model=data.model,
            foreground_package=data.foreground_package,
            foreground_app=data.foreground_app,
        )
        
        self.db.add(reading)
        await self.db.commit()
        await self.db.refresh(reading)
        
        return reading
    
    async def get_stats(self) -> dict:
        """
        Get overall telemetry statistics.
        """
        # Count total readings
        total_result = await self.db.execute(
            select(func.count()).select_from(BatteryTelemetryRaw)
        )
        total_readings = total_result.scalar() or 0
        
        # Count unique devices
        devices_result = await self.db.execute(
            select(func.count(func.distinct(BatteryTelemetryRaw.device_id)))
        )
        unique_devices = devices_result.scalar() or 0
        
        # Get first and last reading timestamps
        first_result = await self.db.execute(
            select(BatteryTelemetryRaw.time)
            .order_by(BatteryTelemetryRaw.time.asc())
            .limit(1)
        )
        first_reading = first_result.scalar()
        
        last_result = await self.db.execute(
            select(BatteryTelemetryRaw.time)
            .order_by(BatteryTelemetryRaw.time.desc())
            .limit(1)
        )
        last_reading = last_result.scalar()
        
        return {
            "total_readings": total_readings,
            "unique_devices": unique_devices,
            "first_reading": first_reading,
            "last_reading": last_reading,
        }
    
    async def get_device_stats(self, device_id: str) -> dict:
        """
        Get statistics for a specific device.
        """
        # Count readings for this device
        count_result = await self.db.execute(
            select(func.count())
            .select_from(BatteryTelemetryRaw)
            .where(BatteryTelemetryRaw.device_id == device_id)
        )
        total_readings = count_result.scalar() or 0
        
        # Get first and last reading
        first_result = await self.db.execute(
            select(BatteryTelemetryRaw.time)
            .where(BatteryTelemetryRaw.device_id == device_id)
            .order_by(BatteryTelemetryRaw.time.asc())
            .limit(1)
        )
        first_reading = first_result.scalar()
        
        last_result = await self.db.execute(
            select(BatteryTelemetryRaw.time)
            .where(BatteryTelemetryRaw.device_id == device_id)
            .order_by(BatteryTelemetryRaw.time.desc())
            .limit(1)
        )
        last_reading = last_result.scalar()
        
        # Get latest health metrics
        latest_result = await self.db.execute(
            select(BatteryTelemetryRaw)
            .where(BatteryTelemetryRaw.device_id == device_id)
            .order_by(BatteryTelemetryRaw.time.desc())
            .limit(1)
        )
        latest = latest_result.scalar()
        
        return {
            "device_id": device_id,
            "total_readings": total_readings,
            "first_reading": first_reading,
            "last_reading": last_reading,
            "latest_health_percent": latest.health_percent if latest else None,
            "latest_cycle_count": latest.cycle_count if latest else None,
            "manufacturer": latest.manufacturer if latest else None,
            "model": latest.model if latest else None,
        }