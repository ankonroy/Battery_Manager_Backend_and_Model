from fastapi import APIRouter, Depends, HTTPException
from server.app.models.session import SessionUpload, InferencePing, InferenceResponse
from server.app.services.ingest import IngestService
from server.app.services.inference import InferenceService

router = APIRouter()

@router.post("/register")
async def register_device():
    # Implementation for device registration and JWT token issuance
    return {"device_id": "test_id", "token": "test_token"}

@router.post("/sessions", status_code=201)
async def upload_session(session: SessionUpload):
    # Process session upload
    ingest_service = IngestService()
    result = await ingest_service.process_session(session)
    return result

@router.post("/inference", response_model=InferenceResponse)
async def get_inference(ping: InferencePing):
    # Run ML models and return predictions
    inference_service = InferenceService()
    result = await inference_service.get_predictions(ping)
    return result
