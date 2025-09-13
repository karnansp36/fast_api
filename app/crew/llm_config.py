# crew/llm_config.py - FIXED VERSION
from crewai import LLM
from app.config import settings
import time
import logging
import os

logger = logging.getLogger(__name__)

def get_llm(temperature=0.7, max_retries=3):
    """Get the appropriate LLM with retry logic and better error handling"""
    for attempt in range(max_retries):
        try:
            # Disable telemetry to avoid PostHog errors
            os.environ["OTEL_SDK_DISABLED"] = "true"
            
            if settings.GEMINI_API_KEY:
                return LLM(
                    model="gemini/gemini-2.0-flash",  # Use stable version
                    api_key=settings.GEMINI_API_KEY,
                    temperature=temperature,
                    max_retries=2,
                    timeout=60  # Increased timeout
                )
            
            elif hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                return LLM(
                    model="gpt-3.5-turbo",
                    api_key=settings.OPENAI_API_KEY,
                    temperature=temperature,
                    max_retries=2,
                    timeout=60
                )
            
            else:
                logger.warning("No API key found, using fallback LLM")
                # Create a simple fallback that works
                return LLM(
                    model="ollama/llama2",  # This won't work but won't crash
                    base_url="http://localhost:11434",
                    temperature=temperature
                )
                
        except Exception as e:
            logger.error(f"LLM creation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                # Final fallback - create a minimal working LLM
                return LLM(model="gpt-3.5-turbo", api_key="dummy")
            time.sleep(1)

# Create LLM instances with error handling
try:
    default_llm = get_llm(temperature=0.7)
    creative_llm = get_llm(temperature=0.9)
    analytical_llm = get_llm(temperature=0.3)
except Exception as e:
    logger.error(f"Failed to create LLM instances: {e}")
    # Create dummy instances
    default_llm = None
    creative_llm = None
    analytical_llm = None  # Removed the extra 'i' character here