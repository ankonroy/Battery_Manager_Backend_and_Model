from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import predict
from app.models.ml_model import ml_model

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
    """Load ML model when API starts"""
    print("Loading battery RUL model...")
    # Model loads automatically when ml_model is imported
    if ml_model.is_loaded:
        print("✅ Model loaded successfully")
    else:
        print("⚠️ Model not loaded, using fallback predictions")

# Include routes
app.include_router(predict.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Battery Manager AI Backend is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if ml_model.is_loaded else "degraded",
        "model_loaded": ml_model.is_loaded
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)