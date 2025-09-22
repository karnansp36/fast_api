# app/core/db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import asyncpg
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True, pool_pre_ping=True)

# Use async_sessionmaker correctly - remove the class_ parameter
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

async def get_session() -> AsyncSession:
    """Get a fresh async session for each request"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_asyncpg_conn():
    """Get a raw asyncpg connection (separate from SQLAlchemy sessions)"""
    return await asyncpg.connect(settings.DATABASE_URL.replace("+asyncpg", ""))

__all__ = ['engine', 'AsyncSessionLocal', 'Base', 'get_session', 'get_asyncpg_conn']