# Project Plan

## Part 1: Plan

- [x] User confirmed and approved the implementation plan.

## Part 2: Scaffolding

### Objective

Create a runnable Dockerized FastAPI baseline that serves static HTML at `/` and JSON APIs under `/api`.

### Checklist

- [x] Create backend FastAPI app in `backend/app/`.
- [x] Add routes: `GET /`, `GET /api/hello`, `GET /api/health`.
- [x] Serve `/` from `backend/static/index.html`.
- [x] Add client-side fetch from `/` to `/api/hello`.
- [x] Add `backend/pyproject.toml` with runtime and test dependencies.
- [x] Generate `backend/uv.lock` via `uv`.
- [x] Add root `Dockerfile` for backend service.
- [x] Add root `docker-compose.yml` exposing port `8000`.
- [x] Add scripts:
- [x] `scripts/start_mac.sh`
- [x] `scripts/stop_mac.sh`
- [x] `scripts/start_linux.sh`
- [x] `scripts/stop_linux.sh`
- [x] `scripts/start_windows.ps1`
- [x] `scripts/stop_windows.ps1`
- [x] Add backend route tests.
- [x] Validate backend tests pass.
- [x] Validate container smoke tests pass.

### Tests

- Backend tests:
- `GET /` returns `200` and `text/html`.
- `GET /api/hello` returns `{"message":"hello world"}`.
- `GET /api/health` returns `{"status":"ok"}`.
- Smoke tests:
- Build and run with `docker compose up --build -d`.
- `curl http://localhost:8000/` returns HTML.
- `curl http://localhost:8000/api/hello` returns expected JSON.
- `curl http://localhost:8000/api/health` returns expected JSON.
- Stop with `docker compose down`.

### Success Criteria

- `http://localhost:8000/` serves static HTML and displays API result from `/api/hello`.
- API contracts match exactly.
- Backend tests pass.
- Docker smoke checks pass.
- Required OS scripts exist and execute expected compose commands.

## Part 3: Add in Frontend

### Objective

Serve the existing Next.js Kanban demo from FastAPI at `/` using a static export built inside Docker.

### Checklist

- [x] Configure Next.js static export.
- [x] Add frontend build stage in `Dockerfile`.
- [x] Copy exported frontend into backend static directory in container image.
- [x] Update backend app to serve exported frontend at `/`.
- [x] Keep API routes available under `/api`.
- [x] Add frontend directory documentation (`frontend/AGENTS.md`).
- [x] Validate frontend unit tests pass.
- [x] Validate frontend e2e tests pass.
- [x] Validate backend tests still pass.
- [x] Validate Docker smoke checks for Kanban at `/`.

### Tests

- Frontend unit tests: `cd frontend && npm run test:unit`
- Frontend e2e tests: `cd frontend && npm run test:e2e`
- Backend tests: `docker run --rm -v "$PWD/backend:/work" -w /work ghcr.io/astral-sh/uv:python3.12-bookworm uv run --extra dev pytest -q`
- Docker smoke tests:
- `./scripts/start_mac.sh` (or Linux/Windows equivalent)
- `curl http://localhost:8000/` contains `Kanban Studio`
- `curl http://localhost:8000/api/hello` returns expected JSON
- `curl http://localhost:8000/api/health` returns expected JSON
- `./scripts/stop_mac.sh` (or Linux/Windows equivalent)

### Success Criteria

- `http://localhost:8000/` renders the Kanban board UI (static Next export).
- FastAPI API routes under `/api` continue to work unchanged.
- Frontend unit and e2e tests pass.
- Backend tests pass.
- Docker run/smoke checks pass.

## Part 4: Add in a fake user sign in experience

### Objective

Require sign in before showing the board, using dummy credentials with backend-managed HttpOnly cookie session and logout support.

### Checklist

- [x] Add backend auth endpoints:
- [x] `POST /api/auth/login`
- [x] `GET /api/auth/me`
- [x] `POST /api/auth/logout`
- [x] Validate credentials against `user` / `password`.
- [x] Issue and validate HttpOnly session cookie.
- [x] Add frontend auth gate so `/` requires sign in before board access.
- [x] Add logout control in board UI.
- [x] Add backend auth tests.
- [x] Add frontend auth unit tests.
- [x] Add frontend e2e test for login + logout flow.
- [x] Validate containerized auth flow with smoke checks.

### Tests

- Backend tests: `docker run --rm -v "$PWD/backend:/work" -w /work ghcr.io/astral-sh/uv:python3.12-bookworm uv run --extra dev pytest -q`
- Frontend unit tests: `cd frontend && npm run test:unit`
- Frontend e2e tests: `cd frontend && npm run test:e2e`
- Container auth smoke tests:
- `GET /api/auth/me` without cookie returns `401`
- `POST /api/auth/login` with `user` / `password` returns success and sets cookie
- `GET /api/auth/me` with cookie returns authenticated user
- `POST /api/auth/logout` clears session
- `GET /api/auth/me` after logout returns `401`
- Browser flow: `/` shows sign in, successful sign in shows Kanban, logout returns to sign in.

### Success Criteria

- On first load of `/`, user must sign in to access Kanban.
- Only `user` / `password` signs in successfully.
- Session is managed by backend HttpOnly cookie.
- Logout returns user to signed-out state.
- Backend, frontend unit, and frontend e2e tests all pass.
- Containerized smoke checks pass for auth endpoints and browser flow.

## Part 5: Database modeling

### Objective

Define and document the SQLite schema for persistent Kanban storage as JSON.

### Checklist

- [x] Propose SQLite schema for users + boards.
- [x] Enforce one-board-per-user constraint at DB level.
- [x] Define JSON storage field and contract.
- [x] Document DB approach in `docs/DATABASE.md`.
- [x] Add SQL DDL reference file in `docs/sqlite_schema.sql`.
- [x] Get user sign-off on schema before implementation in Part 6.

### Proposed Tables

- `users`
- `boards`

### Success Criteria

- Schema is documented and decision-complete for implementation.
- One board per user is enforced by DB constraints.
- JSON board structure and validation expectations are documented.
- User explicitly approves before Part 6 backend persistence implementation.

## Part 6: Backend

### Objective

Implement backend persistence APIs so authenticated users can read and update their board in SQLite.

### Checklist

- [x] Add SQLite access layer for users + board JSON persistence.
- [x] Auto-create database file and tables when missing.
- [x] Add authenticated `GET /api/board`.
- [x] Add authenticated `PUT /api/board`.
- [x] Create default board row when user has no board yet.
- [x] Persist board updates and return updated payload.
- [x] Add backend tests for auth protection, DB creation, read, write, and validation.
- [x] Validate container smoke checks for board read/update flow.

### Tests

- Backend tests: `docker run --rm -v "$PWD/backend:/work" -w /work ghcr.io/astral-sh/uv:python3.12-bookworm uv run --extra dev pytest -q`
- Board API smoke tests:
- `GET /api/board` without auth returns `401`
- login with `user` / `password`
- `GET /api/board` returns board JSON
- `PUT /api/board` persists updates
- subsequent `GET /api/board` returns persisted data

### Success Criteria

- Backend reads/writes board state per authenticated user.
- SQLite file/tables are created automatically when missing.
- Invalid board payloads are rejected.
- Backend tests pass with persistence coverage.
- Containerized smoke checks pass for board endpoints.

## Part 7: Frontend + Backend

### Objective

Connect frontend board interactions to backend board APIs so the board persists across reloads.

### Checklist

- [x] Load board state from `GET /api/board` after authentication.
- [x] Persist board mutations through `PUT /api/board`.
- [x] Keep existing board interactions (rename, add, delete, drag/move) working.
- [x] Add frontend unit coverage for API-backed board sync.
- [x] Update e2e coverage to include board API integration behavior.
- [x] Validate containerized browser persistence flow (change -> reload persists).

### Tests

- Frontend unit tests: `cd frontend && npm run test:unit`
- Frontend e2e tests: `cd frontend && npm run test:e2e`
- Backend tests: `docker run --rm -v "$PWD/backend:/work" -w /work ghcr.io/astral-sh/uv:python3.12-bookworm uv run --extra dev pytest -q`
- Browser persistence smoke:
- Login at `/`
- Change board data in UI (for example, rename first column)
- Reload page
- Confirm changed value remains

### Success Criteria

- Board loads from backend API instead of frontend-only seed state.
- Any board change in UI persists to backend.
- Reloading page keeps latest board state.
- Frontend and backend test suites pass.
- Browser-level persistence smoke check passes.

## Part 8: AI connectivity

### Objective

Add backend connectivity to OpenRouter using `openai/gpt-oss-120b:free`, with a simple `2+2` verification route.

### Checklist

- [x] Add backend AI client for OpenRouter chat completions.
- [x] Add authenticated `POST /api/ai/test` endpoint with fixed prompt `2+2`.
- [x] Return model name, prompt, and model response payload.
- [x] Return simple `500` errors for missing key and upstream failures.
- [x] Wire Docker Compose to load `OPENROUTER_API_KEY` automatically from `.env` when present.
- [x] Add backend tests for auth, missing key, success path, and error path.
- [x] Add real connectivity test that is skipped if `OPENROUTER_API_KEY` is missing.
- [x] Run live model call and confirm real answer from OpenRouter in this environment.

### Tests

- Backend tests: `docker run --rm -v "$PWD/backend:/work" -w /work ghcr.io/astral-sh/uv:python3.12-bookworm uv run --extra dev pytest -q`
- Connectivity endpoint behavior:
- login with `user` / `password`
- `POST /api/ai/test` returns `500` if key missing
- `POST /api/ai/test` returns `200` and model text when key is configured and valid

### Success Criteria

- Backend can call OpenRouter model `openai/gpt-oss-120b:free`.
- Endpoint returns a model response for prompt `2+2` when key is configured.
- Failures are returned as simple `500` responses.
- Tests pass, with live connectivity test skipped when no key is available.

## Part 9: Structured Outputs + Board Context

### Objective

Add an authenticated AI chat backend route that sends board context to OpenRouter, requires structured JSON output, and applies board mutations atomically.

### Checklist

- [x] Add AI chat request/response models and operation schemas.
- [x] Send board JSON, chat history, and user message to model `openai/gpt-oss-120b:free`.
- [x] Require structured JSON output containing `assistant_response` and `operations`.
- [x] Add authenticated `POST /api/ai/chat` endpoint.
- [x] Validate model output with Pydantic before applying operations.
- [x] Apply operations atomically and only persist on full success.
- [x] Return response contract with assistant message, operations, update flag, and board payload.
- [x] Add backend tests for auth, missing key, success path, no-op path, invalid structured output, and atomic rollback on failure.
- [x] Validate container smoke call for `/api/ai/chat`.

### Tests

- Backend tests:
`docker run --rm -v "$PWD/backend:/work" -w /work ghcr.io/astral-sh/uv:python3.12-bookworm uv run --extra dev pytest -q`
- AI chat smoke:
- login with `user` / `password`
- `POST /api/ai/chat` with `{"message":"...","history":[]}`
- verify response includes:
- `assistantMessage` (string)
- `operations` (array)
- `boardUpdated` (boolean)
- `board` (valid board JSON)

### Success Criteria

- `/api/ai/chat` accepts board-aware chat requests for authenticated users.
- Model output is enforced as structured JSON before mutation logic.
- Board operations are applied as all-or-nothing and do not partially persist.
- Response contract is stable for Part 10 frontend integration.
- Backend tests and container smoke checks pass.

## Part 10: AI sidebar UX

Add sidebar chat UI in frontend, display conversation history, submit prompts, and auto-refresh board when backend applies AI-generated updates.
