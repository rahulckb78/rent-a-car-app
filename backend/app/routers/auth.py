import re
import uuid

import pymysql
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .. import db
from ..deps import current_user_optional
from ..security import (
    COOKIE,
    RateLimiter,
    clear_cookie,
    create_session,
    delete_session,
    hash_password,
    set_cookie,
    verify_password,
)  # fmt: skip

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = RateLimiter(limit=20, window_s=300)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignUp(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)  # upper cap: argon2 on huge input is a DoS vector


class SignIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


def _public(user: dict) -> dict:
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def _throttle(request: Request) -> None:
    if not limiter.allow(request.client.host if request.client else "unknown"):
        raise HTTPException(429, "Too many attempts. Try again in a few minutes.")


@router.post("/sign-up")
def sign_up(body: SignUp, request: Request, response: Response):
    _throttle(request)
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Enter a valid email address")
    if not body.name.strip():
        raise HTTPException(400, "Name is required")
    user = {"id": str(uuid.uuid4()), "name": body.name.strip(), "email": email}
    try:
        db.execute(
            "INSERT INTO users (id, email, name, password_hash) VALUES (%s, %s, %s, %s)",
            (user["id"], email, user["name"], hash_password(body.password)),
        )
    except pymysql.err.IntegrityError as exc:  # 1062 duplicate entry on the unique email index
        if exc.args[0] == 1062:
            raise HTTPException(409, "An account with that email already exists") from exc
        raise
    set_cookie(request, response, create_session(user["id"]))
    return {"user": _public(user)}


@router.post("/sign-in")
def sign_in(body: SignIn, request: Request, response: Response):
    _throttle(request)
    row = db.fetch_one(
        "SELECT id, name, email, password_hash FROM users WHERE email = %s", (body.email.strip().lower(),)
    )
    if not verify_password(row["password_hash"] if row else None, body.password):
        raise HTTPException(401, "Invalid email or password")
    set_cookie(request, response, create_session(row["id"]))
    return {"user": _public(row)}


@router.post("/sign-out")
def sign_out(request: Request, response: Response):
    delete_session(request.cookies.get(COOKIE))
    clear_cookie(response)
    return {"ok": True}


@router.get("/me")
def me(user: dict | None = Depends(current_user_optional)):
    # 200 with null (not 401) so the SPA can ask "who am I?" at startup without console errors.
    return {"user": _public(user) if user else None}
