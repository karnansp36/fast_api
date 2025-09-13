# celery_worker.py
from celery import Celery
from app.config import settings
from app.services.memory_service import MemoryService
import asyncio
import logging
from crewai import Crew, Process
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery(
    'crew_worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)
# Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'process-queued-tasks-every-minute': {
            'task': 'app.celery_worker.process_queued_tasks',
            'schedule': crontab(minute='*/1'),  # Run every minute
        },
    },
)
# Initialize services
memory_service = MemoryService()


@celery.task
def delegate_to_agent(agent_type, user_id, message, action):
    """Process task in background using appropriate agent"""
    try:
        # Import agents and tasks inside the function to avoid circular imports
        if agent_type == "memory":
            from app.crew.agents.memory import memory_agent
            from app.crew.tasks import create_memory_task
            if action == "store":
                task = create_memory_task(message, user_id, "store")
            else:
                task = create_memory_task(message, user_id, "search")
            crew = Crew(agents=[memory_agent], tasks=[task], process=Process.sequential)
            result = crew.kickoff()  # Remove asyncio.run for synchronous execution
            return str(result)
                
        elif agent_type == "task":
            from app.crew.agents.task import task_agent
            from app.crew.tasks import create_task_management_task
            if action == "create":
                task = create_task_management_task(message, user_id, "create")
            else:
                task = create_task_management_task(message, user_id, "get")
            crew = Crew(agents=[task_agent], tasks=[task], process=Process.sequential)
            result = crew.kickoff()  # Remove asyncio.run for synchronous execution
            return str(result)
                
        elif agent_type == "emotion":
            from app.crew.agents.emotion import emotion_agent
            from app.crew.tasks import create_emotion_task
            task = create_emotion_task(message)
            crew = Crew(agents=[emotion_agent], tasks=[task], process=Process.sequential)
            result = crew.kickoff()  # Remove asyncio.run for synchronous execution
            return str(result)
            
    except Exception as e:
        logger.error(f"Background task failed: {e}")
        return f"Error: {str(e)}"