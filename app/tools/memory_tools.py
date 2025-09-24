# tools/memory_tools.py
from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
import asyncio
import json
import logging
from app.services.memory_service import memory_service
from app.core.db import AsyncSessionLocal # Import AsyncSessionLocal

logger = logging.getLogger(__name__)

class StoreMemoryInput(BaseModel):
    """Input schema for StoreMemoryTool"""
    user_id: str = Field(..., description="User ID to store memory for")
    text: str = Field(..., description="Text content to store as memory")
    memory_type: str = Field("general", description="Type of memory: general, preference, fact, episodic")
    tags: List[str] = Field(default_factory=list, description="Optional tags for the memory")

class StoreMemoryTool(BaseTool):
    name: str = "store_memory"
    description: str = "Store user memory or important information for later retrieval"
    args_schema: Type[BaseModel] = StoreMemoryInput
    
    def _run(self, user_id: str, text: str, memory_type: str = "general", tags: List[str] = None) -> str:
        """Store memory synchronously"""
        try:
            # Clean and validate inputs
            if isinstance(user_id, dict):
                user_id = str(user_id.get('description', 'default'))
            if isinstance(text, dict):
                text = str(text.get('description', ''))
            if isinstance(memory_type, dict):
                memory_type = str(memory_type.get('description', 'general'))
            if isinstance(tags, dict):
                tags_str = str(tags.get('description', ''))
                tags = tags_str.split(',') if tags_str else []
            
            # Ensure we have valid data
            if not text.strip():
                return "Error: No text provided to store"
            
            user_id = str(user_id).strip()
            text = str(text).strip()
            memory_type = str(memory_type).strip()
            tags = tags or []
            
            logger.info(f"Storing memory for user {user_id} (type: {memory_type}): {text[:50]}...")
            
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Store memory using memory service
            content = {
                "text": text,
                "tags": tags,
                "source": "user_input"
            }
            
            async def _store_memory_async():
                async with AsyncSessionLocal() as session:
                    return await memory_service.store_memory(
                        session,
                        user_id,
                        memory_type,
                        content,
                        meta_data={"tags": tags}
                    )

            result = loop.run_until_complete(_store_memory_async())
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg)
            return error_msg

class SearchMemoryInput(BaseModel):
    """Input schema for SearchMemoryTool"""
    user_id: str = Field(..., description="User ID to search memories for")
    query: str = Field(default="", description="Search query to find relevant memories")
    memory_type: str = Field(None, description="Optional memory type to filter by")

class SearchMemoryTool(BaseTool):
    name: str = "search_memory"
    description: str = "Search and retrieve user memories based on query"
    args_schema: Type[BaseModel] = SearchMemoryInput
    
    def _run(self, user_id: str, query: str = "", memory_type: str = None) -> str:
        """Search memory synchronously"""
        try:
            # Clean inputs
            if isinstance(user_id, dict):
                user_id = str(user_id.get('description', 'default'))
            if isinstance(query, dict):
                query = str(query.get('description', ''))
            if isinstance(memory_type, dict):
                memory_type = str(memory_type.get('description', ''))
                
            user_id = str(user_id).strip()
            query = str(query).strip()
            memory_type = str(memory_type).strip() if memory_type else None
            
            logger.info(f"Searching memories for user {user_id} with query: {query}")
            
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            async def _search_memories_async():
                async with AsyncSessionLocal() as session:
                    return await memory_service.search_memories(session, user_id, memory_type, query, 5)

            memories = loop.run_until_complete(_search_memories_async())
            
            if memories:
                memory_texts = [mem["text"] for mem in memories[:3]]
                result = f"Found {len(memories)} memories: " + "; ".join(memory_texts[:3])
                logger.info(f"Search successful: {len(memories)} memories found")
                return result
            else:
                return "No relevant memories found"
                
        except Exception as e:
            error_msg = f"Failed to search memory: {str(e)}"
            logger.error(error_msg)
            return error_msg