# services/rag.py (updated)
from app.services.memory_service import memory_service
from typing import List

async def store_memory(user_id: str, text_content: str, tags: List[str] = None) -> str:
    """Store user memory with embedding"""
    try:
        content = {
            "text": text_content,
            "tags": tags or [],
            "source": "user_input"
        }
        
        return await memory_service.store_memory(
            user_id, 
            "user_memory", 
            content,
            meta_data={"tags": tags or []}
        )
    except Exception as e:
        return f"Error storing memory: {str(e)}"

async def search_memory(user_id: str, query: str = "", limit: int = 5) -> List[str]:
    """Search user memories"""
    try:
        memories = await memory_service.search_memories(user_id, "user_memory", query, limit)
        return [mem["text"] for mem in memories]
    except Exception as e:
        return [f"Error searching memory: {str(e)}"]