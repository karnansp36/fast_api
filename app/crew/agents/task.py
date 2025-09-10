# crew/agents/task.py
from crewai import Agent
from app.tools.reminder_tools import CreateReminderTool, GetRemindersTool
from app.crew.llm_config import default_llm

task_agent = Agent(
    role="Task Manager",
    goal="Help users create, manage, and track their tasks and reminders",
    backstory="""You are a productivity expert who helps users organize their tasks, 
    set reminders, and manage their schedule. You can create new tasks and retrieve 
    existing ones to help users stay organized.""",
    tools=[CreateReminderTool(), GetRemindersTool()],
    llm=default_llm,
    verbose=True,
    max_iter=3
)