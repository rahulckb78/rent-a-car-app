import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")  # real environment variables (Render) win over the file


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else default


DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DB_SSL_VERIFY = os.environ.get("DB_SSL_VERIFY", "true").lower() != "false"
POOL_MAX = _int("POOL_MAX", 5)

# Extra browser origins allowed to make state-changing requests. The app's own origin is always allowed.
ALLOWED_ORIGINS = {
    o.strip().rstrip("/") for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
}
SESSION_DAYS = _int("SESSION_DAYS", 30)

STATIC_DIR = Path(os.environ.get("STATIC_DIR") or ROOT / "frontend" / "dist" / "browser")

# Booking rules (tennis: 60 min, 7-22h | doctor: 30 min, 9-17h | salon: 30 min, 10-19h).
SLOT_MINUTES = _int("SLOT_MINUTES", 60)
OPEN_HOUR = _int("OPEN_HOUR", 8)
CLOSE_HOUR = _int("CLOSE_HOUR", 20)
MAX_SLOTS_PER_BOOKING = _int("MAX_SLOTS_PER_BOOKING", 4)
MAX_DAYS_AHEAD = _int("MAX_DAYS_AHEAD", 60)
BUSINESS_TZ = os.environ.get("BUSINESS_TZ", "UTC")
ZoneInfo(BUSINESS_TZ)  # fail fast on a typo'd zone name
