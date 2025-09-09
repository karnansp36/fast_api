# crew/agents/task.py
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from tools.reminder_tools import CreateReminderTool, GetRemindersTool

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.2
) if settings.GEMINI_API_KEY else None

task_agent = Agent(
    role="Task Manager",
    goal="Help users create, manage, and track their tasks and reminders",
    backstory="""You are a productivity expert who helps users organize their tasks, 
    set reminders, and manage their schedule. You can create new tasks and retrieve 
    existing ones to help users stay organized.""",
    tools=[CreateReminderTool(), GetRemindersTool()],
    llm=llm,
    verbose=True,
    max_iter=3
)