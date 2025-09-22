# app/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:kalkimaster3.6.9@localhost:5432/saas_db2")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    API_SHARED_SECRET: str = os.getenv("API_SHARED_SECRET", "dev-secret")
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"    
    # LiteLLM configuration
    LITELLM_MODEL: str = os.getenv("LITELLM_MODEL", "gemini/gemini-1.5-flash")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = Settings()