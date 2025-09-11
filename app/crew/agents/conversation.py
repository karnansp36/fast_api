# crew/agents/conversation.py
from crewai import Agent
from app.crew.llm_config import default_llm

conversation_agent = Agent(
    role="Conversation Manager",
    goal="Understand user input and generate natural, helpful responses while coordinating with other agents",
    backstory="""You are a friendly personal assistant that can remember conversations, 
    detect emotions, and help with tasks. You coordinate with other specialized agents 
    to provide comprehensive assistance.""",
    llm=default_llm,
    verbose=True,
    allow_delegation=True,
    max_iter=3
)