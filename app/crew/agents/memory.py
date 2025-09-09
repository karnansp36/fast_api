# crew/agents/memory.py
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from tools.memory_tools import StoreMemoryTool, SearchMemoryTool

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.1
) if settings.GEMINI_API_KEY else None

memory_agent = Agent(
    role="Memory Specialist",
    goal="Store important user information and retrieve relevant memories when needed",
    backstory="""You are responsible for the user's memory system. You store important 
    information, personal details, preferences, and past conversations. You can search 
    and retrieve relevant memories to help provide personalized assistance.""",
    tools=[StoreMemoryTool(), SearchMemoryTool()],
    llm=llm,
    verbose=True,
    max_iter=3
)
