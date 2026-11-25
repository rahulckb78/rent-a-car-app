"""MySQL access: one small pool, dict rows, autocommit, explicit transactions where needed."""

import ssl
from contextlib import contextmanager
from urllib.parse import parse_qs, unquote, urlparse

import pymysql
from dbutils.pooled_db import PooledDB
from pymysql.cursors import DictCursor

from .config import DATABASE_URL, DB_SSL_VERIFY, POOL_MAX

_pool: PooledDB | None = None


def connection_kwargs(url: str | None = None) -> dict:
    url = url or DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Put your MySQL URL in .env (see .env.example).")
    u = urlparse(url)
    if u.scheme not in ("mysql", "mysql+pymysql", "mariadb"):
        raise RuntimeError("DATABASE_URL must look like mysql://user:password@host:port/dbname")
    host = u.hostname or "localhost"
    kwargs = dict(
        host=host,
        port=u.port or 3306,
        user=unquote(u.username or ""),
        password=unquote(u.password or ""),
        database=(u.path or "/").lstrip("/"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=20,
        init_command="SET time_zone = '+00:00'",  # TIMESTAMP columns (created_at) are read back as UTC
    )
    query = {k: v[0].lower() for k, v in parse_qs(u.query).items()}
    local = host in ("localhost", "127.0.0.1", "::1")
    wants_tls = (
        query.get("ssl") in ("true", "1", "required") or query.get("ssl-mode") == "required" or not local
    )
    if wants_tls and query.get("ssl") != "false":
        ctx = ssl.create_default_context()
        if not DB_SSL_VERIFY:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl"] = ctx
    return kwargs


def connect() -> pymysql.connections.Connection:
    """Plain connection for scripts (migrate, seed)."""
    return pymysql.connect(**connection_kwargs())


def open_pool() -> None:
    global _pool
    # ping=1: check the connection before handing it out (hosted MySQL drops idle connections).
    _pool = PooledDB(
        pymysql, maxconnections=POOL_MAX, mincached=1, blocking=True, ping=1, **connection_kwargs()
    )


def close_pool() -> None:
    global _pool
    if _pool:
        _pool.close()
        _pool = None


@contextmanager
def get_conn():
    assert _pool is not None, "pool not open"
    conn = _pool.connection()
    try:
        yield conn
    finally:
        conn.close()  # returns it to the pool


def fetch_all(sql: str, params=None) -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def fetch_one(sql: str, params=None) -> dict | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params=None) -> int:
    with get_conn() as conn, conn.cursor() as cur:
        return cur.execute(sql, params)


@contextmanager
def transaction():
    """Cursor inside BEGIN ... COMMIT; rolls back on any exception."""
    with get_conn() as conn:
        conn.begin()
        try:
            with conn.cursor() as cur:
                yield cur
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
