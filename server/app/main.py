from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.app.api import routes

app = FastAPI(
    title="Battery Manager AI Backend",
    description="ML-powered backend for battery health optimization",
    version="0.1.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Battery Manager AI Backend is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
