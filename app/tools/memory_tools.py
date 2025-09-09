# tools/memory_tools.py
from crewai_tools import BaseTool
from services.rag import store_memory, search_memory
from typing import Type, List
from pydantic import BaseModel, Field
import asyncio

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
        """Store memory synchronously"""
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(store_memory(user_id, text, tags))
            loop.close()
            return result
        except Exception as e:
            return f"Error storing memory: {str(e)}"

class SearchMemoryInput(BaseModel):
    """Input schema for SearchMemoryTool"""
    user_id: str = Field(..., description="User ID to search memories for")
    query: str = Field(default="", description="Search query to find relevant memories")

class SearchMemoryTool(BaseTool):
    name: str = "search_memory"
    description: str = "Search and retrieve user memories based on query"
    args_schema: Type[BaseModel] = SearchMemoryInput
    
    def _run(self, user_id: str, query: str = "") -> str:
        """Search memory synchronously"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            memories = loop.run_until_complete(search_memory(user_id, query))
            loop.close()
            
            if memories:
                return f"Found memories: {'; '.join(memories[:3])}"
            else:
                return "No relevant memories found"
        except Exception as e:
            return f"Error searching memory: {str(e)}"