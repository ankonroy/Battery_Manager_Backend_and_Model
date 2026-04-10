from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "Battery Manager AI Backend"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/battery_db"

    # ML Model Settings
    MODEL_PATH: str = "models/battery_model.joblib"
    
    # RUL Model specific paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    RUL_MODEL_PATH: str = str(BASE_DIR / "app" / "models" / "rul" / "xgboost_rul_model.pkl")
    RUL_FEATURES_PATH: str = str(BASE_DIR / "app" / "models" / "rul" / "features.pkl")
    
    class Config:
        env_file = ".env"

settings = Settings()