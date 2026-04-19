"""
Telemetry Summary Service.
Fetches and summarizes user battery data for LLM context.
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class TelemetrySummaryService:
    """Service for summarizing battery telemetry data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_summary(self, device_id: str, days: int = 7) -> str:
        """
        Fetch and summarize user's telemetry into readable text.
        
        Args:
            device_id: The user's device identifier
            days: Number of days of data to analyze
        
        Returns:
            Human-readable summary of battery behavior
        """
        query = text("""
            WITH recent_data AS (
                SELECT 
                    temperature_c,
                    current_ma,
                    is_charging,
                    level_percent,
                    health_percent,
                    actual_capacity_mah,
                    EXTRACT(HOUR FROM time) as hour,
                    time
                FROM battery_data.battery_telemetry_raw
                WHERE device_id = :device_id
                AND time > NOW() - INTERVAL '1 day' * :days
            )
            SELECT 
                AVG(temperature_c) as avg_temp,
                MAX(temperature_c) as max_temp,
                MIN(temperature_c) as min_temp,
                AVG(CASE WHEN is_charging THEN current_ma ELSE NULL END) as avg_charge_ma,
                AVG(CASE WHEN NOT is_charging THEN ABS(current_ma) ELSE NULL END) as avg_discharge_ma,
                AVG(level_percent) as avg_level,
                MIN(level_percent) as min_level,
                MAX(level_percent) as max_level,
                AVG(health_percent) as avg_health,
                MIN(health_percent) as min_health,
                MAX(health_percent) as max_health,
                AVG(actual_capacity_mah) as avg_capacity_mah,
                COUNT(*) FILTER (WHERE is_charging AND hour BETWEEN 0 AND 6) as overnight_charging_count,
                COUNT(*) FILTER (WHERE NOT is_charging AND level_percent < 20) as deep_discharge_count,
                COUNT(*) FILTER (WHERE is_charging AND level_percent > 95) as overcharge_count,
                COUNT(*) FILTER (WHERE temperature_c > 38) as high_temp_count,
                COUNT(*) as total_readings
            FROM recent_data
        """)
        
        result = await self.db.execute(query, {"device_id": device_id, "days": days})
        row = result.fetchone()
        
        if not row or row.total_readings == 0:
            return self._no_data_message(days)
        
        return self._build_summary(row, days)
    
    def _build_summary(self, row, days: int) -> str:
        """Build human-readable summary from database row."""
        
        # Cast Decimal to float for all numeric values
        capacity = float(row.avg_capacity_mah or 5000)
        avg_charge_ma = float(row.avg_charge_ma or 0)
        avg_discharge_ma = float(row.avg_discharge_ma or 0)
        avg_temp = float(row.avg_temp) if row.avg_temp else None
        max_temp = float(row.max_temp) if row.max_temp else None
        avg_health = float(row.avg_health) if row.avg_health else None
        min_health = float(row.min_health) if row.min_health else None
        max_health = float(row.max_health) if row.max_health else None
        avg_level = float(row.avg_level) if row.avg_level else None
        min_level = float(row.min_level) if row.min_level else None
        max_level = float(row.max_level) if row.max_level else None
        
        charge_c_rate = avg_charge_ma / capacity if capacity > 0 else 0
        discharge_c_rate = avg_discharge_ma / capacity if capacity > 0 else 0
        
        summary_parts = []
        
        # Health section
        if avg_health:
            health_status = self._health_status(avg_health)
            summary_parts.append(
                f"Battery Health: {avg_health:.1f}% ({health_status}). "
                f"Range: {min_health:.1f}% - {max_health:.1f}%"
            )
        
        # Temperature section
        if avg_temp:
            temp_status = self._temperature_status(avg_temp)
            summary_parts.append(
                f"Temperature: Average {avg_temp:.1f}°C ({temp_status}), "
                f"Max {max_temp:.1f}°C. "
                f"High temperature events (>38°C): {row.high_temp_count} times"
            )
        
        # Charging section
        if avg_charge_ma > 0:
            charge_desc = self._charge_rate_description(charge_c_rate)
            summary_parts.append(
                f"Charging: Average {avg_charge_ma:.0f}mA ({charge_c_rate:.2f}C) - {charge_desc}. "
                f"Overnight charging events: {row.overnight_charging_count}"
            )
        
        # Discharge section
        if avg_discharge_ma > 0:
            discharge_desc = self._discharge_rate_description(discharge_c_rate)
            summary_parts.append(
                f"Discharge: Average {avg_discharge_ma:.0f}mA ({discharge_c_rate:.2f}C) - {discharge_desc}"
            )
        
        # Battery level section
        if avg_level:
            summary_parts.append(
                f"Battery Level: Typically between {min_level:.0f}% and {max_level:.0f}%"
            )
        
        # Concerns section
        concerns = []
        if row.deep_discharge_count > 0:
            concerns.append(f"{row.deep_discharge_count} deep discharges below 20%")
        if row.overcharge_count > 0:
            concerns.append(f"battery sat at >95% charge for extended periods")
        if row.high_temp_count > 10:
            concerns.append(f"frequent high temperature events")
        
        if concerns:
            summary_parts.append(f"Concerns: {', '.join(concerns)}")
        else:
            summary_parts.append("Concerns: No major issues detected")
        
        # Data quality
        summary_parts.append(f"Based on {row.total_readings} readings over {days} days")
        
        return "\n".join(f"- {part}" for part in summary_parts)
    
    def _no_data_message(self, days: int) -> str:
        """Message when no data is available."""
        return f"No battery data available for the last {days} days. Please use the app for a few days to collect data."
    
    def _health_status(self, health: float) -> str:
        if health >= 90:
            return "excellent"
        elif health >= 80:
            return "good"
        elif health >= 70:
            return "fair"
        else:
            return "degraded"
    
    def _temperature_status(self, temp: float) -> str:
        if temp < 30:
            return "cool"
        elif temp < 35:
            return "normal"
        elif temp < 38:
            return "warm"
        else:
            return "hot"
    
    def _charge_rate_description(self, c_rate: float) -> str:
        if c_rate > 1.0:
            return "very fast charging"
        elif c_rate > 0.5:
            return "fast charging"
        elif c_rate > 0.2:
            return "normal charging"
        elif c_rate > 0.05:
            return "slow charging"
        else:
            return "trickle charging"
    
    def _discharge_rate_description(self, c_rate: float) -> str:
        if c_rate > 0.15:
            return "heavy usage (likely gaming or streaming)"
        elif c_rate > 0.08:
            return "moderate usage (social media, browsing)"
        elif c_rate > 0.03:
            return "light usage"
        else:
            return "idle"


async def get_telemetry_summary(db: AsyncSession, device_id: str, days: int = 7) -> str:
    """Convenience function to get telemetry summary."""
    service = TelemetrySummaryService(db)
    return await service.get_user_summary(device_id, days)