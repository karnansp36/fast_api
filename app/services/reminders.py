# services/reminders.py
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from dateutil import parser
from app.core.models import Task

async def create_reminder(task: str, time: str = None, user_id: str = "default", db: AsyncSession = None) -> Dict[str, Any]:
    try:
        due_time = None
        if time and time != "now":
            try:
                due_time = parser.parse(time)
            except (ValueError, TypeError):
                return {"error": f"Invalid time format: {time}"}
        
        reminder = Task(
            user_id=user_id,
            text=task,
            due_time=due_time,
            status="scheduled",
        )
        db.add(reminder)
        await db.commit()
        await db.refresh(reminder)

        return {
            "id": reminder.id,
            "task": reminder.text,
            "time": reminder.due_time.isoformat() if reminder.due_time else "now",
            "user_id": reminder.user_id,
            "status": reminder.status,
            "created_at": reminder.created_at.isoformat(),
        }

    except (ValueError, SQLAlchemyError) as e:
        await db.rollback()
        return {"error": f"Failed to create reminder: {str(e)}"}

async def get_user_reminders(user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    """Get all reminders for a user from DB"""
    try:
        result = await db.execute(
            select(Task).where(Task.user_id == user_id)
        )
        tasks = result.scalars().all()

        return [
            {
                "id": task.id,
                "task": task.text,
                "time": task.due_time.isoformat() if task.due_time else "now",
                "user_id": task.user_id,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
            }
            for task in tasks
        ]
    except SQLAlchemyError as e:
        return [{"error": f"Failed to fetch reminders: {str(e)}"}]
