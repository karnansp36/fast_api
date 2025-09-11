# tools/memory_tools.py - FIXED VERSION
from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
import asyncio
import json
from app.services.memory_service import memory_service
import logging

logger = logging.getLogger(__name__)

class StoreMemoryInput(BaseModel):
    """Input schema for StoreMemoryTool"""
    user_id: str = Field(..., description="User ID to store memory for")
    text: str = Field(..., description="Text content to store as memory")
    tags: List[str] = Field(default_factory=list, description="Optional tags for the memory")

class StoreMemoryTool(BaseTool):
    name: str = "store_memory"
    description: str = "Store user memory or important information for later retrieval"
    args_schema: Type[BaseModel] = StoreMemoryInput
    
    def _run(self, user_id: str, text: str, tags: List[str] = None) -> str:
        """Store memory synchronously - FIXED VERSION"""
        try:
            # Clean and validate inputs
            if isinstance(user_id, dict):
                user_id = str(user_id.get('description', 'default'))
            if isinstance(text, dict):
                text = str(text.get('description', ''))
            if isinstance(tags, dict):
                tags_str = str(tags.get('description', ''))
                tags = tags_str.split(',') if tags_str else []
            
            # Ensure we have valid data
            if not text.strip():
                return "Error: No text provided to store"
            
            user_id = str(user_id).strip()
            text = str(text).strip()
            tags = tags or []
            
            logger.info(f"Storing memory for user {user_id}: {text[:50]}...")
            
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Store memory
            result = loop.run_until_complete(
                memory_service.store_memory(
                    user_id, 
                    "user_memory", 
                    {"text": text, "tags": tags},
                    meta_data={"tags": tags}
                )
            )
            
            return f"Successfully stored: {text[:50]}..."
            
        except Exception as e:
            error_msg = f"Failed to store memory: {str(e)}"
            logger.error(error_msg)
            return error_msg

class SearchMemoryInput(BaseModel):
    """Input schema for SearchMemoryTool"""
    user_id: str = Field(..., description="User ID to search memories for")
    query: str = Field(default="", description="Search query to find relevant memories")

class SearchMemoryTool(BaseTool):
    name: str = "search_memory"
    description: str = "Search and retrieve user memories based on query"
    args_schema: Type[BaseModel] = SearchMemoryInput
    
    def _run(self, user_id: str, query: str = "") -> str:
        """Search memory synchronously - FIXED VERSION"""
        try:
            # Clean inputs
            if isinstance(user_id, dict):
                user_id = str(user_id.get('description', 'default'))
            if isinstance(query, dict):
                query = str(query.get('description', ''))
                
            user_id = str(user_id).strip()
            query = str(query).strip()
            
            logger.info(f"Searching memories for user {user_id} with query: {query}")
            
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            memories = loop.run_until_complete(
                memory_service.search_memories(user_id, "user_memory", query, 3)
            )
            
            if memories:
                memory_texts = [mem["text"] for mem in memories[:3]]
                result = f"Found {len(memory_texts)} memories: " + "; ".join(memory_texts[:3])
                logger.info(f"Search successful: {len(memories)} memories found")
                return result
            else:
                return "No relevant memories found"
                
        except Exception as e:
            error_msg = f"Failed to search memory: {str(e)}"
            logger.error(error_msg)
            return error_msg