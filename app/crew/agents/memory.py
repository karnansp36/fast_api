# crew/agents/memory.py
from crewai import Agent
from app.tools.memory_tools import StoreMemoryTool, SearchMemoryTool
from app.crew.llm_config import analytical_llm

memory_agent = Agent(
    role="Memory Specialist",
    goal="Store important user information and retrieve relevant memories when needed",
    backstory="""You are responsible for the user's memory system. You store important 
    information, personal details, preferences, and past conversations. You can search 
    and retrieve relevant memories to help provide personalized assistance.""",
    tools=[StoreMemoryTool(), SearchMemoryTool()],
    llm=analytical_llm,
    verbose=True,
    max_iter=3
)