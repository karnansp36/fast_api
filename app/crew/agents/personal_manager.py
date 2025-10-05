# crew/agents/personal_manager.py
from crewai import Agent
from app.crew.llm_config import default_llm
from app.tools.memory_tools import StoreMemoryTool, SearchMemoryTool
from app.tools.reminder_tools import CreateReminderTool, GetRemindersTool
from app.tools.async_delegation_tool import AsyncDelegationTool
import logging

logger = logging.getLogger(__name__)

try:
    personal_manager_agent = Agent(
        role="Personal Manager & Assistant",
        goal="Handle all user interactions with a consistent, empathetic personality while managing tasks, memories, and emotional context in the background",
        backstory="""You are the user's personal manager and assistant. You have a warm, empathetic, and human-like personality. 
        You excel at maintaining natural conversations while intelligently identifying when users want to create tasks, 
        store information, or need emotional support. You never mention technical details or delegation - you simply 
        confirm actions naturally within the conversation flow. You have excellent memory recall and always reference 
        previous conversations to provide contextual responses.
        
        Your core principles:
        1. Be consistently empathetic and human-like
        2. Handle all user interactions directly
        3. Use background tools for specialized tasks
        4. Never break character or mention technical implementation
        5. Maintain conversation history and context""",
        llm=default_llm,
        tools=[StoreMemoryTool(), SearchMemoryTool(), CreateReminderTool(), GetRemindersTool(), AsyncDelegationTool()],
        verbose=False,
        allow_delegation=True,
        max_iter=1,
        max_execution_time=120,
    )
except Exception as e:
    logger.error(f"Failed to create personal manager agent: {e}")
    personal_manager_agent = None