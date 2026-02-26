from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "EduAI Suite"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080
    
    # AI
    GOOGLE_API_KEY: str
    
    # Google OAuth (optional for now, needed in Day 3-4)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"    # ← This ignores any extra variables in .env
    }

settings = Settings()