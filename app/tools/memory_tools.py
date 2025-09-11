# tools/memory_tools.py - FIXED VERSION (No Mem0)
from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

# Import your custom memory service instead of mem0
from typing import Dict, Any, Optional
from datetime import datetime

class SimpleMemoryService:
    """Simple in-memory fallback service to avoid Mem0 issues"""
    def __init__(self):
        self.memories = {}
    
    async def store_memory(self, user_id: str, memory_type: str, content: Dict[str, Any], meta_data: Dict[str, Any] = None) -> str:
        try:
            if user_id not in self.memories:
                self.memories[user_id] = []
            
            memory_entry = {
                "text": content.get("text", str(content)),
                "type": memory_type,
                "content": content,
                "meta_data": meta_data or {},
                "timestamp": datetime.now().isoformat()
            }
            
            self.memories[user_id].append(memory_entry)
            logger.info(f"Stored memory for user {user_id}")
            return f"Memory stored successfully: {memory_entry['text'][:50]}..."
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return f"Error storing memory: {str(e)}"
    
    async def search_memories(self, user_id: str, memory_type: Optional[str] = None, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        try:
            if user_id not in self.memories:
                return []
            
            user_memories = self.memories[user_id]
            
            # Filter by type if specified
            if memory_type:
                user_memories = [mem for mem in user_memories if mem.get("type") == memory_type]
            
            # Search by query if provided
            if query:
                query_lower = query.lower()
                filtered = []
                for mem in user_memories:
                    text = mem.get("text", "").lower()
                    if query_lower in text:
                        filtered.append(mem)
                user_memories = filtered
            
            # Return recent first, limited
            sorted_memories = sorted(user_memories, key=lambda x: x.get("timestamp", ""), reverse=True)
            return sorted_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

# Use simple memory service to avoid Mem0 issues
simple_memory_service = SimpleMemoryService()

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
            
            # Store memory using simple service (no Mem0)
            result = loop.run_until_complete(
                simple_memory_service.store_memory(
                    user_id, 
                    "user_memory", 
                    {"text": text, "tags": tags},
                    meta_data={"tags": tags}
                )
            )
            
            return result
            
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
                simple_memory_service.search_memories(user_id, "user_memory", query, 3)
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
