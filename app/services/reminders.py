# services/reminders.py
from datetime import datetime
from typing import Dict, Any, List

# Simple in-memory storage for demo
reminders_store = {}

def create_reminder(task: str, time: str = None, user_id: str = "default") -> Dict[str, Any]:
    """Create a reminder task"""
    try:
        reminder_id = f"{user_id}_{len(reminders_store)}"
        reminder = {
            "id": reminder_id,
            "task": task,
            "time": time or "now",
            "user_id": user_id,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        reminders_store[reminder_id] = reminder
        return reminder
    except Exception as e:
        return {"error": f"Failed to create reminder: {str(e)}"}

def get_user_reminders(user_id: str) -> List[Dict[str, Any]]:
    """Get all reminders for a user"""
    return [r for r in reminders_store.values() if r.get("user_id") == user_id]