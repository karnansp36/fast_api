# Personal Manager API

A FastAPI service for a conversational personal assistant. It combines CrewAI-based message routing with PostgreSQL-backed memories, tasks, and conversation history, and offers HTTP and WebSocket chat interfaces. Redis and Celery provide background task processing.

> **Project status:** This repository is an evolving project, not a production-ready service. Review the security and operational notes before deploying it with real users or data.

## Features

- Conversational responses routed through CrewAI agents and a configurable language model.
- Persistent memories, reminders/tasks, and conversation history in PostgreSQL.
- HTTP chat endpoint and real-time WebSocket chat.
- Redis-backed Celery worker for background tasks.
- SQLAlchemy models and Alembic migration history.
- FastAPI interactive API documentation.

## Technology

- Python, FastAPI, and Uvicorn
- CrewAI and LiteLLM for agent and model orchestration
- PostgreSQL, SQLAlchemy, Alembic, and pgvector
- Redis and Celery for background work

## Requirements

- Python 3.10 or later
- PostgreSQL with the [pgvector](https://github.com/pgvector/pgvector) extension installed
- Redis (used by Celery)
- An LLM provider: Gemini or OpenAI credentials, or a locally running Ollama service

## Installation

### 1. Clone the repository and create a virtual environment

```bash
git clone https://github.com/karnansp36/fast_api.git
cd fast_api
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

The root `requirements.txt` is the repository's pinned dependency list.

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure PostgreSQL and Redis

Create a PostgreSQL database, install pgvector on the server, and enable the extension in the project database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Start Redis and PostgreSQL using your preferred local setup. This repository does not currently include a Docker Compose file.

### 4. Configure environment variables

Create a `.env` file in the repository root and set values for your environment:

```dotenv
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/<database>
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
GEMINI_API_KEY=<your-gemini-api-key>
# Or use an OpenAI key if that is your configured provider:
OPENAI_API_KEY=<your-openai-api-key>
```

Set only the provider credentials you need, and never commit real secrets. The application currently has development fallback values in `app/config.py`; explicitly configure `DATABASE_URL` and review `API_SHARED_SECRET` before running outside a local development environment. The LLM selection logic is in `app/crew/llm_config.py`; Ollama fallback expects a local Ollama service.

### 5. Prepare the database

Alembic migrations are provided. Before running them, update `sqlalchemy.url` in `alembic.ini` to point to your development database (do not put production credentials in a committed file), then run:

```bash
alembic upgrade head
```

The application also attempts to create tables at startup. For production database changes, use and review migrations rather than relying on automatic schema creation.

### 6. Run the API and worker

In separate terminals, with the virtual environment activated:

```bash
# API
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# Celery worker
celery -A app.celery_worker:celery worker --loglevel=info
```

The worker configuration also defines a periodic task. If you need scheduled tasks to run, start Celery Beat separately:

```bash
celery -A app.celery_worker:celery beat --loglevel=info
```

Open <http://127.0.0.1:8000/docs> for interactive API documentation. The root and health routes can be used for a quick check.

## API overview

Routes below reflect the `/api/v1` prefix configured in `app.main`:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic service status |
| `GET` | `/health` | Health response |
| `GET` | `/api/v1/health` | Chat router health response |
| `GET` | `/api/v1/chat/{user_id}?message=...` | Send a chat message over HTTP |
| WebSocket | `/api/v1/ws/chat/{user_id}` | Real-time chat connection |

Example HTTP request:

```bash
curl --get 'http://127.0.0.1:8000/api/v1/chat/demo-user' \
  --data-urlencode 'message=Hello'
```

The WebSocket accepts a plain-text message or JSON containing a `message` field. See the interactive docs and `app/api/websocket_routes.py` for response shapes and current behavior.

## Repository layout

```text
app/
  api/          HTTP and WebSocket routes
  core/         database setup and SQLAlchemy models
  crew/         agents, LLM configuration, and orchestration
  services/     memory, embeddings, and reminder operations
  tools/        agent tools for memory, reminders, and delegation
  main.py       FastAPI application and lifecycle
  celery_worker.py  Celery application and task definitions
migrations/     Alembic environment and schema revisions
requirements.txt  Pinned Python dependencies
```

## Development notes and known limitations

- The embedding function in `app/services/embeddings.py` is hash-based placeholder logic, not a semantic embedding model. Do not treat vector search results as production-quality semantic retrieval without replacing it.
- `app/main.py` configures permissive CORS and includes development-oriented startup behavior. Add appropriate authentication, authorization, CORS restrictions, secret management, and deployment settings before exposing the service publicly.
- The checked-in `alembic.ini` includes a database URL. Replace it for local development and avoid storing credentials in source control.
- The root requirements file is a large pinned environment snapshot. Consider maintaining a smaller direct-dependency manifest and a tested lock file as the project matures.
- Tests and automated CI are not currently documented in this repository. Verify the service and its external integrations in your own environment.

## Contributing

Contributions are welcome. For changes, please open an issue to discuss substantial work, use a focused pull request, and include relevant tests or reproducible validation steps. Never include API keys, database credentials, or personal data in commits or issue reports.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.
