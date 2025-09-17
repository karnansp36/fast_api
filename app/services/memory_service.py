# services/memory_service.py - UPDATED
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, cast, String, text, desc
from app.core.db import AsyncSessionLocal
from app.core.models import Memory, ConversationHistory, Task
from app.services.embeddings import embed_text
import json
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        pass
    
    async def _get_session(self) -> AsyncSession:
        """Get async database session"""
        return AsyncSessionLocal()
    
    async def store_memory(self, user_id: str, memory_type: str, 
                          content: Dict[str, Any], meta_data: Dict[str, Any] = None) -> str:
        """Store a memory with embedding"""
        try:
            # Convert content to text for embedding
            text_content = self._content_to_text(content)
            
            # Generate embedding
            embedding = embed_text(text_content)
            
            async with AsyncSessionLocal() as session:
                memory = Memory(
                    user_id=str(user_id),
                    text=text_content,
                    memory_type=memory_type,
                    meta_data={
                        "original_content": content,
                        **(meta_data or {})
                    },
                    embedding=embedding
                )
                session.add(memory)
                await session.commit()
                await session.refresh(memory)
                
                return f"Memory stored successfully: {text_content[:50]}..."
                
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return f"Error storing memory: {str(e)}"
    
    async def store_conversation(self, user_id: str, message: str, response: str, emotion: str = None):
        """Store a conversation exchange - FIXED"""
        try:
            async with AsyncSessionLocal() as session:
                conversation = ConversationHistory(
                    user_id=str(user_id),
                    message=message,
                    response=response,
                    emotion=emotion
                )
                session.add(conversation)
                await session.commit()
                await session.refresh(conversation)
                logger.info(f"Conversation stored for user {user_id}")
                return True
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            return False
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history - FIXED"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ConversationHistory)
                    .where(ConversationHistory.user_id == str(user_id))
                    .order_by(desc(ConversationHistory.created_at))
                    .limit(limit)
                )
                history = result.scalars().all()
                
                return [{
                    "id": h.id,
                    "user_id": h.user_id,
                    "message": h.message,
                    "response": h.response,
                    "emotion": h.emotion,
                    "created_at": h.created_at.isoformat() if h.created_at else None
                } for h in history]
                
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def search_memories(
        self, user_id: str, memory_type: Optional[str] = None,
        query: str = "", limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search memories with optional filtering by type and query"""
        try:
            async with AsyncSessionLocal() as session:
                base_query = select(Memory).where(Memory.user_id == str(user_id))
                
                if memory_type:
                    base_query = base_query.where(Memory.memory_type == memory_type)
                
                base_query = base_query.order_by(desc(Memory.created_at)).limit(limit)

                result = await session.execute(base_query)
                memories = result.scalars().all()

                return [{
                    "id": mem.id,
                    "user_id": mem.user_id,
                    "content": mem.meta_data.get("original_content", {}),
                    "text": mem.text,
                    "type": mem.memory_type,
                    "created_at": mem.created_at.isoformat() if mem.created_at else None,
                    "meta_data": mem.meta_data
                } for mem in memories]

        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context for the personal manager - FIXED"""
        try:
            # Get recent conversation history
            conversation_history = await self.get_conversation_history(user_id, 5)
            
            # Get recent memories
            recent_memories = await self.search_memories(user_id, limit=5)
            
            # Get user preferences
            preferences = await self.search_memories(user_id, "preference", limit=5)
            
            # Get pending tasks
            pending_tasks = await self.get_user_tasks(user_id, status="pending")
            
            return {
                "conversation_history": conversation_history,
                "recent_memories": recent_memories,
                "preferences": preferences,
                "pending_tasks": pending_tasks,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {}
    
    async def get_user_tasks(self, user_id: str, status: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user tasks with optional status filter"""
        try:
            async with AsyncSessionLocal() as session:
                query = select(Task).where(Task.user_id == str(user_id))
                
                if status:
                    query = query.where(Task.status == status)
                
                query = query.order_by(desc(Task.created_at)).limit(limit)
                
                result = await session.execute(query)
                tasks = result.scalars().all()
                
                return [{
                    "id": task.id,
                    "user_id": task.user_id,
                    "task": task.text,
                    "due_time": task.due_time.isoformat() if task.due_time else None,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                } for task in tasks]
                
        except Exception as e:
            logger.error(f"Error getting user tasks: {e}")
            return []
    
    def _content_to_text(self, content: Dict[str, Any]) -> str:
        """Convert content dictionary to searchable text"""
        if isinstance(content, str):
            return content
        
        text_parts = []
        for key, value in content.items():
            if isinstance(value, (str, int, float)):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, dict):
                text_parts.append(f"{key}: {self._content_to_text(value)}")
            elif isinstance(value, list):
                text_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
        
        return "; ".join(text_parts)
    
    async def delete_memory(self, user_id: str, memory_id: int) -> bool:
        """Delete a specific memory"""
        try:
            async with AsyncSessionLocal() as session:
                memory = await session.get(Memory, memory_id)
                if memory and memory.user_id == str(user_id):
                    await session.delete(memory)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

# Global instance
memory_service = MemoryService()