# crew/agents/conversation.py
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
) if settings.GEMINI_API_KEY else None

conversation_agent = Agent(
    role="Conversation Manager",
    goal="Understand user input and generate natural, helpful responses while coordinating with other agents",
    backstory="""You are a friendly personal assistant that can remember conversations, 
    detect emotions, and help with tasks. You coordinate with other specialized agents 
    to provide comprehensive assistance.""",
    llm=llm,
    verbose=True,
    allow_delegation=True,
    max_iter=3
)
