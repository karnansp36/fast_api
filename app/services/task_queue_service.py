# services/task_queue_service.py
import sqlite3
import json
from datetime import datetime
import logging
from app.config import settings
import os

logger = logging.getLogger(__name__)

# Get the path for the task queue database
TASK_QUEUE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'task_queue.db')

def init_task_queue_db():
    """Initialize the task queue database"""
    try:
        conn = sqlite3.connect(TASK_QUEUE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP NULL
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Task queue database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize task queue database: {e}")

def add_to_task_queue(agent_type, user_id, message, action):
    """Add a task to the queue for later processing"""
    try:
        conn = sqlite3.connect(TASK_QUEUE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO task_queue (agent_type, user_id, message, action) VALUES (?, ?, ?, ?)',
            (agent_type, user_id, message, action)
        )
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Task added to queue with ID: {task_id}")
        return task_id
    except Exception as e:
        logger.error(f"Failed to add task to queue: {e}")
        return None

def get_pending_tasks():
    """Get all pending tasks from the queue"""
    try:
        conn = sqlite3.connect(TASK_QUEUE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM task_queue WHERE status = "pending" ORDER BY created_at ASC')
        tasks = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task[0],
                'agent_type': task[1],
                'user_id': task[2],
                'message': task[3],
                'action': task[4],
                'status': task[5],
                'created_at': task[6],
                'processed_at': task[7]
            })
        
        return task_list
    except Exception as e:
        logger.error(f"Failed to get pending tasks: {e}")
        return []

def mark_task_as_processed(task_id):
    """Mark a task as processed"""
    try:
        conn = sqlite3.connect(TASK_QUEUE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE task_queue SET status = "processed", processed_at = ? WHERE id = ?',
            (datetime.now(), task_id)
        )
        conn.commit()
        conn.close()
        logger.info(f"Task {task_id} marked as processed")
        return True
    except Exception as e:
        logger.error(f"Failed to mark task {task_id} as processed: {e}")
        return False

def process_queued_tasks():
    """Process all pending tasks in the queue"""
    try:
        pending_tasks = get_pending_tasks()
        logger.info(f"Found {len(pending_tasks)} pending tasks to process")
        
        for task in pending_tasks:
            try:
                # Try to process with Celery if available
                from celery import current_app
                current_app.send_task('app.celery_worker.delegate_to_agent', 
                                    args=[task['agent_type'], task['user_id'], task['message'], task['action']])
                
                # Mark as processed
                mark_task_as_processed(task['id'])
                logger.info(f"Processed queued task {task['id']}")
            except Exception as e:
                logger.error(f"Failed to process queued task {task['id']}: {e}")
        
        return len(pending_tasks)
    except Exception as e:
        logger.error(f"Failed to process task queue: {e}")
        return 0

# Initialize the database on import
init_task_queue_db()