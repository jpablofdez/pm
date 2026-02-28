import base64
import binascii
import hashlib
import hmac
import os
import time
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.database import load_board_for_user, save_board_for_user
from app.kanban_schema import BoardModel

BASE_DIR = Path(__file__).resolve().parent.parent
FALLBACK_INDEX_FILE = BASE_DIR / "static" / "index.html"
FRONTEND_DIST_DIR = BASE_DIR / "static" / "frontend"

AUTH_COOKIE_NAME = "pm_session"
AUTH_USERNAME = "user"
AUTH_PASSWORD = "password"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 12
SESSION_SECRET = os.getenv("PM_MVP_SESSION_SECRET", "pm-mvp-dev-secret")

app = FastAPI(title="PM MVP Backend")


class LoginRequest(BaseModel):
    username: str
    password: str


def _create_session_token(username: str) -> str:
    issued_at = str(int(time.time()))
    payload = f"{username}:{issued_at}"
    signature = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode(
        "utf-8"
    )


def _get_session_user(session_token: str | None) -> str | None:
    if not session_token:
        return None

    try:
        decoded = base64.urlsafe_b64decode(session_token.encode("utf-8")).decode("utf-8")
        username, issued_at, signature = decoded.split(":")
    except (UnicodeDecodeError, ValueError, binascii.Error):
        return None

    payload = f"{username}:{issued_at}"
    expected_signature = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        issued_at_int = int(issued_at)
    except ValueError:
        return None

    if int(time.time()) - issued_at_int > SESSION_MAX_AGE_SECONDS:
        return None

    return username


def _require_authenticated_username(session_token: str | None) -> str:
    username = _get_session_user(session_token)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return username


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "hello world"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> JSONResponse:
    if payload.username != AUTH_USERNAME or payload.password != AUTH_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    response = JSONResponse({"authenticated": True, "username": payload.username})
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=_create_session_token(payload.username),
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE_SECONDS,
        path="/",
    )
    return response


@app.get("/api/auth/me")
def me(
    session_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> dict[str, str | bool]:
    username = _get_session_user(session_token)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return {"authenticated": True, "username": username}


@app.post("/api/auth/logout")
def logout() -> JSONResponse:
    response = JSONResponse({"authenticated": False})
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    return response


@app.get("/api/board")
def get_board(
    session_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> dict[str, object]:
    username = _require_authenticated_username(session_token)
    return load_board_for_user(username)


@app.put("/api/board")
def update_board(
    payload: BoardModel,
    session_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> dict[str, object]:
    username = _require_authenticated_username(session_token)
    board_data = payload.model_dump()
    save_board_for_user(username, board_data)
    return board_data


if FRONTEND_DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
else:

    @app.get("/", include_in_schema=False)
    def root() -> FileResponse:
        return FileResponse(FALLBACK_INDEX_FILE)
