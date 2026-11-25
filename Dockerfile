# One image serves the API and the built Angular app from a single origin.

# ---- 1. build the Angular frontend ----
FROM node:24-slim AS web
ENV NG_CLI_ANALYTICS=false
WORKDIR /web
COPY frontend/package*.json ./
# Lockfile is created by the first `npm install`; fall back if it is missing.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend/ ./
RUN npm run build

# ---- 2. Python runtime ----
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 STATIC_DIR=/app/static
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist/browser ./static
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
# Migrations run on every start (idempotent), then the API. Render injects $PORT.
CMD ["sh", "-c", "python migrate.py && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
