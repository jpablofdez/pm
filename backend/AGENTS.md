# Backend

This directory contains the FastAPI backend for the Project Management MVP.

## Scope in Parts 2-9

- Serve static HTML at `/`
- Serve built frontend static export at `/`
- Serve JSON APIs under `/api`
- Handle dummy auth session endpoints under `/api/auth`
- Persist board data in SQLite via `/api/board` endpoints
- Provide OpenRouter connectivity test endpoint at `/api/ai/test`
- Provide structured AI chat endpoint at `/api/ai/chat` with board operations
- Run in Docker on port `8000`
- Include backend tests for route behavior

## Structure

- `app/` FastAPI application package
- `app/ai_client.py` OpenRouter connectivity helper
- `app/ai_kanban.py` structured AI chat/operation models and board mutation logic
- `app/database.py` SQLite initialization and board persistence helpers
- `app/kanban_schema.py` board payload schema and default board seed
- `static/` static assets served by the backend
- `tests/` backend test suite
- `pyproject.toml` Python dependencies and test config managed by `uv`
