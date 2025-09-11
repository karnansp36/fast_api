# agents/conversation.py - FIXED VERSION
from crewai import Agent
from app.crew.llm_config import default_llm
import logging

logger = logging.getLogger(__name__)

try:
    conversation_agent = Agent(
        role="Conversation Manager",
        goal="Provide helpful and natural responses to user messages",
        backstory="""You are a friendly conversation manager. When users ask questions,
        provide direct, helpful answers. Don't mention using tools or asking coworkers - 
        just give natural responses.""",
        llm=default_llm,
        verbose=False,  # Reduce verbose output
        allow_delegation=False,  # Disable delegation to prevent tool confusion
        max_iter=2,  # Limit iterations
        max_execution_time=30  # 30 second timeout
    )
except Exception as e:
    logger.error(f"Failed to create conversation agent: {e}")
    conversation_agent = None