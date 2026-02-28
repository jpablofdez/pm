# Backend

This directory contains the FastAPI backend for the Project Management MVP.

## Scope in Parts 2-8

- Serve static HTML at `/`
- Serve built frontend static export at `/`
- Serve JSON APIs under `/api`
- Handle dummy auth session endpoints under `/api/auth`
- Persist board data in SQLite via `/api/board` endpoints
- Provide OpenRouter connectivity test endpoint at `/api/ai/test`
- Run in Docker on port `8000`
- Include backend tests for route behavior

## Structure

- `app/` FastAPI application package
- `app/ai_client.py` OpenRouter connectivity helper
- `app/database.py` SQLite initialization and board persistence helpers
- `app/kanban_schema.py` board payload schema and default board seed
- `static/` static assets served by the backend
- `tests/` backend test suite
- `pyproject.toml` Python dependencies and test config managed by `uv`
