from fastapi import APIRouter
from app.api.v1.endpoints import anomaly, inference, sessions

router = APIRouter()

router.include_router(anomaly.router)
router.include_router(inference.router)
router.include_router(sessions.router)