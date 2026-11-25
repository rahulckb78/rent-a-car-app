import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from . import db
from .config import ALLOWED_ORIGINS, STATIC_DIR
from .errors import install_error_handlers
from .routers import ROUTERS

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.open_pool()
    yield
    db.close_pool()


app = FastAPI(
    title="RentACar",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)
install_error_handlers(app)


@app.middleware("http")
async def origin_guard(request: Request, call_next):
    """CSRF defence on top of SameSite=Lax cookies: a state-changing request that names an Origin must be
    same-origin (Origin == this request's own scheme://host) or explicitly allowed. Browsers always send
    Origin on cross-site POSTs; scripts/curl send none and are let through (they have no ambient cookies)."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin")
        own = f"{request.url.scheme}://{request.headers.get('host', '')}"
        if origin and origin.rstrip("/") != own and origin.rstrip("/") not in ALLOWED_ORIGINS:
            return JSONResponse({"error": "Origin not allowed"}, status_code=403)
    return await call_next(request)


@app.get("/api/health")
def health():
    return {"ok": True}


for router in ROUTERS:
    app.include_router(router)


# Registered last: anything not matched above. Unknown /api paths must be a JSON 404 (not index.html),
# real files in the Angular build are served as-is, every other GET falls back to index.html (client routing).
@app.api_route(
    "/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False
)
def spa(full_path: str, request: Request):
    if full_path == "api" or full_path.startswith("api/") or request.method != "GET":
        return JSONResponse({"error": "Not found"}, status_code=404)
    root = STATIC_DIR.resolve()
    candidate = (root / full_path).resolve()
    if full_path and candidate.is_file() and candidate.is_relative_to(root):  # no path traversal
        return FileResponse(candidate)
    if (
        "." in full_path.rsplit("/", 1)[-1]
    ):  # a missing file (main-XXXX.js, .map, ...) is a 404, not index.html
        return JSONResponse({"error": "Not found"}, status_code=404)
    index = root / "index.html"
    if index.is_file():
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
    return JSONResponse(
        {"error": "Frontend not built. Run `make build`, or use the dev server on :4200."}, status_code=404
    )
