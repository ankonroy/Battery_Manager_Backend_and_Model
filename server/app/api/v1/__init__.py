"""
API v1 Router.
Aggregates all endpoint routers for version 1 of the API.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import predict, anomaly

router = APIRouter()

# Register existing endpoints
router.include_router(predict.router)
router.include_router(anomaly.router)

# Future endpoints can be added here:
# from app.api.v1.endpoints import inference, sessions
# router.include_router(inference.router)
# router.include_router(sessions.router)