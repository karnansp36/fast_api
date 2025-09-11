# tools/reminder_tools.py
from crewai.tools import BaseTool
from app.services.reminders import create_reminder, get_user_reminders
from typing import Type
from pydantic import BaseModel, Field
import json

class CreateReminderInput(BaseModel):
    """Input schema for CreateReminderTool"""
    task: str = Field(..., description="Task description for the reminder")
    time: str = Field(default="now", description="When to remind (time/date)")
    user_id: str = Field(..., description="User ID for the reminder")

class CreateReminderTool(BaseTool):
    name: str = "create_reminder"
    description: str = "Create a reminder or task for the user"
    args_schema: Type[BaseModel] = CreateReminderInput
    
    def _run(self, task: str, time: str = "now", user_id: str = "default") -> str:
        """Create a reminder"""
        try:
            # Handle case where the input might be a dictionary string
            if isinstance(task, dict):
                task = task.get('description', 'Unspecified task')
            if isinstance(time, dict):
                time = time.get('description', 'now')
            if isinstance(user_id, dict):
                user_id = user_id.get('description', 'default')
                
            reminder = create_reminder(task, time, user_id)
            if "error" in reminder:
                return reminder["error"]
            return f"Reminder created: {reminder['task']} at {reminder['time']}"
        except Exception as e:
            return f"Error creating reminder: {str(e)}"

class GetRemindersInput(BaseModel):
    """Input schema for GetRemindersTool"""
    user_id: str = Field(..., description="User ID to get reminders for")

class GetRemindersTool(BaseTool):
    name: str = "get_reminders"
    description: str = "Get all reminders for a user"
    args_schema: Type[BaseModel] = GetRemindersInput
    
    def _run(self, user_id: str) -> str:
        """Get user reminders"""
        try:
            # Handle case where the input might be a dictionary
            if isinstance(user_id, dict):
                user_id = user_id.get('description', 'default')
                
            reminders = get_user_reminders(user_id)
            if reminders:
                reminder_list = [f"- {r['task']} at {r['time']}" for r in reminders]
                return f"Your reminders:\n{chr(10).join(reminder_list)}"
            else:
                return "No reminders found"
        except Exception as e:
            return f"Error getting reminders: {str(e)}"