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