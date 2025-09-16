# models.py
from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from app.core.db import Base

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False)
    text = Column(Text, nullable=False)
    memory_type = Column(String(50), default="general")  # general, preference, fact, episodic
    meta_data = Column(JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    embedding = Column(Vector(1536))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False)
    text = Column(Text, nullable=False)
    due_time = Column(TIMESTAMP(timezone=True))
    status = Column(String, default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    emotion = Column(String(20))  # detected emotion
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())