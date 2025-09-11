# app/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    API_SHARED_SECRET: str = os.getenv("API_SHARED_SECRET", "dev-secret")
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"    
    # LiteLLM configuration
    LITELLM_MODEL: str = os.getenv("LITELLM_MODEL", "gemini/gemini-1.5-flash")
    
    class Config:
        env_file = ".env"

settings = Settings()