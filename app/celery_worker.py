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
                
        elif agent_type == "emotion_agent":
            from app.crew.agents.emotion import emotion_agent
            from app.crew.tasks import create_emotion_task
            
            task_desc = create_emotion_task(message)
            crew = Crew(agents=[emotion_agent], tasks=[task_desc], process=Process.sequential)
            result = crew.kickoff()
            logger.info(f"Emotion agent completed: {result[:100]}...")
            return str(result)
            
    except Exception as e:
        logger.error(f"Background task failed for {agent_type}: {e}")
        return f"Error: {str(e)}"

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