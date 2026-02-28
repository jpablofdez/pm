import json
import os
import sqlite3
from pathlib import Path

from app.kanban_schema import DEFAULT_BOARD_DATA

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "pm.db"
DEFAULT_PASSWORD_HASH = "mvp_dummy_password_hash"

SCHEMA_SQL = """
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
"""


def get_db_path() -> Path:
    configured_path = os.getenv("PM_MVP_DB_PATH")
    if configured_path:
        return Path(configured_path)
    return DEFAULT_DB_PATH


def _connect() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.executescript(SCHEMA_SQL)
    return connection


def _get_or_create_user_id(connection: sqlite3.Connection, username: str) -> int:
    user_row = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if user_row:
        return int(user_row["id"])

    cursor = connection.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, DEFAULT_PASSWORD_HASH),
    )
    return int(cursor.lastrowid)


def load_board_for_user(username: str) -> dict[str, object]:
    with _connect() as connection:
        user_id = _get_or_create_user_id(connection, username)
        board_row = connection.execute(
            "SELECT board_json FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if not board_row:
            default_board_json = json.dumps(DEFAULT_BOARD_DATA)
            connection.execute(
                "INSERT INTO boards (user_id, board_json) VALUES (?, ?)",
                (user_id, default_board_json),
            )
            return json.loads(default_board_json)

        board_data = json.loads(str(board_row["board_json"]))
        return board_data


def save_board_for_user(username: str, board_data: dict[str, object]) -> None:
    board_json = json.dumps(board_data)

    with _connect() as connection:
        user_id = _get_or_create_user_id(connection, username)
        connection.execute(
            """
            INSERT INTO boards (user_id, board_json)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              board_json = excluded.board_json,
              updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, board_json),
        )
