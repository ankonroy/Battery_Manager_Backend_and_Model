from fastapi import APIRouter, HTTPException
from app.api.v1.schemas.battery import AnomalyRequest, AnomalyResponse
from app.models.anomaly import get_anomaly_detector

router = APIRouter(prefix="/anomaly", tags=["anomaly"])


@router.post("/detect", response_model=AnomalyResponse)
async def detect_anomaly(request: AnomalyRequest):
    """
    Detect if a battery cycle is anomalous and explain why.
    
    This endpoint uses an Isolation Forest model trained on CALCE battery
    cycling data to identify unusual battery behavior.
    """
    try:
        detector = get_anomaly_detector()
        
        # Convert request to dict
        cycle_data = request.model_dump()
        
        # Get prediction
        result = detector.predict(cycle_data)
        
        return AnomalyResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/features")
async def get_required_features():
    """
    Get the list of features required for anomaly detection.
    """
    detector = get_anomaly_detector()
    return {
        "required_features": detector.feature_columns,
        "count": len(detector.feature_columns)
    }


@router.get("/health")
async def health_check():
    """Check if the anomaly detection model is loaded."""
    try:
        detector = get_anomaly_detector()
        return {
            "status": "healthy",
            "model_loaded": detector.model is not None,
            "features_count": len(detector.feature_columns)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }