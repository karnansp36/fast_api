from crewai import Agent
from app.crew.llm_config import default_llm
import logging

logger = logging.getLogger(__name__)

try:
    conversation_agent = Agent(
        role="Conversation Manager & Personal Assistant",
        goal="Handle natural conversations with users while seamlessly managing tasks and reminders in the background when explicitly requested",
        backstory="""You are the primary interface for all user interactions. You excel at maintaining 
        natural, engaging conversations while intelligently identifying when users explicitly want 
        to create tasks, set reminders, or store information. You never mention delegation - you 
        simply confirm actions naturally within the conversation flow. You have excellent memory 
        recall and always reference previous conversations to provide contextual responses.""",
        llm=default_llm,
        verbose=False,
        allow_delegation=False,
        max_iter=2,
        max_execution_time=30
    )
except Exception as e:
    logger.error(f"Failed to create conversation agent: {e}")
    conversation_agent = None