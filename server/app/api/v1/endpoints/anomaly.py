"""
Cycle-Level Anomaly Detection Endpoints.
Uses Isolation Forest model to detect anomalous battery cycles.
"""
from fastapi import APIRouter, HTTPException, status
from app.api.v1.schemas.battery import CycleAnomalyRequest, CycleAnomalyResponse
from app.models.anomaly import get_anomaly_detector

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


@router.post(
    "/detect",
    response_model=CycleAnomalyResponse,
    summary="Detect cycle-level anomalies",
    description="""
    Analyzes a single battery cycle and determines if it's anomalous.
    
    The model uses an Isolation Forest trained on CALCE battery cycling data
    to identify unusual patterns in 11 key features.
    
    If an anomaly is detected, returns a detailed explanation.
    """
)
async def detect_anomaly(request: CycleAnomalyRequest):
    """
    Detect if a battery cycle is anomalous and explain why.
    
    This endpoint uses an Isolation Forest model trained on CALCE battery
    cycling data to identify unusual battery behavior.
    """
    try:
        detector = get_anomaly_detector()
        
        if not detector.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Anomaly detection model is not loaded."
            )
        
        # Convert request to dict
        cycle_data = request.model_dump()
        
        # Get prediction
        result = detector.predict(cycle_data)
        
        return CycleAnomalyResponse(**result)
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model files not found: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get(
    "/features",
    summary="Get required features",
    description="Returns the list of features required for anomaly detection."
)
async def get_required_features():
    """
    Get the list of features required for anomaly detection.
    """
    try:
        detector = get_anomaly_detector()
        return {
            "required_features": detector.get_required_features(),
            "count": len(detector.feature_columns)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not retrieve features: {str(e)}"
        )

@router.get(
    "/health",
    summary="Health check",
    description="Check if the anomaly detection model is loaded and ready."
)
async def health_check():
    """Check if the anomaly detection model is loaded."""
    try:
        detector = get_anomaly_detector()
        return {
            "status": "healthy",
            "model_loaded": detector.is_ready(),
            "features_count": len(detector.feature_columns) if detector.feature_columns else 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# In server/app/api/v1/endpoints/anomaly.py

@router.post("/check", response_model=dict)
async def check_battery_anomaly(request: CycleAnomalyRequest):
    """
    Simple endpoint for app integration.
    Returns only whether an anomaly is detected.
    """
    try:
        detector = get_anomaly_detector()
        cycle_data = request.model_dump()
        result = detector.predict(cycle_data)
        
        # Simple response for app
        return {
            "is_anomaly": result["is_anomaly"],
            "confidence": result["confidence"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))