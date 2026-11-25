"""Apply migrations/*.sql in filename order, each exactly once (tracked in schema_migrations).

Safe to run on every deploy and from several instances at once (GET_LOCK serialises them).
MySQL has no transactional DDL and no ADD COLUMN IF NOT EXISTS: to change the schema, ADD A NEW FILE
(003_add_specialty.sql); never edit one that has already been applied.
"""

import re
import sys
from pathlib import Path

from app.db import connect

DIR = Path(__file__).parent / "migrations"


def statements(sql: str) -> list[str]:
    sql = re.sub(r"--[^\n]*", "", sql)  # strip line comments (no ';' inside string literals in migrations)
    return [s.strip() for s in sql.split(";") if s.strip()]


def main() -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT GET_LOCK('app_migrate', 60) AS got")
        if not cur.fetchone()["got"]:
            raise RuntimeError("Could not get the migration lock")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " name VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        cur.execute("SELECT name FROM schema_migrations")
        done = {r["name"] for r in cur.fetchall()}
        applied = 0
        for path in sorted(DIR.glob("*.sql")):
            if path.name in done:
                continue
            for stmt in statements(path.read_text()):
                cur.execute(stmt)
            cur.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
            print(f"Applied {path.name}")
            applied += 1
        print("Schema up to date." if not applied else f"{applied} migration(s) applied.")
        cur.execute("SELECT RELEASE_LOCK('app_migrate')")
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Migration failed: {exc}", file=sys.stderr)
        sys.exit(1)
