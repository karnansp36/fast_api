# api/websocket_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.crew.orchestrator import run_crew
import json
from typing import Dict

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

manager = ConnectionManager()

@router.websocket("/ws/chat/{user_id}")
async def chat_socket(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON if sent as JSON
                message_data = json.loads(data)
                message = message_data.get("message", data)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text
                message = data
            
            # Process message through CrewAI
            try:
                result = await run_crew(message, user_id)
                await websocket.send_json({
                    "reply": result,
                    "user_id": user_id,
                    "status": "success"
                })
            except Exception as e:
                await websocket.send_json({
                    "reply": f"Sorry, I encountered an error: {str(e)}",
                    "user_id": user_id,
                    "status": "error"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Personal Manager with CrewAI"}

@router.get("/chat/{user_id}")
async def chat_http(user_id: str, message: str):
    """HTTP endpoint for testing"""
    try:
        result = await run_crew(message, user_id)
        return {"reply": result, "user_id": user_id, "status": "success"}
    except Exception as e:
        return {"reply": f"Error: {str(e)}", "user_id": user_id, "status": "error"}