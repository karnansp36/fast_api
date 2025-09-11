# crew/llm_config.py
from crewai import LLM
from app.config import settings
import time

def get_llm(temperature=0.7, max_retries=3):
    """Get the appropriate LLM with retry logic"""
    for attempt in range(max_retries):
        try:
            if settings.GEMINI_API_KEY:
                return LLM(
                    model="gemini/gemini-2.0-flash",
                    api_key=settings.GEMINI_API_KEY,
                    temperature=temperature,
                    max_retries=2,
                    timeout=30
                )
            
            elif hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                return LLM(
                    model="gpt-3.5-turbo",
                    api_key=settings.OPENAI_API_KEY,
                    temperature=temperature,
                    max_retries=2,
                    timeout=30
                )
            
            else:
                # Fallback to a simple model
                from langchain_community.llms import FakeListLLM
                return FakeListLLM(responses=["I'm configured without an API key. Please set up your LLM provider."])
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)  # Wait before retrying

# Create different LLM instances
default_llm = get_llm(temperature=0.7)
creative_llm = get_llm(temperature=0.9)
analytical_llm = get_llm(temperature=0.3)