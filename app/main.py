from contextlib import asynccontextmanager
import logging
from pathlib import Path
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.websocket_routes import router as chat_router
from app.core.db import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting TaskPilot API")
    yield
    logger.info("Shutting down TaskPilot API")
    await engine.dispose()


app = FastAPI(
    title="TaskPilot API",
    description="A conversational personal assistant for memories, reminders, and agent-supported tasks.",
    version="0.2.0",
    lifespan=lifespan,
)

# The chat page and API are same-origin. Configure explicit origins if this API
# is consumed by a separate web client; do not use wildcard CORS in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(chat_router, prefix="/api/v1", tags=["chat"])


@app.get("/", include_in_schema=False)
async def chat_interface():
    return StaticFiles(directory=str(WEB_DIR), html=True)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "TaskPilot", "timestamp": time.time()}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception for %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )
