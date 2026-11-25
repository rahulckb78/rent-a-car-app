# RentACar

Pick a car and drive away in minutes.

Angular (frontend) + FastAPI (API) + MySQL + cookie-session auth, served as one web service.

## Run locally
```bash
cp .env.example .env     # (already done by the scaffold) then set DATABASE_URL
make setup               # venv + npm install
make migrate seed        # schema + sample data
make dev                 # API http://localhost:8000, app http://localhost:4200
make smoke               # end-to-end checks against the running API
```
`make lint` runs ruff and a strict Angular compile. `make build` builds the frontend into `frontend/dist/browser`, which the API serves on its own origin.

## Configuration (`.env`, never committed)
| Variable | Meaning |
|---|---|
| `DATABASE_URL` | MySQL URL `mysql://user:pass@host:port/db` (TLS automatic for non-local hosts) |
| `PORT` | API port for local dev (default 8000) |
| `BUSINESS_TZ`, `SLOT_MINUTES`, `OPEN_HOUR`, `CLOSE_HOUR`, `MAX_SLOTS_PER_BOOKING`, `MAX_DAYS_AHEAD` | booking rules |
| `SESSION_DAYS` | sign-in lifetime |
| `ALLOWED_ORIGINS` | optional extra origins for state-changing requests |

## Deploy (Render, Docker)
`render.yaml` defines one Docker web service. Render dashboard → New → Blueprint → pick this repo, then set `DATABASE_URL`. The container runs `python migrate.py` then uvicorn on every start. Seed once with `make seed` using the production `DATABASE_URL`.
