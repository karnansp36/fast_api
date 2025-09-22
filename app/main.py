# main.py - FIXED VERSION
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.websocket_routes import router as chat_router
from app.core.db import Base, engine, AsyncSessionLocal  # Import AsyncSessionLocal
from sqlalchemy import text
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from sqlalchemy import select, text
from app.core.models import ConversationHistory 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Personal Manager API...")
    
    # Create database tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
        
        # Test database connection
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        
        # Verify database tables are accessible and writable
        await verify_database_tables()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue anyway - the app might work with limited functionality
    
    # Initialize services
    try:
        from app.services.emotion_service import emotion_service
        logger.info("Emotion service initialized")
    except Exception as e:
        logger.error(f"Emotion service initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Personal Manager API...")
    await engine.dispose()

async def verify_database_tables():
    """Verify all required tables exist and are accessible"""
    try:
        
        async with AsyncSessionLocal() as session:
            # Check if conversation_history table exists and is accessible
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM conversation_history"))
                count = result.scalar()
                logger.info(f"✅ Conversation history table accessible with {count} records")
            except Exception as e:
                logger.error(f"❌ Conversation history table check failed: {e}")
                # Try to create the table if it doesn't exist
                try:
                    async with engine.begin() as conn:
                        await conn.run_sync(ConversationHistory.__table__.create)
                    logger.info("✅ Created conversation_history table")
                except Exception as create_error:
                    logger.error(f"❌ Failed to create conversation_history table: {create_error}")
                    return
            
            # Check if we can insert a test record
            try:
                test_conv = ConversationHistory(
                    user_id="system_test",
                    message="Test message during startup",
                    response="Test response during startup",
                    emotion="neutral"
                )
                session.add(test_conv)
                await session.commit()
                
                # Verify the record was inserted
                result = await session.execute(
                    select(ConversationHistory).where(ConversationHistory.user_id == "system_test")
                )
                inserted = result.scalar_one_or_none()
                
                if inserted:
                    # Clean up the test record
                    await session.delete(inserted)
                    await session.commit()
                    logger.info("✅ Conversation history table is writable and readable")
                else:
                    logger.error("❌ Failed to verify test record insertion")
                    
            except Exception as e:
                logger.error(f"❌ Conversation history table write test failed: {e}")
                # Try to rollback any partial transaction
                try:
                    await session.rollback()
                except:
                    pass
        
        # Verify other important tables
        tables_to_check = ["memories", "tasks"]
        for table_name in tables_to_check:
            try:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    logger.info(f"✅ {table_name} table accessible with {count} records")
            except Exception as e:
                logger.error(f"❌ {table_name} table check failed: {e}")
                
    except Exception as e:
        logger.error(f"❌ Database table verification failed: {e}")



app = FastAPI(
    title="Personal Manager API",
    description="Single front-facing personal manager agent with specialized workers",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Personal Manager API is running", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)