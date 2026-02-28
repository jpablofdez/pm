from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def test_login_rejects_invalid_credentials() -> None:
    response = _client().post(
        "/api/auth/login",
        json={"username": "user", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials."}


def test_auth_session_flow() -> None:
    client = _client()
    login_response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert login_response.status_code == 200
    assert login_response.json() == {"authenticated": True, "username": "user"}
    assert "pm_session=" in login_response.headers["set-cookie"]

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json() == {"authenticated": True, "username": "user"}

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"authenticated": False}

    me_after_logout_response = client.get("/api/auth/me")
    assert me_after_logout_response.status_code == 401
    assert me_after_logout_response.json() == {"detail": "Not authenticated."}


def test_me_rejects_invalid_cookie() -> None:
    client = _client()
    client.cookies.set("pm_session", "invalid-cookie")
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}
