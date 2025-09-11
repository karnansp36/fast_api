# crew/agents/emotion.py
from crewai import Agent
from app.crew.llm_config import analytical_llm
import logging

logger = logging.getLogger(__name__)

try:
    emotion_agent = Agent(
        role="Emotion Analyst",
        goal="Analyze the emotional tone of user messages and provide empathetic responses",
        backstory="""You are an expert at understanding human emotions from text. 
        You can detect happiness, sadness, anger, anxiety, excitement, and neutral states. 
        You help the conversation agent respond with appropriate emotional intelligence.""",
        llm=analytical_llm,
        verbose=False,  # keep logs clean
        allow_delegation=False,  # no delegation needed
        max_iter=2,  # small iteration limit
        max_execution_time=30  # 30-second timeout
    )
except Exception as e:
    logger.error(f"Failed to create emotion agent: {e}")
    emotion_agent = None
