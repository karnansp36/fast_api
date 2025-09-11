# models.py - Fix user_id type inconsistency
from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
import uuid
from app.core.db import Base

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Keep as String for consistency
    text = Column(Text, nullable=False)
    meta_data = Column(JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    embedding = Column(Vector(1536))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)  # Changed from UUID to String for consistency
    text = Column(Text, nullable=False)
    due_time = Column(TIMESTAMP(timezone=True))
    status = Column(String, default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
