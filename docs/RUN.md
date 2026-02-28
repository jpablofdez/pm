# Run and Test

## Run with scripts

- macOS: `./scripts/start_mac.sh`
- Linux: `./scripts/start_linux.sh`
- Windows PowerShell: `./scripts/start_windows.ps1`

Stop:

- macOS: `./scripts/stop_mac.sh`
- Linux: `./scripts/stop_linux.sh`
- Windows PowerShell: `./scripts/stop_windows.ps1`

## Direct Docker commands

- Start: `docker compose up --build -d`
- Stop: `docker compose down`

## Verify Part 3

- Open `http://localhost:8000/` and confirm the Kanban page loads (`Kanban Studio` heading).
- Check API routes:
- `curl http://localhost:8000/api/hello`
- `curl http://localhost:8000/api/health`

## Verify Part 4

- Open `http://localhost:8000/` and confirm sign-in screen appears first.
- Sign in with:
- Username: `user`
- Password: `password`
- Confirm the Kanban board appears after sign-in.
- Click `Log out` and confirm sign-in screen appears again.

API checks:

- Unauthenticated: `curl -i http://localhost:8000/api/auth/me` should return `401`
- Login:
`curl -c /tmp/pm_auth_cookie.txt -H 'Content-Type: application/json' -d '{"username":"user","password":"password"}' http://localhost:8000/api/auth/login`
- Authenticated me:
`curl -b /tmp/pm_auth_cookie.txt http://localhost:8000/api/auth/me`
- Logout:
`curl -b /tmp/pm_auth_cookie.txt -c /tmp/pm_auth_cookie.txt -X POST http://localhost:8000/api/auth/logout`
- Me after logout:
`curl -i -b /tmp/pm_auth_cookie.txt http://localhost:8000/api/auth/me` should return `401`

## Verify Part 6

- Unauthenticated board read should fail:
`curl -i http://localhost:8000/api/board`

- Login and store cookie:
`curl -c /tmp/pm_board_cookie.txt -H 'Content-Type: application/json' -d '{"username":"user","password":"password"}' http://localhost:8000/api/auth/login`

- Read board:
`curl -b /tmp/pm_board_cookie.txt http://localhost:8000/api/board`

- Update board (example rename `Backlog` to `Roadmap`):
`curl -b /tmp/pm_board_cookie.txt http://localhost:8000/api/board > /tmp/board.json`
`sed 's/Backlog/Roadmap/' /tmp/board.json > /tmp/board_updated.json`
`curl -b /tmp/pm_board_cookie.txt -H 'Content-Type: application/json' -X PUT -d @/tmp/board_updated.json http://localhost:8000/api/board`

- Read again and confirm persisted value:
`curl -b /tmp/pm_board_cookie.txt http://localhost:8000/api/board`

## Verify Part 7

- Open `http://localhost:8000/` and sign in with `user` / `password`.
- Rename the first column title (for example, `Backlog` to `Roadmap`).
- Refresh the page.
- Confirm the renamed title remains after reload.

Optional API confirmation:

- Login and store cookie:
`curl -c /tmp/pm_board_cookie.txt -H 'Content-Type: application/json' -d '{"username":"user","password":"password"}' http://localhost:8000/api/auth/login`
- Read board:
`curl -b /tmp/pm_board_cookie.txt http://localhost:8000/api/board`

## Verify Part 8

- Ensure `.env` in project root contains:
`OPENROUTER_API_KEY=...`

- Login:
`curl -c /tmp/pm_ai_cookie.txt -H 'Content-Type: application/json' -d '{"username":"user","password":"password"}' http://localhost:8000/api/auth/login`

- Connectivity test:
`curl -b /tmp/pm_ai_cookie.txt -X POST http://localhost:8000/api/ai/test`

Expected:

- If key is missing/invalid: `500` with error detail.
- If key is valid: `200` with `model`, `prompt`, and non-empty `response` text.

## Verify Part 9

- Ensure `.env` in project root contains:
`OPENROUTER_API_KEY=...`
- Login:
`curl -c /tmp/pm_ai_chat_cookie.txt -H 'Content-Type: application/json' -d '{"username":"user","password":"password"}' http://localhost:8000/api/auth/login`
- Send AI chat request:
`curl -b /tmp/pm_ai_chat_cookie.txt -H 'Content-Type: application/json' -X POST -d '{"message":"Say hello and do not change the board","history":[]}' http://localhost:8000/api/ai/chat`

Expected:

- If key is missing/invalid or rate-limited: `500` with error detail.
- If request succeeds: `200` JSON with:
- `assistantMessage`
- `operations` array
- `boardUpdated` boolean
- `board` payload

## Verify Part 10

- Open `http://localhost:8000/` and sign in with `user` / `password`.
- In the `AI Assistant` sidebar, submit a prompt such as:
`Rename Backlog to Roadmap AI`
- Confirm the assistant response appears in the conversation.
- Confirm the first column title updates in the board UI when the AI returns `boardUpdated: true`.
- Submit a follow-up prompt and confirm conversation history keeps both user and assistant messages.

## Backend tests

From project root:

`docker run --rm -v "$PWD/backend:/work" -w /work ghcr.io/astral-sh/uv:python3.12-bookworm uv run --extra dev pytest`

## Frontend tests

From `frontend/`:

- Unit: `npm run test:unit`
- E2E: `npm run test:e2e`
