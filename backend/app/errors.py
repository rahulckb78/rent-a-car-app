import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("app")


def install_error_handlers(app: FastAPI) -> None:
    # FastAPI's default error body is {"detail": ...} and validation errors are 422.
    # The frontend expects {"error": "<message>"} everywhere, and 400 for bad input.
    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        return JSONResponse({"error": f"{field}: {first['msg']}" if field else first["msg"]}, status_code=400)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        log.exception("Unhandled error", exc_info=exc)
        return JSONResponse({"error": "Internal server error"}, status_code=500)
