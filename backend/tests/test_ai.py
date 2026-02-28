import os

import pytest
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


def test_ai_test_requires_authentication() -> None:
    client = _client()
    response = client.post("/api/ai/test")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_ai_test_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = _client()
    _login(client)

    response = client.post("/api/ai/test")
    assert response.status_code == 500
    assert response.json() == {"detail": "OPENROUTER_API_KEY is not configured."}


def test_ai_test_success_with_mock(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    call_args: dict[str, str] = {}

    def fake_run_connectivity_prompt(api_key: str, prompt: str = "2+2") -> str:
        call_args["api_key"] = api_key
        call_args["prompt"] = prompt
        return "4"

    monkeypatch.setattr(ai_client, "run_connectivity_prompt", fake_run_connectivity_prompt)

    client = _client()
    _login(client)

    response = client.post("/api/ai/test")
    assert response.status_code == 200
    assert response.json() == {
        "model": "openai/gpt-oss-120b:free",
        "prompt": "2+2",
        "response": "4",
    }
    assert call_args == {"api_key": "test-key", "prompt": "2+2"}


def test_ai_test_returns_500_when_openrouter_call_fails(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_run_connectivity_prompt(api_key: str, prompt: str = "2+2") -> str:
        raise ai_client.AIConnectivityError("OpenRouter request failed.")

    monkeypatch.setattr(ai_client, "run_connectivity_prompt", fake_run_connectivity_prompt)

    client = _client()
    _login(client)

    response = client.post("/api/ai/test")
    assert response.status_code == 500
    assert response.json() == {"detail": "OpenRouter request failed."}


def test_ai_test_real_connectivity_when_key_present() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY is not configured.")

    client = _client()
    _login(client)

    response = client.post("/api/ai/test")
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "openai/gpt-oss-120b:free"
    assert body["prompt"] == "2+2"
    assert isinstance(body["response"], str)
    assert body["response"].strip()
