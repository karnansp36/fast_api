from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pathlib import Path
import asyncio
import json
import logging
import time
import traceback
from typing import Dict

from app.crew.orchestrator import run_personal_manager as run_crew

logger = logging.getLogger(__name__)
router = APIRouter()
WEB_DIR = Path(__file__).resolve().parents[1] / "web"


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.dispatchers: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.message_queues[user_id] = asyncio.Queue()
        self.dispatchers[user_id] = asyncio.create_task(self.dispatch_messages(user_id))

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        task = self.processing_tasks.pop(user_id, None)
        if task:
            task.cancel()
        dispatcher = self.dispatchers.pop(user_id, None)
        if dispatcher:
            dispatcher.cancel()
        self.message_queues.pop(user_id, None)

    async def dispatch_messages(self, user_id: str):
        try:
            websocket = self.active_connections[user_id]
            queue = self.message_queues[user_id]
            while True:
                message = await queue.get()
                await websocket.send_json(message)
                queue.task_done()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("WebSocket dispatcher stopped for user %s", user_id)
            self.disconnect(user_id)


manager = ConnectionManager()


async def push_message_to_user(user_id: str, message: str):
    """Queue a message for a connected user; return False if they are offline."""
    queue = manager.message_queues.get(user_id)
    if queue is None:
        logger.warning("User %s is not connected; reminder was not delivered", user_id)
        return False
    await queue.put({"reply": message, "user_id": user_id, "status": "reminder"})
    return True


async def process_message_with_timeout(user_id: str, message: str, start_time: float):
    try:
        result = await asyncio.wait_for(run_crew(message, user_id), timeout=180.0)
        queue = manager.message_queues.get(user_id)
        if queue:
            await queue.put({
                "reply": result,
                "user_id": user_id,
                "status": "success",
                "processing_time": time.time() - start_time,
            })
    except asyncio.TimeoutError:
        queue = manager.message_queues.get(user_id)
        if queue:
            await queue.put({
                "reply": "The request took too long to process. Please try again.",
                "user_id": user_id,
                "status": "timeout",
                "processing_time": time.time() - start_time,
            })
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Error processing chat message for user %s", user_id)
        queue = manager.message_queues.get(user_id)
        if queue:
            await queue.put({
                "reply": "Sorry, I could not process that message. Please try again.",
                "user_id": user_id,
                "status": "error",
                "processing_time": time.time() - start_time,
            })


@router.get("/ui", include_in_schema=False)
async def chat_ui():
    return FileResponse(WEB_DIR / "chat.html")


@router.websocket("/ws/chat/{user_id}")
async def chat_socket(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        await websocket.send_json({"type": "ping", "timestamp": time.time()})
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
            start_time = time.time()
            try:
                message_data = json.loads(data)
                message = message_data.get("message", data)
            except (json.JSONDecodeError, AttributeError):
                message = data
            if not isinstance(message, str) or not message.strip():
                await websocket.send_json({"status": "error", "message": "Message cannot be empty."})
                continue
            await websocket.send_json({"status": "processing", "message": "Request received."})
            previous = manager.processing_tasks.get(user_id)
            if previous and not previous.done():
                previous.cancel()
            manager.processing_tasks[user_id] = asyncio.create_task(
                process_message_with_timeout(user_id, message.strip(), start_time)
            )
    except asyncio.TimeoutError:
        try:
            await websocket.send_json({"type": "ping", "timestamp": time.time()})
        except Exception:
            manager.disconnect(user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception:
        logger.exception("Unexpected WebSocket error for user %s", user_id)
        manager.disconnect(user_id)


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TaskPilot"}


@router.get("/chat/{user_id}")
async def chat_http(user_id: str, message: str):
    if not message.strip():
        return {"reply": "Message cannot be empty.", "user_id": user_id, "status": "error"}
    start_time = time.time()
    try:
        result = await asyncio.wait_for(run_crew(message.strip(), user_id), timeout=120.0)
        return {
            "reply": result,
            "user_id": user_id,
            "status": "success",
            "processing_time": time.time() - start_time,
        }
    except asyncio.TimeoutError:
        return {
            "reply": "The request took too long to process. Please try again.",
            "user_id": user_id,
            "status": "timeout",
            "processing_time": time.time() - start_time,
        }
    except Exception:
        logger.exception("Error processing HTTP chat request for user %s", user_id)
        return {
            "reply": "Sorry, I could not process that message. Please try again.",
            "user_id": user_id,
            "status": "error",
            "processing_time": time.time() - start_time,
        }
