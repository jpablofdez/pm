# Database Model (Part 5)

## Goal

Define a simple SQLite schema that supports:

- multiple users (future-safe)
- exactly one board per user for MVP
- board state stored as JSON

This is a schema proposal only. Implementation is planned for Part 6.

## SQLite File

- Proposed path: `backend/data/pm.db`
- Create database file automatically if it does not exist.

## Schema

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## Why this shape

- `users.username UNIQUE`: guarantees one account per username.
- `boards.user_id UNIQUE`: enforces one board per user (MVP rule).
- `board_json` with `json_valid(...)`: stores flexible Kanban state while still validating JSON format at DB level.
- Timestamp fields support auditing and future sync/debug.

## JSON Contract for `boards.board_json`

`board_json` stores the frontend `BoardData` shape:

```json
{
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"] }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Example card",
      "details": "Example details"
    }
  }
}
```

Minimum validation in backend application layer (Part 6):

- `columns` is an array.
- each column has `id`, `title`, `cardIds`.
- `cards` is a dictionary keyed by card id.
- each card has `id`, `title`, `details`.
- every `cardIds` entry exists in `cards`.

## MVP auth alignment

- Current login is fixed (`user` / `password`).
- In Part 6, the backend will ensure a corresponding user row exists (seed/upsert) and link that user to a single board row.
- `password_hash` is included now for future real auth migration; for MVP, values can be seeded deterministically.

## Out of scope in Part 5

- no DB writes/reads implemented yet
- no migrations framework yet
- no board history/versioning table yet
- no chat history persistence yet
