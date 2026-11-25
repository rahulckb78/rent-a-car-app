from fastapi import HTTPException, Request

from .security import COOKIE, user_for_token


def current_user_optional(request: Request) -> dict | None:
    return user_for_token(request.cookies.get(COOKIE))


def current_user(request: Request) -> dict:
    user = current_user_optional(request)
    if not user:
        raise HTTPException(401, "Sign in required")
    return user
