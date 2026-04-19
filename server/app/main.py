from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.models.ml_model import ml_model
from app.models.anomaly import get_anomaly_detector
from app.database.connection import check_database_connection

app = FastAPI(
    title="Battery Manager AI Backend",
    description="ML-powered backend for battery health optimization",
    version="0.1.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model on startup
@app.on_event("startup")
async def startup_event():
    """Load ML models and check database when API starts."""
    print("=" * 50)
    print("🚀 Starting Battery Manager AI Backend...")
    print("=" * 50)
    
    # Check database connection
    print("\n🗄️ Checking database connection...")
    db_connected = await check_database_connection()
    if db_connected:
        print("   ✅ Database connected successfully")
    else:
        print("   ⚠️ Database connection failed - telemetry will not work")
    
    # Load RUL model
    print("\n📊 Loading battery RUL model...")
    if ml_model.is_loaded:
        print("   ✅ RUL model loaded successfully")
    else:
        print("   ⚠️ RUL model not loaded, using fallback predictions")
    
    # Load Anomaly detection model
    print("\n🔍 Loading anomaly detection model...")
    try:
        anomaly_detector = get_anomaly_detector()
        if anomaly_detector.is_ready():
            print(f"   ✅ Anomaly model loaded with {len(anomaly_detector.feature_columns)} features")
        else:
            print("   ⚠️ Anomaly model not fully loaded")
    except Exception as e:
        print(f"   ❌ Failed to load anomaly model: {e}")
    
    print("\n" + "=" * 50)
    print("✨ Backend ready!")
    print("=" * 50)


# Include all API routes with /api prefix
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Battery Manager AI Backend is running",
        "endpoints": {
            "predict": "/api/v1/predict",
            "anomaly_detect": "/api/v1/anomaly/detect",
            "anomaly_features": "/api/v1/anomaly/features",
            "anomaly_health": "/api/v1/anomaly/health",
            "telemetry_ingest": "/api/v1/telemetry/ingest",
            "telemetry_stats": "/api/v1/telemetry/stats",
            "telemetry_health": "/api/v1/telemetry/health",
            "advice_ask": "/api/v1/advice/ask",
            "advice_auto": "/api/v1/advice/auto/{device_id}",
            "advice_health": "/api/v1/advice/health",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check for all models and database."""
    # Check database
    db_connected = await check_database_connection()
    
    # Check RUL model
    rul_loaded = ml_model.is_loaded
    
    # Check Anomaly model
    try:
        anomaly_detector = get_anomaly_detector()
        anomaly_loaded = anomaly_detector.is_ready()
        anomaly_features = len(anomaly_detector.feature_columns) if anomaly_loaded else 0
    except:
        anomaly_loaded = False
        anomaly_features = 0
    
    # Determine overall status
    if rul_loaded and anomaly_loaded and db_connected:
        status = "healthy"
    elif rul_loaded or anomaly_loaded:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return {
        "status": status,
        "database": {
            "connected": db_connected
        },
        "models": {
            "rul": {
                "loaded": rul_loaded
            },
            "anomaly": {
                "loaded": anomaly_loaded,
                "features_count": anomaly_features
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)