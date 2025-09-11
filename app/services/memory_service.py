from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, cast, String
from app.core.db import AsyncSessionLocal
from app.core.models import Memory
from app.services.embeddings import embed_text
import json
from datetime import datetime
import re

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
                    user_id=str(user_id),  # Ensure string conversion
                    text=text_content,
                    meta_data={
                        "type": memory_type,
                        "original_content": content,
                        **(meta_data or {})
                    },
                    embedding=embedding
                )
                session.add(memory)
                await session.commit()
                
                return f"Memory stored successfully: {text_content[:50]}..."
                
        except Exception as e:
            return f"Error storing memory: {str(e)}"
    
    async def search_memories(self, user_id: str, memory_type: Optional[str] = None,
                            query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories with optional filtering by type and query - FIXED"""
        try:
            async with AsyncSessionLocal() as session:
                # Build base query with proper string casting
                base_query = select(Memory).where(Memory.user_id == str(user_id))
                
                # Add memory type filter if specified - FIXED for PostgreSQL JSONB
                if memory_type:
                    base_query = base_query.where(
                        cast(Memory.meta_data['type'], String) == memory_type
                    )
                
                # Add text search if query provided
                if query:
                    base_query = base_query.where(
                        or_(
                            Memory.text.ilike(f"%{query}%"),
                            cast(Memory.meta_data['original_content'], String).ilike(f"%{query}%")
                        )
                    )
                
                # Add limit and order
                base_query = base_query.order_by(Memory.created_at.desc()).limit(limit)
                
                result = await session.execute(base_query)
                memories = result.scalars().all()
                
                return [{
                    "id": mem.id,
                    "user_id": mem.user_id,
                    "content": mem.meta_data.get("original_content", {}),
                    "text": mem.text,
                    "type": mem.meta_data.get("type", "unknown"),
                    "created_at": mem.created_at.isoformat() if mem.created_at else None,
                    "meta_data": mem.meta_data
                } for mem in memories]
                
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
    
    async def get_recent_memories(self, user_id: str, memory_type: Optional[str] = None,
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent memories, optionally filtered by type"""
        return await self.search_memories(str(user_id), memory_type, "", limit)
    
    async def search_similar_memories(self, user_id: str, query_text: str, 
                                     memory_type: Optional[str] = None, 
                                     limit: int = 3) -> List[Dict[str, Any]]:
        """Search for similar memories using embedding similarity"""
        try:
            # Generate embedding for query
            query_embedding = embed_text(query_text)
            
            async with AsyncSessionLocal() as session:
                # Build base query with proper string casting
                base_query = select(Memory).where(Memory.user_id == str(user_id))
                
                # Add memory type filter if specified
                if memory_type:
                    base_query = base_query.where(
                        cast(Memory.meta_data['type'], String) == memory_type
                    )
                
                # Use pgvector cosine distance for similarity search
                base_query = base_query.order_by(
                    Memory.embedding.cosine_distance(query_embedding)
                ).limit(limit)
                
                result = await session.execute(base_query)
                memories = result.scalars().all()
                
                return [{
                    "id": mem.id,
                    "content": mem.meta_data.get("original_content", {}),
                    "text": mem.text,
                    "type": mem.meta_data.get("type", "unknown"),
                    "similarity_score": 1 - float(mem.embedding.cosine_distance(query_embedding)),
                    "created_at": mem.created_at.isoformat() if mem.created_at else None
                } for mem in memories]
                
        except Exception as e:
            print(f"Error searching similar memories: {e}")
            # Fallback to text search
            return await self.search_memories(str(user_id), memory_type, query_text, limit)
    
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
        except Exception:
            return False

# Global instance
memory_service = MemoryService()