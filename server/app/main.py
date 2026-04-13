from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import predict, anomaly  # Add anomaly import
from app.models.ml_model import ml_model
from app.models.anomaly import get_anomaly_detector  # Add this import

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
    """Load ML models when API starts."""
    print("=" * 50)
    print("🚀 Starting Battery Manager AI Backend...")
    print("=" * 50)
    
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


# Include routes
app.include_router(predict.router, prefix="/api/v1")
app.include_router(anomaly.router, prefix="/api/v1")  # Add anomaly router


@app.get("/")
async def root():
    return {
        "message": "Battery Manager AI Backend is running",
        "endpoints": {
            "predict": "/api/v1/predict",
            "anomaly": "/api/v1/anomaly/detect",
            "anomaly_features": "/api/v1/anomaly/features",
            "anomaly_health": "/api/v1/anomaly/health",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check for all models."""
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
    if rul_loaded and anomaly_loaded:
        status = "healthy"
    elif rul_loaded or anomaly_loaded:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return {
        "status": status,
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