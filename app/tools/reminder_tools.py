# tools/reminder_tools.py
from crewai.tools import BaseTool
from app.services.reminders import create_reminder, get_user_reminders
from app.core.db import AsyncSessionLocal
from typing import Type
from pydantic import BaseModel, Field
import asyncio

class CreateReminderInput(BaseModel):
    task: str = Field(..., description="Task description for the reminder")
    time: str = Field(default="now", description="When to remind (time/date in ISO format or 'now')")
    user_id: str = Field(..., description="User ID for the reminder")

class CreateReminderTool(BaseTool):
    name: str = "create_reminder"
    description: str = "Create a reminder or task for the user"
    args_schema: Type[BaseModel] = CreateReminderInput

    async def _run(self, task: str, time: str = "now", user_id: str = "default") -> str:
        try:
            async with AsyncSessionLocal() as db:
                result = await create_reminder(task, time, user_id, db)
                if "error" in result:
                    return f"❌ {result['error']}"
                return f"✅ Reminder created: {result['task']} at {result['time']}"
        except Exception as e:
            return f"❌ Error creating reminder: {str(e)}"

class GetRemindersInput(BaseModel):
    user_id: str = Field(..., description="User ID to get reminders for")

class GetRemindersTool(BaseTool):
    name: str = "get_reminders"
    description: str = "Get all reminders for a user"
    args_schema: Type[BaseModel] = GetRemindersInput

    async def _run(self, user_id: str) -> str:
        try:
            async with AsyncSessionLocal() as db:
                reminders = await get_user_reminders(user_id, db)
                if reminders and isinstance(reminders, list):
                    reminder_list = [
                        f"- {r['task']} at {r['time']} ({r['status']})"
                        for r in reminders if "task" in r
                    ]
                    return "📌 Your reminders:\n" + "\n".join(reminder_list) if reminder_list else "No reminders found"
                else:
                    return "No reminders found"
        except Exception as e:
            return f"❌ Error getting reminders: {str(e)}"