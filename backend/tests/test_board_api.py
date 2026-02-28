import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200


def test_board_requires_authentication(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PM_MVP_DB_PATH", str(tmp_path / "pm.db"))
    client = TestClient(app)

    get_response = client.get("/api/board")
    put_response = client.put("/api/board", json={"columns": [], "cards": {}})

    assert get_response.status_code == 401
    assert put_response.status_code == 401


def test_board_db_is_created_and_seeded_on_first_read(
    tmp_path: Path, monkeypatch
) -> None:
    db_path = tmp_path / "pm.db"
    monkeypatch.setenv("PM_MVP_DB_PATH", str(db_path))
    client = TestClient(app)
    _login(client)

    assert not db_path.exists()

    response = client.get("/api/board")
    assert response.status_code == 200
    body = response.json()

    assert db_path.exists()
    assert "columns" in body
    assert "cards" in body
    assert len(body["columns"]) == 5
    assert len(body["cards"]) == 8

    with sqlite3.connect(db_path) as connection:
        user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        board_count = connection.execute("SELECT COUNT(*) FROM boards").fetchone()[0]
        assert user_count == 1
        assert board_count == 1


def test_board_update_persists_per_user(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PM_MVP_DB_PATH", str(tmp_path / "pm.db"))
    client = TestClient(app)
    _login(client)

    initial_response = client.get("/api/board")
    assert initial_response.status_code == 200
    board = initial_response.json()
    board["columns"][0]["title"] = "Roadmap"
    board["cards"]["card-1"]["title"] = "Updated title"

    update_response = client.put("/api/board", json=board)
    assert update_response.status_code == 200
    assert update_response.json()["columns"][0]["title"] == "Roadmap"

    refreshed_response = client.get("/api/board")
    assert refreshed_response.status_code == 200
    refreshed_board = refreshed_response.json()
    assert refreshed_board["columns"][0]["title"] == "Roadmap"
    assert refreshed_board["cards"]["card-1"]["title"] == "Updated title"


def test_board_update_rejects_invalid_payload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PM_MVP_DB_PATH", str(tmp_path / "pm.db"))
    client = TestClient(app)
    _login(client)

    invalid_board = {
        "columns": [
            {
                "id": "col-backlog",
                "title": "Backlog",
                "cardIds": ["missing-card"],
            }
        ],
        "cards": {},
    }

    response = client.put("/api/board", json=invalid_board)
    assert response.status_code == 422
