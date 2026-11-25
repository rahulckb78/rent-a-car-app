import hashlib
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Request, Response

from . import db
from .config import SESSION_DAYS

COOKIE = "session"
_ph = PasswordHasher()
_DUMMY_HASH = _ph.hash("not-a-real-password")  # verified when the email is unknown, to equalise timing


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    try:
        return _ph.verify(stored_hash or _DUMMY_HASH, password) and stored_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id: str) -> str:
    """Opaque random token; only its hash is stored, so a DB leak does not leak live sessions."""
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    db.execute("DELETE FROM sessions WHERE expires_at < UTC_TIMESTAMP()")
    db.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, %s)",
        (_digest(token), user_id, expires),
    )
    return token


def user_for_token(token: str | None) -> dict | None:
    if not token:
        return None
    return db.fetch_one(
        """SELECT u.id, u.name, u.email FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = %s AND s.expires_at > UTC_TIMESTAMP()""",
        (_digest(token),),
    )


def delete_session(token: str | None) -> None:
    if token:
        db.execute("DELETE FROM sessions WHERE token_hash = %s", (_digest(token),))


def set_cookie(request: Request, response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True, samesite="lax",
        secure=request.url.scheme == "https", path="/",
    )  # fmt: skip


def clear_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/")


class RateLimiter:
    """Sliding window per key, in memory (fine for one instance; use Redis if you scale out)."""

    def __init__(self, limit: int, window_s: int):
        self.limit, self.window = limit, window_s
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True
