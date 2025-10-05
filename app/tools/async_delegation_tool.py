# tools/async_delegation_tool.py
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import logging
from app.celery_worker import celery

logger = logging.getLogger(__name__)

class AsyncDelegationInput(BaseModel):
    agent_type: str = Field(..., description="Type of specialized worker to delegate to")
    user_id: str = Field(..., description="User ID for context")
    message: str = Field(..., description="Message content to process")
    action: str = Field("process", description="Action to perform")
    time: str = Field("now", description="When the reminder should be scheduled (ISO format or 'now')")

class AsyncDelegationTool(BaseTool):
    name: str = "AsyncDelegationTool"
    description: str = "Delegate complex tasks to specialized workers for background processing"
    args_schema: Type[BaseModel] = AsyncDelegationInput

    def _run(self, agent_type: str, user_id: str, message: str, action: str = "process", time: str = "now") -> str:
        """Delegate task for background processing"""
        try:
            logger.info(f"Delegating to {agent_type} for user {user_id}: {message[:50]}...")
            
            if agent_type == "reminder_agent":
                celery.send_task('app.celery_worker.create_reminder_task', args=[message, time, user_id])
                return f"Reminder task has been queued for background processing."
            else:
                celery.send_task('app.celery_worker.delegate_to_agent', args=[agent_type, user_id, message, action])
                return f"Task has been queued for processing by our {agent_type.replace('_', ' ')}"
            
        except Exception as e:
            logger.error(f"Delegation failed for {agent_type}: {e}")
            return "Task delegation failed, but I'll process your request directly"