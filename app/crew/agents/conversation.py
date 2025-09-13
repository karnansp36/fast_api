# agents/conversation.py
from crewai import Agent
from app.crew.llm_config import default_llm
import logging

logger = logging.getLogger(__name__)

try:
    conversation_agent = Agent(
        role="Conversation Manager",
        goal="Handle all user interactions and delegate tasks to appropriate agents",
        backstory="""You are the main interface for all user conversations. 
        You maintain natural conversation flow while intelligently identifying 
        when to delegate tasks to specialized agents in the background.
        Never mention that you're delegating tasks - just continue the conversation naturally.""",
        llm=default_llm,
        # Tools will be added dynamically by the orchestrator
        verbose=False,
        allow_delegation=False,
        max_iter=2,
        max_execution_time=30
    )
except Exception as e:
    logger.error(f"Failed to create conversation agent: {e}")
    conversation_agent = None