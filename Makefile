# Everyday commands. Backend venv lives in backend/.venv, frontend deps in frontend/node_modules.
PY := backend/.venv/bin/python
export NG_CLI_ANALYTICS := false

.PHONY: setup migrate seed dev api web build lint smoke

setup:            ## create venv, install backend + frontend deps
	python3 -m venv backend/.venv
	$(PY) -m pip install -q -r backend/requirements-dev.txt
	cd frontend && npm install

migrate:          ## apply auth + app schema (idempotent)
	cd backend && .venv/bin/python migrate.py

seed:             ## upsert seed data (idempotent)
	cd backend && .venv/bin/python seed.py

dev:              ## API on :8000 (reload) + Angular on :4200 (proxies /api)
	$(PY) scripts/dev.py

api:
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port $${PORT:-8000}

web:
	cd frontend && npm start

build:            ## production Angular build -> frontend/dist/browser (served by the API)
	cd frontend && npm run build

lint:             ## ruff + strict Angular compile
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	cd frontend && npm run build

smoke:            ## end-to-end checks against a RUNNING server (BASE_URL=... for a deployed one)
	$(PY) backend/smoke.py
