# services/memory_service.py - UPDATED
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.db import AsyncSessionLocal, get_session
from app.core.models import Memory, ConversationHistory, Task
from app.services.embeddings import embed_text
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        pass
    
    async def store_memory(self, session: AsyncSession, user_id: str, memory_type: str, 
                          content: Dict[str, Any], meta_data: Dict[str, Any] = None) -> str:
        """Store a memory with embedding - FIXED to accept session"""
        try:
            # Convert content to text for embedding
            text_content = self._content_to_text(content)
            
            # Generate embedding
            embedding = embed_text(text_content)
            
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
            await session.rollback()
            return f"Error storing memory: {str(e)}"
    
    async def store_conversation(self, session: AsyncSession, user_id: str, message: str, response: str, emotion: str = None) -> bool:
        """Store a chat conversation exchange - FIXED to accept session"""
        try:
            # Clean and validate inputs
            user_id = str(user_id).strip()
            message = str(message).strip() if message else ""
            response = str(response).strip() if response else ""
            emotion = str(emotion).strip() if emotion else None

            if not message or not response:
                logger.warning(f"Skipping empty conversation storage for user {user_id}")
                return False

            conversation = ConversationHistory(
                user_id=user_id,
                message=message[:4000],
                response=response[:4000],
                emotion=emotion[:20] if emotion else None
            )
            session.add(conversation)
            await session.commit()
            logger.info(f"✅ Conversation stored for user {user_id}: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Error storing conversation for user {user_id}: {e}")
            await session.rollback()
            return False
    
    async def get_conversation_history(self, session: AsyncSession, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history - FIXED to accept session"""
        try:
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
    
    # Update other methods similarly to accept session parameter...

# Global instance
memory_service = MemoryService()