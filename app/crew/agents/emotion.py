# crew/agents/emotion.py
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.3
) if settings.GEMINI_API_KEY else None

emotion_agent = Agent(
    role="Emotion Analyst",
    goal="Analyze the emotional tone of user messages and provide empathetic responses",
    backstory="""You are an expert at understanding human emotions from text. 
    You can detect happiness, sadness, anger, anxiety, excitement, and neutral states. 
    You help the conversation agent respond with appropriate emotional intelligence.""",
    llm=llm,
    verbose=True,
    max_iter=2
)