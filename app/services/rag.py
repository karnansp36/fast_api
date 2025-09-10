# services/rag.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.core.models import Memory
from app.services.embeddings import embed_text
from typing import List

async def store_memory(user_id: str, text_content: str, tags: List[str] = None) -> str:
    """Store user memory with embedding"""
    try:
        embedding = embed_text(text_content)
        
        async with AsyncSessionLocal() as session:
            memory = Memory(
                user_id=user_id,
                text=text_content,
                metadata={"tags": tags or []},
                # embedding=embedding  # Uncomment if using pgvector
            )
            session.add(memory)
            await session.commit()
            return f"Memory stored successfully: {text_content[:50]}..."
    except Exception as e:
        return f"Error storing memory: {str(e)}"

async def search_memory(user_id: str, query: str = "", limit: int = 5) -> List[str]:
    """Search user memories"""
    try:
        async with AsyncSessionLocal() as session:
            if query:
                result = await session.execute(
                    select(Memory.text).where(
                        Memory.user_id == user_id,
                        Memory.text.ilike(f"%{query}%")
                    ).limit(limit)
                )
            else:
                result = await session.execute(
                    select(Memory.text).where(
                        Memory.user_id == user_id
                    ).limit(limit)
                )
            memories = result.scalars().all()
            return [memory for memory in memories]
    except Exception as e:
        return [f"Error searching memory: {str(e)}"]