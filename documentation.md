# Personal Manager with CrewAI - Features and Tools

## Overview

This project is a FastAPI microservice designed to provide multi-agent AI capabilities using CrewAI. It leverages various tools and libraries to offer features such as API endpoints, database interaction, and real-time communication via WebSockets.

## Key Features

*   **API Endpoints:** Provides API endpoints for various functionalities, including chat and other services.
*   **Database Interaction:** Uses a PostgreSQL database for data storage.
*   **WebSockets:** Enables real-time communication.
*   **Multi-Agent AI Capabilities:** Utilizes CrewAI for managing multiple AI agents.
*   **Memory Storage:** Includes memory storage capabilities.
*   **Agent Routing:** Supports agent routing.
*   **Authentication/API Keys:** Implements API key-based authentication.
*   **Logging:** Includes logging functionality for monitoring and debugging.
*   **Feature Flags:** Uses feature flags for enabling/disabling features.

## Tools and Libraries

*   **FastAPI:** Web framework for building APIs.
*   **Uvicorn:** ASGI server for running the FastAPI application.
*   **Pydantic:** Data validation and settings management.
*   **python-dotenv:** Loads environment variables from a `.env` file.
*   **SQLAlchemy:** SQL toolkit and Object-Relational Mapper.
*   **asyncpg:** PostgreSQL database client library for asyncio.
*   **psycopg2-binary:** PostgreSQL adapter for Python.
*   **alembic:** Database migration tool.
*   **redis:** Key-value store for caching.
*   **celery:** Distributed task queue.
*   **google-genai:** Google Gemini SDK.
*   **langchain:** Framework for developing applications with language models.
*   **langchain-google-genai:** Langchain wrapper for Gemini.
*   **langchain-postgres:** PGVector vector store.
*   **crewai:** Multi-agent framework.
*   **crewai-tools:** (Optional) if you want stock tools (web, etc.).
*   **pgvector:** Vector database extension.
*   **litellm:** Library for interacting with LLMs.
*   **Google Gemini API:** Used for interacting with Gemini models.
*   **Ollama:** Used for running local LLMs.

## Configuration

The project uses a `.env` file for configuration, including database URLs, API keys, and other settings.
