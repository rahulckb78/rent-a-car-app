from fastapi import APIRouter, HTTPException

from .. import db
from ..config import CLOSE_HOUR, MAX_DAYS_AHEAD, MAX_SLOTS_PER_BOOKING, OPEN_HOUR, SLOT_MINUTES
from ..timeutil import days_between, format_minutes, is_valid_date, venue_now

router = APIRouter(prefix="/api/resources", tags=["resources"])


def to_resource(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "pricePerSlot": float(
            row["price_per_slot"]
        ),  # DECIMAL arrives as Decimal -> would serialise as a string
        "rating": float(row["rating"]),
        "image": row["image"],
        "description": row["description"],
        "capacity": row["capacity"],
    }


@router.get("")
def list_resources():
    return [to_resource(r) for r in db.fetch_all("SELECT * FROM resources ORDER BY name ASC")]


@router.get("/{resource_id}")
def get_resource(resource_id: str):
    row = db.fetch_one("SELECT * FROM resources WHERE id = %s", (resource_id,))
    if not row:
        raise HTTPException(404, "Car not found")
    return {
        **to_resource(row),
        "slotMinutes": SLOT_MINUTES,
        "openHour": OPEN_HOUR,
        "closeHour": CLOSE_HOUR,
        "maxSlots": MAX_SLOTS_PER_BOOKING,
        "maxDaysAhead": MAX_DAYS_AHEAD,
    }


@router.get("/{resource_id}/availability")
def availability(resource_id: str, date: str = ""):
    """[{start: '09:00', end: '10:00', available: true}, ...] for one day."""
    if not is_valid_date(date):
        raise HTTPException(400, "date must be YYYY-MM-DD")
    if not db.fetch_one("SELECT 1 AS x FROM resources WHERE id = %s", (resource_id,)):
        raise HTTPException(404, "Car not found")

    taken = {
        r["t"]
        for r in db.fetch_all(
            """SELECT DATE_FORMAT(slot_start, '%%H:%%i') AS t FROM booking_slots
                WHERE resource_id = %s AND slot_start >= %s AND slot_start < DATE_ADD(%s, INTERVAL 1 DAY)""",
            (resource_id, date, date),
        )
    }
    today, now_min = venue_now()
    past_day = date < today
    too_far = days_between(today, date) > MAX_DAYS_AHEAD

    slots = []
    for start in range(OPEN_HOUR * 60, CLOSE_HOUR * 60 - SLOT_MINUTES + 1, SLOT_MINUTES):
        label = format_minutes(start)
        past = past_day or (date == today and start <= now_min)
        slots.append(
            {"start": label, "end": format_minutes(start + SLOT_MINUTES),
             "available": label not in taken and not past and not too_far}
        )  # fmt: skip
    return slots
