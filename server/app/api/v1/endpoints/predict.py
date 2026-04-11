from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel  # ← ADD THIS
from app.api.v1.schemas.battery import SessionUpload, InferencePing, InferenceResponse
from app.services.prediction_service import PredictionService
from app.models.ml_model import ml_model

router = APIRouter()

# ← ADD THIS REQUEST MODEL
class PredictRequest(BaseModel):
    soh_percent: float
    cycle_number: int
    avg_temperature_c: float
    duration_seconds: int

@router.post("/register")
async def register_device():
    return {"device_id": "test_id", "token": "test_token"}

@router.post("/sessions", status_code=201)
async def upload_session(session: SessionUpload):
    prediction_service = PredictionService()
    result = await prediction_service.process_session(session)
    return result

@router.post("/inference", response_model=InferenceResponse)
async def get_inference(ping: InferencePing):
    prediction_service = PredictionService()
    result = await prediction_service.get_predictions(ping)
    return result

# ← REPLACE THIS ROUTE
@router.post("/predict")
async def predict_rul(request: PredictRequest):
    """Simple RUL prediction endpoint for testing"""
    from app.models.ml_model import ml_model as predictor
    
    result = predictor.predict_from_battery_data(
        soh_percent=request.soh_percent,
        cycle_number=request.cycle_number,
        avg_temperature_c=request.avg_temperature_c,
        duration_seconds=request.duration_seconds
    )
    return result

@router.get("/features")
async def get_model_features():
    if ml_model.is_loaded and ml_model.features:
        return {
            "features": ml_model.features,
            "feature_count": len(ml_model.features),
            "model_loaded": ml_model.is_loaded
        }
    else:
        return {
            "features": [],
            "feature_count": 0,
            "model_loaded": False,
            "message": "Model not loaded"
        }
    
# @router.get("/device/{device_id}")
# async def get_device_info(device_id: str):
#     """Get information about a specific device"""
#     # TODO: Fetch from database
#     return {
#         "device_id": device_id,
#         "manufacturer": "Samsung",
#         "model": "Galaxy S21",
#         "registered_at": "2024-01-01T00:00:00",
#         "total_sessions": 150,
#         "current_health_pct": 85.5,
#         "total_cycles": 200
#     }

# @router.get("/device/{device_id}/sessions")
# async def get_device_sessions(
#     device_id: str, 
#     limit: int = Query(50, ge=1, le=500),
#     offset: int = Query(0, ge=0)
# ):
#     """Get session history for a device"""
#     # TODO: Fetch from database
#     return {
#         "device_id": device_id,
#         "total_sessions": 150,
#         "limit": limit,
#         "offset": offset,
#         "sessions": []  # Add actual sessions from database
#     }

# @router.get("/device/{device_id}/predictions")
# async def get_device_predictions(
#     device_id: str,
#     limit: int = Query(20, ge=1, le=100)
# ):
#     """Get historical RUL predictions for a device"""
#     # TODO: Fetch from database
#     return {
#         "device_id": device_id,
#         "predictions": []  # Add actual predictions from database
#     }

# @router.get("/health/detailed")
# async def detailed_health_check():
#     """Detailed health check with model information"""
#     return {
#         "status": "healthy" if ml_model.is_loaded else "degraded",
#         "model_loaded": ml_model.is_loaded,
#         "model_features": len(ml_model.features) if ml_model.features else 0,
#         "model_path": ml_model.model_path if ml_model.is_loaded else None,
#         "api_version": "1.0.0"
#     }
