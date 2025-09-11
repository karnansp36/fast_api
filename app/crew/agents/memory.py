# agents/memory.py - FIXED VERSION
from crewai import Agent
from app.crew.llm_config import default_llm
from app.tools.memory_tools import StoreMemoryTool, SearchMemoryTool
import logging

logger = logging.getLogger(__name__)

try:
    memory_agent = Agent(
        role="Memory Specialist",
        goal="Store and retrieve user information efficiently",
        backstory="""You are a memory specialist. When asked to store information,
        use the store_memory tool. When asked to search, use search_memory tool.
        Be concise and direct.""",
        llm=default_llm,
        tools=[StoreMemoryTool(), SearchMemoryTool()],
        verbose=False,
        allow_delegation=False,
        max_iter=2,
        max_execution_time=30
    )
except Exception as e:
    logger.error(f"Failed to create memory agent: {e}")
    memory_agent = None