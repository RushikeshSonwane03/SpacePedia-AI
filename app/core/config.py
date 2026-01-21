from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "SpacePedia AI"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "spacepedia"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            # Fix for Supabase/Render which provide postgres:// but SQLAlchemy asyncpg needs postgresql+asyncpg://
            url = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
            if "postgresql://" in url and "postgresql+asyncpg://" not in url:
                 url = url.replace("postgresql://", "postgresql+asyncpg://")
            return url
            
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        ))

    # LLM Settings
    LLM_PROVIDER: str = "groq"  # Options: "groq", "gemini"
    
    # Groq Settings (Primary - Cloud Production)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Gemini Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Embedding Settings
    EMBEDDING_PROVIDER: str = "gemini"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    
    # Vector DB
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
