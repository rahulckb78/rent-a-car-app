import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .config import BUSINESS_TZ

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def is_valid_date(value) -> bool:
    if not isinstance(value, str) or not _DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def days_between(a: str, b: str) -> int:
    """Whole days b - a for YYYY-MM-DD strings, timezone-free."""
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def parse_time_to_minutes(value) -> int | None:
    m = _TIME_RE.match(value) if isinstance(value, str) else None
    return int(m[1]) * 60 + int(m[2]) if m else None


def format_minutes(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


def venue_now() -> tuple[str, int]:
    """(today 'YYYY-MM-DD', minutes since midnight) at the venue, not on the server."""
    now = datetime.now(ZoneInfo(BUSINESS_TZ))
    return now.strftime("%Y-%m-%d"), now.hour * 60 + now.minute
