# TaskPilot

**TaskPilot is an open-source, agent-powered personal task assistant.** Chat with the service to manage reminders and tasks, save useful information, and get context-aware responses. The FastAPI backend routes user messages to CrewAI agents and persists application data in PostgreSQL.

> **Status:** Active development. This repository currently provides a FastAPI backend and a basic browser chat page. It is not production-ready: authentication, authorization, a production embedding model, and comprehensive test coverage still need work. Run it locally and do not send sensitive data to an internet-accessible deployment.

## Product direction

TaskPilot is intended to let people describe what they need in natural language and have the appropriate agents carry out supported tasks. The current code includes a personal manager agent, intent extraction, reminder/task handling, memory tools, chat history, HTTP chat, and WebSocket chat. The browser interface is a lightweight starting point for interacting with the API.

The agent should only be described as automating actions that are implemented and configured in the running deployment. Additional integrations and task capabilities are future work.

## Features

- Browser chat interface served by the FastAPI application.
- HTTP and WebSocket chat endpoints.
- CrewAI personal manager agent and message intent routing.
- PostgreSQL storage models for memories, reminders/tasks, and conversation history.
- Redis and Celery task processing support.
- Alembic migration history and FastAPI interactive API docs.
- Configurable LLM providers in the existing application code (Gemini, OpenAI, or local Ollama).

## Technology

- Python, FastAPI, and Uvicorn
- CrewAI and LiteLLM
- PostgreSQL, SQLAlchemy, Alembic, and pgvector
- Redis and Celery

## Requirements

- Python 3.10 or later
- PostgreSQL with the pgvector extension
- Redis for Celery/background work
- A configured model provider: Gemini or OpenAI credentials, or a local Ollama installation

## Quick start

### 1. Clone and set up Python

```bash
git clone https://github.com/karnansp36/fast_api.git
cd fast_api
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the pinned dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start PostgreSQL and Redis

Create a PostgreSQL database and make sure pgvector is installed on its server. Enable the extension in the database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Start PostgreSQL and Redis with your local tools. Docker Compose is not currently included in this repository.

### 3. Configure the application

Copy `.env.example` to `.env` and set database and model-provider values for your local environment. Never commit `.env` or real credentials.

```bash
cp .env.example .env
```

The API uses `DATABASE_URL` for its asynchronous SQLAlchemy connection. The Alembic configuration currently uses a synchronous PostgreSQL URL in `alembic.ini`; set that URL to the same local database before migrating. Do not put production credentials in a tracked file.

### 4. Apply migrations

```bash
alembic upgrade head
```

### 5. Run the application

Start the API in one terminal:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Visit <http://127.0.0.1:8000> to open the chat page, or <http://127.0.0.1:8000/docs> for interactive API documentation.

For background tasks, start a worker in another terminal:

```bash
celery -A app.celery_worker:celery worker --loglevel=info
```

The Celery application defines a periodic schedule. To run scheduled work, start Celery Beat separately:

```bash
celery -A app.celery_worker:celery beat --loglevel=info
```

## Configuration

See `.env.example` and `app/config.py`. At minimum, configure a valid `DATABASE_URL` and a model provider. Redis is required when using Celery tasks.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection URL for the async application database |
| `REDIS_URL` | Redis connection URL |
| `CELERY_BROKER_URL` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | Celery result backend URL |
| `GEMINI_API_KEY` | Gemini provider credential, if selected |
| `OPENAI_API_KEY` | OpenAI provider credential, if selected |
| `API_SHARED_SECRET` | Reserved configuration; do not assume endpoints are protected by it |

## API

The chat router is mounted under `/api/v1`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Browser chat interface |
| `GET` | `/health` | Basic service health response |
| `GET` | `/api/v1/health` | Chat router health response |
| `GET` | `/api/v1/chat/{user_id}?message=...` | Send a message over HTTP |
| WebSocket | `/api/v1/ws/chat/{user_id}` | Real-time chat connection |

Example HTTP request:

```bash
curl --get 'http://127.0.0.1:8000/api/v1/chat/demo-user' \
  --data-urlencode 'message=Remind me to review my notes tomorrow at 9 AM'
```

The HTTP chat endpoint waits for the agent response. For the WebSocket protocol and response fields, refer to `app/api/websocket_routes.py`.

## Project structure

```text
app/
  api/          HTTP and WebSocket endpoints
  core/         database setup and SQLAlchemy models
  crew/         agent definitions, LLM configuration, orchestration
  services/     memory, embeddings, and reminder operations
  tools/        agent tools for memory, reminders, and delegation
  web/          browser chat interface
  config.py     environment-based application settings
  main.py       FastAPI application entry point
  celery_worker.py  Celery tasks and schedule
migrations/     Alembic environment and schema revisions
requirements.txt  pinned runtime dependencies
.env.example   local configuration template (no real secrets)
CONTRIBUTING.md contribution workflow and development expectations
LICENSE        MIT license
```

## Development and contribution

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Issues and PRs should be focused, explain the user impact, and include validation steps. Never include API keys, database passwords, personal data, or `.env` contents in commits or issue reports.

## Known limitations and security

- The browser chat currently uses an automatically generated local demo user ID; there is no user authentication or authorization. Do not expose it publicly with real user data.
- The API currently uses broad CORS settings. Restrict allowed origins and add appropriate authentication and authorization before deployment.
- `app/services/embeddings.py` currently generates hash-based placeholder vectors, not semantic embeddings. Similarity retrieval is not production-grade until a real embedding model is integrated.
- Some agent tools and service methods are under development; verify each task flow before relying on it.
- Use Alembic migrations for schema changes. The app should not be treated as a substitute for reviewed production migrations.
- The repository does not yet include a comprehensive automated test suite or CI workflow. Add tests for behavior and integrations when contributing.

## License

TaskPilot is released under the MIT License. See [LICENSE](LICENSE).
