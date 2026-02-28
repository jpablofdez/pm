FROM node:24-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY backend ./backend
COPY --from=frontend-builder /frontend/out ./backend/static/frontend
RUN uv sync --project ./backend --frozen --no-dev

EXPOSE 8000

CMD ["/app/backend/.venv/bin/python", "-m", "uvicorn", "app.main:app", "--app-dir", "/app/backend", "--host", "0.0.0.0", "--port", "8000"]
