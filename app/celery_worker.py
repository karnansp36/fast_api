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
    imports=('app.celery_worker',),
    beat_schedule={
        'process-queued-tasks-every-minute': {
            'task': 'app.celery_worker.process_queued_tasks',
            'schedule': crontab(minute='*/1'),
        },
    },
    task_routes={
        'app.celery_worker.delegate_to_agent': {'queue': 'agent_tasks'},
    }
)

# Initialize services
memory_service = MemoryService()

@celery.task(name='app.celery_worker.delegate_to_agent')
def delegate_to_agent(agent_type, user_id, message, action):
    """Process task in background using appropriate agent"""
    try:
        logger.info(f"Celery task started for {agent_type}: {message[:50]}...")
        
        # Import agents and tasks inside the function to avoid circular imports
        if agent_type == "task_agent":
            from app.crew.agents.task import task_agent
            from app.crew.tasks import create_task_management_task
            
            if action == "create":
                task_desc = create_task_management_task(message, user_id, "create")
            else:
                task_desc = create_task_management_task(message, user_id, "get")
            
            crew = Crew(agents=[task_agent], tasks=[task_desc], process=Process.sequential)
            result = crew.kickoff()
            logger.info(f"Task agent completed: {result[:100]}...")
            return str(result)
                
        elif agent_type == "memory_agent":
            from app.crew.agents.memory import memory_agent
            from app.crew.tasks import create_memory_task
            
            if action == "store":
                task_desc = create_memory_task(message, user_id, "store")
            else:
                task_desc = create_memory_task(message, user_id, "search")
            
            crew = Crew(agents=[memory_agent], tasks=[task_desc], process=Process.sequential)
            result = crew.kickoff()
            logger.info(f"Memory agent completed: {result[:100]}...")
            return str(result)
                
            
    except Exception as e:
        logger.error(f"Background task failed for {agent_type}: {e}")
        return f"Error: {str(e)}"

@celery.task(name='app.celery_worker.create_reminder_task')
def create_reminder_task(task_text: str, time_str: str, user_id: str):
    """Celery task to create a reminder in the background."""
    from app.services.reminders import create_reminder
    from app.core.db import AsyncSessionLocal
    logger.info(f"Celery task: Creating reminder for user {user_id}: {task_text[:50]}...")
    
    async def run_create_reminder():
        async with AsyncSessionLocal() as db:
            result = await create_reminder(task_text, time_str, user_id, db)
            if "error" in result:
                logger.error(f"Celery task failed to create reminder: {result['error']}")
            else:
                logger.info(f"Celery task successfully created reminder: {result['task']}")
        return result

    return asyncio.run(run_create_reminder())

@celery.task
def process_queued_tasks():
    """Process tasks from the fallback queue"""
    try:
        from app.services.task_queue_service import get_pending_tasks, mark_task_as_processed
        pending_tasks = get_pending_tasks()
        
        for task in pending_tasks:
            try:
                # Process the queued task
                delegate_to_agent(
                    task['agent_type'], 
                    task['user_id'], 
                    task['message'], 
                    task['action']
                )
                mark_task_as_processed(task['id'])
                logger.info(f"Processed queued task {task['id']}")
            except Exception as e:
                logger.error(f"Failed to process queued task {task['id']}: {e}")
        
        return f"Processed {len(pending_tasks)} queued tasks"
    except Exception as e:
        logger.error(f"Failed to process task queue: {e}")
        return "Queue processing failed"