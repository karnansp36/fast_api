# tools/async_delegation_tool.py
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import logging
import time
from app.config import settings

logger = logging.getLogger(__name__)

class AsyncDelegationInput(BaseModel):
    agent_type: str = Field(..., description="Type of agent to delegate to (memory, task, emotion)")
    user_id: str = Field(..., description="User ID for context")
    message: str = Field(..., description="Message content to process")
    action: str = Field("process", description="Action to perform (store, search, create, etc.)")

class AsyncDelegationTool(BaseTool):
    name: str = "AsyncDelegationTool"
    description: str = "Delegate tasks to specialized agents for background processing"
    args_schema: Type[BaseModel] = AsyncDelegationInput

    def _run(self, agent_type: str, user_id: str, message: str, action: str = "process") -> str:
        try:
            # Try to import and use Celery
            try:
                from celery import current_app
                task = current_app.send_task('app.celery_worker.delegate_to_agent', 
                                            args=[agent_type, user_id, message, action])
                return f"Task delegated to {agent_type} agent for background processing (Task ID: {task.id})"
            except Exception as e:
                logger.warning(f"Celery not available, using fallback: {e}")
                
            # Fallback: Store the task in the task queue for later processing
            try:
                from app.services.task_queue_service import add_to_task_queue
                task_id = add_to_task_queue(agent_type, user_id, message, action)
                if task_id:
                    return f"Task queued for {agent_type} agent (Queue ID: {task_id})"
                else:
                    return f"Failed to queue task for {agent_type} agent"
            except Exception as e:
                logger.error(f"Failed to queue task: {e}")
                
            return f"Task will be processed later by {agent_type} agent"
            
        except Exception as e:
            logger.error(f"Failed to delegate task: {e}")
            return "Task delegation failed, but I'll process your request"