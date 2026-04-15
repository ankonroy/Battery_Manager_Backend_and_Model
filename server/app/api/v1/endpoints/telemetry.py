"""
Telemetry data ingestion endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.telemetry_service import TelemetryService
from app.api.v1.schemas.telemetry import (
    TelemetryRequest,
    TelemetryResponse,
    TelemetryStatsResponse,
)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post(
    "/ingest",
    response_model=TelemetryResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest battery telemetry",
    description="Save per-minute battery telemetry data to the database.",
)
async def ingest_telemetry(
    request: TelemetryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a single battery telemetry reading.
    
    Data is saved to the database asynchronously.
    """
    try:
        service = TelemetryService(db)
        
        # Save reading (could be moved to background task for high volume)
        await service.save_reading(request)
        
        return TelemetryResponse(
            status="accepted",
            timestamp=request.timestamp_utc,
            message="Telemetry data saved successfully",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save telemetry data: {str(e)}",
        )


@router.get(
    "/stats",
    response_model=TelemetryStatsResponse,
    summary="Get telemetry statistics",
    description="Get overall statistics about collected telemetry data.",
)
async def get_telemetry_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall telemetry statistics.
    """
    try:
        service = TelemetryService(db)
        stats = await service.get_stats()
        
        return TelemetryStatsResponse(
            total_readings=stats["total_readings"],
            unique_devices=stats["unique_devices"],
            first_reading=stats["first_reading"],
            last_reading=stats["last_reading"],
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get(
    "/devices/{device_id}",
    summary="Get device statistics",
    description="Get telemetry statistics for a specific device.",
)
async def get_device_stats(
    device_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for a specific device.
    """
    try:
        service = TelemetryService(db)
        stats = await service.get_device_stats(device_id)
        
        if stats["total_readings"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for device: {device_id}",
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device statistics: {str(e)}",
        )


@router.get(
    "/health",
    summary="Telemetry service health check",
    description="Check if telemetry service can connect to database.",
)
async def telemetry_health_check(
    db: AsyncSession = Depends(get_db),
):
    """
    Check if the telemetry service is healthy.
    """
    from app.database.connection import check_database_connection
    
    db_healthy = await check_database_connection()
    
    return {
        "service": "telemetry",
        "status": "healthy" if db_healthy else "unhealthy",
        "database_connected": db_healthy,
    }