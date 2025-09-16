# tools/reminder_tools.py
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from app.services.reminders import create_reminder, get_user_reminders
from app.core.db import AsyncSessionLocal
import asyncio
import logging

logger = logging.getLogger(__name__)

class CreateReminderInput(BaseModel):
    """Input schema for CreateReminderTool"""
    task: str = Field(..., description="The task or reminder to create")
    time: str = Field("now", description="When the reminder should be scheduled (ISO format or 'now')")
    user_id: str = Field(..., description="User ID for the reminder")

class CreateReminderTool(BaseTool):
    name: str = "create_reminder"
    description: str = "Create a new task or reminder for the user"
    args_schema: Type[BaseModel] = CreateReminderInput

    def _run(self, task: str, time: str = "now", user_id: str = "default") -> str:
        """Create a reminder synchronously"""
        try:
            # Clean inputs
            if isinstance(task, dict):
                task = str(task.get('description', ''))
            if isinstance(time, dict):
                time = str(time.get('description', 'now'))
            if isinstance(user_id, dict):
                user_id = str(user_id.get('description', 'default'))
                
            task = str(task).strip()
            time = str(time).strip()
            user_id = str(user_id).strip()
            
            if not task:
                return "Error: No task provided"
            
            logger.info(f"Creating reminder for user {user_id}: {task[:50]}...")
            
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Create reminder
            async def create_reminder_async():
                async with AsyncSessionLocal() as db:
                    return await create_reminder(task, time, user_id, db)
            
            result = loop.run_until_complete(create_reminder_async())
            
            if "error" in result:
                return f"Error creating reminder: {result['error']}"
            else:
                return f"Reminder created: {result['task']} (scheduled for {result['time']})"
                
        except Exception as e:
            error_msg = f"Failed to create reminder: {str(e)}"
            logger.error(error_msg)
            return error_msg

class GetRemindersInput(BaseModel):
    """Input schema for GetRemindersTool"""
    user_id: str = Field(..., description="User ID to get reminders for")

class GetRemindersTool(BaseTool):
    name: str = "get_reminders"
    description: str = "Get all current tasks and reminders for a user"
    args_schema: Type[BaseModel] = GetRemindersInput

    def _run(self, user_id: str) -> str:
        """Get reminders synchronously"""
        try:
            # Clean input
            if isinstance(user_id, dict):
                user_id = str(user_id.get('description', 'default'))
                
            user_id = str(user_id).strip()
            
            logger.info(f"Getting reminders for user {user_id}")
            
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Get reminders
            async def get_reminders_async():
                async with AsyncSessionLocal() as db:
                    return await get_user_reminders(user_id, db)
            
            reminders = loop.run_until_complete(get_reminders_async())
            
            if reminders and "error" in reminders[0]:
                return f"Error getting reminders: {reminders[0]['error']}"
            elif reminders:
                reminder_list = []
                for rem in reminders[:5]:  # Limit to 5 most recent
                    status = f" ({rem['status']})" if rem.get('status') else ""
                    reminder_list.append(f"- {rem['task']}{status}")
                
                return f"Found {len(reminders)} reminders:\n" + "\n".join(reminder_list)
            else:
                return "No reminders found"
                
        except Exception as e:
            error_msg = f"Failed to get reminders: {str(e)}"
            logger.error(error_msg)
            return error_msg