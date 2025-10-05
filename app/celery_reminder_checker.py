# celery_reminder_checker.py
from datetime import datetime, timezone
from app.core.db import AsyncSessionLocal
from app.core.models import Task
from sqlalchemy.future import select
from app.api.websocket_routes import push_message_to_user  # You must implement this function to send chat messages
import asyncio
import logging

logger = logging.getLogger(__name__)

async def check_and_push_due_reminders():
    """
    Celery periodic task: Check the Task table for reminders that are due and push them to the chat.
    """
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        # Query all pending tasks with due_time <= now
        result = await session.execute(
            select(Task).where(Task.status == "pending", Task.due_time != None, Task.due_time <= now)
        )
        due_tasks = result.scalars().all()
        for task in due_tasks:
            try:
                # Push the reminder to the chat (implement this function in your websocket/chat system)
                await push_message_to_user(task.user_id, f"⏰ Reminder: {task.text}")
                # Mark the task as completed
                task.status = "completed"
                await session.commit()
                logger.info(f"Pushed reminder to user {task.user_id}: {task.text}")
            except Exception as e:
                logger.error(f"Failed to push reminder for user {task.user_id}: {e}")

# To use with Celery, wrap with a sync function
from celery import shared_task
from asgiref.sync import async_to_sync

@shared_task
def celery_check_and_push_due_reminders():
    async_to_sync(check_and_push_due_reminders)()
