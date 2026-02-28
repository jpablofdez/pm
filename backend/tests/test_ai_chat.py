from pathlib import Path

from fastapi.testclient import TestClient

from app import ai_client
from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200


def test_ai_chat_requires_authentication() -> None:
    client = _client()
    response = client.post("/api/ai/chat", json={"message": "hello", "history": []})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_ai_chat_requires_api_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PM_MVP_DB_PATH", str(tmp_path / "pm.db"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    client = _client()
    _login(client)

    response = client.post("/api/ai/chat", json={"message": "hello", "history": []})
    assert response.status_code == 500
    assert response.json() == {"detail": "OPENROUTER_API_KEY is not configured."}


def test_ai_chat_applies_operations_and_persists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PM_MVP_DB_PATH", str(tmp_path / "pm.db"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_run_kanban_chat(
        api_key: str,
        board_data: dict[str, object],
        history: list[dict[str, str]],
        message: str,
    ) -> dict[str, object]:
        assert api_key == "test-key"
        assert isinstance(board_data, dict)
        assert history == [{"role": "user", "content": "previous"}]
        assert message == "Please rename backlog and add a card."
        return {
            "assistant_response": "Done. I renamed Backlog and added a card.",
            "operations": [
                {
                    "type": "rename_column",
                    "columnId": "col-backlog",
                    "title": "Roadmap",
                },
                {
                    "type": "create_card",
                    "columnId": "col-backlog",
                    "title": "New AI card",
                    "details": "Created by AI",
                    "cardId": "card-ai-test",
                },
            ],
        }

    monkeypatch.setattr(ai_client, "run_kanban_chat", fake_run_kanban_chat)

    client = _client()
    _login(client)

    response = client.post(
        "/api/ai/chat",
        json={
            "message": "Please rename backlog and add a card.",
            "history": [{"role": "user", "content": "previous"}],
        },
    )
    assert response.status_code == 200
    body = response.json()

    assert body["assistantMessage"] == "Done. I renamed Backlog and added a card."
    assert body["boardUpdated"] is True
    assert body["board"]["columns"][0]["title"] == "Roadmap"
    assert body["board"]["cards"]["card-ai-test"]["title"] == "New AI card"

    board_response = client.get("/api/board")
    assert board_response.status_code == 200
    board = board_response.json()
    assert board["columns"][0]["title"] == "Roadmap"
    assert "card-ai-test" in board["cards"]


def test_ai_chat_without_operations_does_not_change_board(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("PM_MVP_DB_PATH", str(tmp_path / "pm.db"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_run_kanban_chat(
        api_key: str,
        board_data: dict[str, object],
        history: list[dict[str, str]],
        message: str,
    ) -> dict[str, object]:
        return {
            "assistant_response": "No changes needed.",
            "operations": [],
        }

    monkeypatch.setattr(ai_client, "run_kanban_chat", fake_run_kanban_chat)

    client = _client()
    _login(client)
    original_board = client.get("/api/board").json()

    response = client.post("/api/ai/chat", json={"message": "What do you see?", "history": []})
    assert response.status_code == 200
    body = response.json()
    assert body["boardUpdated"] is False

    board_after = client.get("/api/board").json()
    assert board_after == original_board


def test_ai_chat_applies_operations_atomically(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("PM_MVP_DB_PATH", str(tmp_path / "pm.db"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_run_kanban_chat(
        api_key: str,
        board_data: dict[str, object],
        history: list[dict[str, str]],
        message: str,
    ) -> dict[str, object]:
        return {
            "assistant_response": "I tried to rename and update a card.",
            "operations": [
                {
                    "type": "rename_column",
                    "columnId": "col-backlog",
                    "title": "Roadmap",
                },
                {
                    "type": "update_card",
                    "cardId": "card-missing",
                    "title": "Should fail",
                },
            ],
        }

    monkeypatch.setattr(ai_client, "run_kanban_chat", fake_run_kanban_chat)

    client = _client()
    _login(client)
    original_board = client.get("/api/board").json()

    response = client.post(
        "/api/ai/chat",
        json={"message": "rename backlog and update missing card", "history": []},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "Card 'card-missing' was not found."}

    board_after = client.get("/api/board").json()
    assert board_after == original_board
    assert board_after["columns"][0]["title"] == "Backlog"


def test_ai_chat_returns_500_for_invalid_structured_output(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("PM_MVP_DB_PATH", str(tmp_path / "pm.db"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_run_kanban_chat(
        api_key: str,
        board_data: dict[str, object],
        history: list[dict[str, str]],
        message: str,
    ) -> dict[str, object]:
        return {"assistant_response": "", "operations": "oops"}

    monkeypatch.setattr(ai_client, "run_kanban_chat", fake_run_kanban_chat)

    client = _client()
    _login(client)

    response = client.post("/api/ai/chat", json={"message": "hello", "history": []})
    assert response.status_code == 500
