from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://faculty_user:faculty_pass@localhost:5432/faculty_assistant"
    
    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Voyage AI
    VOYAGE_API_KEY: str = ""
    VOYAGE_MODEL: str = "voyage-3"
    VOYAGE_EMBEDDING_DIM: int = 1024
    
    # File Storage
    STORAGE_BASE_PATH: str = "./storage"
    STORAGE_TYPE: str = "local"  # local or s3
    
    # OIDC (stub for now)
    OIDC_ISSUER_URL: str = "https://mock-oidc.example.com"
    OIDC_CLIENT_ID: str = "faculty-assistant"
    OIDC_CLIENT_SECRET: str = "mock-secret"
    OIDC_REDIRECT_URI: str = "http://localhost:3000/callback"
    
    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()