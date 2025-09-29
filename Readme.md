# 🤖 Personal Manager AI Microservice

A **Personal Assistant Microservice** built with **FastAPI**, **CrewAI**, **PostgreSQL (`pgvector`)**, **Redis**, and **Celery**.  
This service acts as a personal manager capable of **empathetic conversations**, **task scheduling**, and **memory management**.  

---

## ✨ Features

### ✅ Implemented
- **Empathetic Conversation**
  - Natural, human-like interactions powered by CrewAI agents.  
- **Memory Management**
  - **Store Memories:** “Remember my preference for coffee.”  
  - **Search Memories:** Retrieve relevant info for contextual replies.  
- **Task / Reminder Management**
  - **Create Reminders:** “Remind me to call mom tomorrow at 10 AM.”  
  - **Get Reminders:** Fetch pending tasks and reminders.  
- **Asynchronous Task Delegation**
  - Long-running tasks handled in the background with **Celery**.  
- **Conversation History**
  - All messages stored for continuity.  
- **Configurable LLMs**
  - Works with **Gemini**, **OpenAI**, and **Ollama** via environment config.  
- **WebSocket API**
  - Real-time chat interface for interactive conversations.  
- **Robust Error Handling**
  - Global exception handling for API and WebSocket.  
- **Database Initialization**
  - Auto-creates and validates database schema at startup.  

### 🚀 Planned / Projected
- **Emotion Service Integration** (for detecting user emotions).  
- **More Specialized Agents** (beyond the Personal Manager).  
- **Advanced RAG** (with `pgvector` for smarter context retrieval).  
- **User Preferences** (dedicated preference management system).  

---

## 🏗️ Architecture

The system follows a **microservice architecture** built around FastAPI.

- **FastAPI App (`main.py`)**
  - Routes, middleware, DB lifecycle, error handling.  
- **Database (PostgreSQL + `pgvector`)**
  - Stores **memories**, **tasks**, and **conversation history**.  
- **Redis**
  - Message broker + Celery result backend.  
- **Celery**
  - Handles background jobs (e.g., reminder creation).  
- **CrewAI**
  - Orchestrates AI agents.  
  - **Orchestrator (`orchestrator.py`)**: Handles user input → intent detection → agent execution.  
  - **Personal Manager Agent**: Empathetic AI agent with task/memory tools.  
- **Services (`app/services/`)**
  - `memory_service.py` → memory CRUD.  
  - `reminders.py` → task/reminder management.  
  - `embeddings.py` → text embeddings (placeholder).  
- **Tools (`app/tools/`)**
  - Memory tools: `StoreMemoryTool`, `SearchMemoryTool`.  
  - Reminder tools: `CreateReminderTool`, `GetRemindersTool`.  
  - Delegation: `AsyncDelegationTool`.  
- **API Endpoints**
  - WebSocket: `ws/chat/{user_id}`  
  - HTTP: `/chat/{user_id}` (basic testing).  

---

## 🗄️ Data Models

### `Memory`
| Field       | Type       | Description |
|-------------|------------|-------------|
| id          | UUID       | Primary key |
| user_id     | String     | User identifier |
| text        | Text       | Content of memory |
| memory_type | String     | e.g. general, preference, episodic |
| meta_data   | JSON       | Extra info |
| embedding   | Vector     | `pgvector` embedding |
| created_at  | Timestamp  | Creation time |

### `Task`
| Field      | Type       | Description |
|------------|------------|-------------|
| id         | UUID       | Primary key |
| user_id    | String     | User identifier |
| text       | Text       | Task description |
| due_time   | DateTime   | Optional deadline |
| status     | String     | pending / completed |
| created_at | Timestamp  | Created at |
| updated_at | Timestamp  | Last update |

### `ConversationHistory`
| Field      | Type       | Description |
|------------|------------|-------------|
| id         | UUID       | Primary key |
| user_id    | String     | User identifier |
| message    | Text       | User’s input |
| response   | Text       | AI response |
| emotion    | String     | Detected emotion (future) |
| created_at | Timestamp  | Interaction time |

---

## ⚙️ Configuration

Environment variables are managed via `.env` and `pydantic_settings`.

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `CELERY_BROKER_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | Celery result backend |
| `GEMINI_API_KEY` | API key for Gemini |
| `OPENAI_API_KEY` | API key for OpenAI |
| `OLLAMA_HOST`, `OLLAMA_MODEL` | Ollama settings |
| `EMBEDDING_DIMENSIONS` | Vector embedding size |
| `SHORT_MEMORY_MAXLEN` | Max conversation memory length |
| `RAG_TOP_K` | Retrieval chunk size |
| Feature flags | `ENABLE_WEBSOCKETS`, `ENABLE_MEMORY_STORAGE`, `ENABLE_AGENT_ROUTING` |

---

## 🧠 AI Orchestration

- **PersonalManagerOrchestrator**
  - Routes messages.  
  - Detects intents (memory, reminder, conversation).  
  - Gathers context (conversation, memories, preferences, pending tasks).  
  - Creates CrewAI task → delegates to **Personal Manager Agent**.  

- **Personal Manager Agent**
  - **Role:** Personal Manager & Assistant.  
  - **Goal:** Empathetic, context-aware interaction.  
  - **Backstory:** Warm, human-like personality.  
  - **Tools:** `StoreMemoryTool`, `SearchMemoryTool`, `CreateReminderTool`, `GetRemindersTool`, `AsyncDelegationTool`.  

---

## 🔌 API Endpoints

### WebSocket
- `GET /ws/chat/{user_id}` → Real-time chat.  

### HTTP
- `/` → API status.  
- `/health` → Health check.  
- `/api/v1/health` → Health check.  
- `/api/v1/chat/{user_id}?message=...` → Test chat via HTTP.  

---

## 🚀 Setup & Run

1. **Clone repo**  
   ```bash
   git clone <repo-url>
   cd personal-manager-ai


Install dependencies

pip install -r requirements.txt


Set environment variables in .env.

Run Postgres & Redis (Docker recommended).

Start Celery worker

celery -A app.celery_worker worker --loglevel=info


Run FastAPI app

uvicorn app.main:app --host 0.0.0.0 --port 8000

⚠️ Note on Emotion Service

main.py references app/services/emotion_service.py, but the file is missing.
This likely indicates planned emotion detection functionality that is not yet implemented.