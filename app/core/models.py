from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector   # ✅ correct
from sqlalchemy.sql import func
import uuid
from app.core.db import Base

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    text = Column(Text, nullable=False)
    meta_data = Column(JSON, default={})  
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    embedding = Column(Vector(1536))  # adjust dimension to your embedding model

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    text = Column(Text, nullable=False)
    due_time = Column(TIMESTAMP(timezone=True))
    status = Column(String, default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
