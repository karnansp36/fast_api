# core/models.py - UPDATED
from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from app.core.db import Base
import uuid

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)  # Added index
    text = Column(Text, nullable=False)
    memory_type = Column(String(50), default="general", index=True)  # Added index
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Changed to DateTime
    embedding = Column(Vector(1536))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)  # Added index
    text = Column(Text, nullable=False)
    due_time = Column(DateTime(timezone=True), index=True)  # Changed to DateTime
    status = Column(String(20), default="pending", index=True)  # Added index
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Changed to DateTime
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)  # Added index
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    emotion = Column(String(20), index=True)  # Added index
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Changed to DateTime