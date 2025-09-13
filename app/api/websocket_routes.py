# api/websocket_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# Replace old orchestrator import with enhanced orchestrator
from app.crew.orchestrator_enhanced import run_enhanced_crew as run_crew
import json
from typing import Dict
import asyncio
import logging
import time
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.processing_tasks:
            self.processing_tasks[user_id].cancel()
            del self.processing_tasks[user_id]

manager = ConnectionManager()

async def process_message_with_timeout(websocket, user_id, message, start_time):
    """Process message with proper timeout handling"""
    try:
        # Set a timeout for the crew execution (120 seconds)
        result = await asyncio.wait_for(run_crew(message, user_id), timeout=180.0)
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(f"Request completed in {processing_time:.2f} seconds for user {user_id}")
        
        # Only send success if the connection is still active
        if user_id in manager.active_connections:
            await websocket.send_json({
                "reply": result,
                "user_id": user_id,
                "status": "success",
                "processing_time": processing_time
            })
        
        return True
        
    except asyncio.TimeoutError:
        end_time = time.time()
        processing_time = end_time - start_time
        logger.error(f"Request timeout after {processing_time:.2f} seconds for user {user_id}")
        
        if user_id in manager.active_connections:
            await websocket.send_json({
                "reply": "I apologize, but the request took too long to process. Please try again with a more specific request.",
                "user_id": user_id,
                "status": "timeout",
                "processing_time": processing_time
            })
        
        return False
        
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        logger.error(f"Error processing message for user {user_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")  # ADD THIS LINE

        if user_id in manager.active_connections:
            await websocket.send_json({
                "reply": f"Sorry, I encountered an error: {str(e)}",
                "user_id": user_id,
                "status": "error",
                "processing_time": processing_time
            })
        
        return False

@router.websocket("/ws/chat/{user_id}")
async def chat_socket(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial ping to establish connection
        await websocket.send_json({"type": "ping", "timestamp": time.time()})
        
        while True:
            try:
                # Wait for message with timeout (300 seconds = 5 minutes)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
                start_time = time.time()
                
                try:
                    # Parse JSON if sent as JSON
                    message_data = json.loads(data)
                    message = message_data.get("message", data)
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    message = data
                
                # Send acknowledgment that message was received
                await websocket.send_json({
                    "status": "processing",
                    "message": "Request received, processing...",
                    "timestamp": start_time
                })
                
                # Process message in background task
                processing_task = asyncio.create_task(
                    process_message_with_timeout(websocket, user_id, message, start_time)
                )
                manager.processing_tasks[user_id] = processing_task
                
                # Wait for the task to complete but don't block receiving new messages
                await processing_task
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive when no messages received
                try:
                    await websocket.send_json({"type": "ping", "timestamp": time.time()})
                    logger.debug(f"Sent ping to user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send ping to user {user_id}: {str(e)}")
                    break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection for user {user_id}: {str(e)}")
        manager.disconnect(user_id)

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Personal Manager with CrewAI"}

@router.get("/chat/{user_id}")
async def chat_http(user_id: str, message: str):
    """HTTP endpoint for testing"""
    start_time = time.time()
    try:
        # Set timeout for HTTP requests as well
        result = await asyncio.wait_for(run_crew(message, user_id), timeout=120.0)
        end_time = time.time()
        processing_time = end_time - start_time
        
        return {
            "reply": result, 
            "user_id": user_id, 
            "status": "success",
            "processing_time": processing_time
        }
    except asyncio.TimeoutError:
        end_time = time.time()
        processing_time = end_time - start_time
        return {
            "reply": "I apologize, but the request took too long to process. Please try again with a more specific request.", 
            "user_id": user_id, 
            "status": "timeout",
            "processing_time": processing_time
        }
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        return {
            "reply": f"Error: {str(e)}", 
            "user_id": user_id, 
            "status": "error",
            "processing_time": processing_time
        }