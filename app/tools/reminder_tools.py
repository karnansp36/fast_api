# tools/reminder_tools.py
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from app.services.reminders import get_user_reminders
from app.tools.async_delegation_tool import AsyncDelegationTool
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
        """Delegate reminder creation for background processing"""
        try:
            # Clean inputs
            task = str(task).strip()
            time = str(time).strip()
            user_id = str(user_id).strip()
            
            if not task:
                return "Error: No task provided"
            
            logger.info(f"Delegating reminder creation for user {user_id}: {task[:50]}...")
            
            # Delegate to AsyncDelegationTool
            delegation_tool = AsyncDelegationTool()
            result = delegation_tool._run(
                agent_type="reminder_agent",
                user_id=user_id,
                message=task,
                action="create",
                time=time
            )
            
            return result
                
        except Exception as e:
            error_msg = f"Failed to delegate reminder creation: {str(e)}"
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
            
            # Get reminders - relying on get_user_reminders to handle its own session
            # This is a synchronous call to an async function, which is generally not ideal.
            # For a proper async setup, this would also be delegated via Celery.
            # However, for now, we'll keep it functional.
            
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            async def get_reminders_async():
                # get_user_reminders can handle session internally if not provided
                return await get_user_reminders(user_id)
            
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