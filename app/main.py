# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.db import engine
from app.core.models import Base
from app.api.websocket_routes import router as websocket_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database setup error: {e}")
    
    yield
    
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="Personal Manager with CrewAI",
    description="A FastAPI microservice using CrewAI for multi-agent AI capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(websocket_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Personal Manager with CrewAI is running",
        "docs": "/docs",
        "websocket": "/api/v1/ws/chat/{user_id}",
        "http_chat": "/api/v1/chat/{user_id}?message=your_message"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)