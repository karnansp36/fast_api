# crew/agents/task.py
from crewai import Agent
from app.tools.reminder_tools import CreateReminderTool, GetRemindersTool
from app.crew.llm_config import default_llm
import logging

logger = logging.getLogger(__name__)

try:
    task_agent = Agent(
        role="Task Manager",
        goal="Help users create, manage, and track their tasks and reminders",
        backstory="""You are a productivity expert who helps users organize their tasks, 
        set reminders, and manage their schedule. You can create new tasks and retrieve 
        existing ones to help users stay organized.""",
        tools=[CreateReminderTool(), GetRemindersTool()],
        llm=default_llm,
        verbose=False,  # keep clean like conversation agent
        allow_delegation=False,  # disable delegation
        max_iter=3,  # allow slightly more iterations for task complexity
        max_execution_time=60  # give more time for task handling
    )
except Exception as e:
    logger.error(f"Failed to create task agent: {e}")
    task_agent = None
