import pymysql
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .. import db
from ..config import CLOSE_HOUR, MAX_DAYS_AHEAD, MAX_SLOTS_PER_BOOKING, OPEN_HOUR, SLOT_MINUTES
from ..deps import current_user
from ..timeutil import days_between, is_valid_date, parse_time_to_minutes, venue_now

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


class BookingIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    resource_id: str = Field(alias="resourceId", min_length=1, max_length=64)
    date: str
    start_time: str = Field(alias="startTime")
    slots: int = 1
    name: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default="", max_length=500)


def to_booking(row: dict) -> dict:
    return {
        "id": row["id"],
        "resourceId": row["resource_id"],
        "resourceName": row["resource_name"],
        "date": row["date"],
        "startTime": row["start_time"],
        "endTime": row["end_time"],
        "notes": row["notes"],
        "total": float(row["total"]),
        "status": row["status"],
        "createdAt": row["created_at"],
    }


@router.post("", status_code=201)
def create_booking(body: BookingIn, user: dict = Depends(current_user)):
    if not body.name.strip():
        raise HTTPException(400, "name is required")
    if not is_valid_date(body.date):
        raise HTTPException(400, "date must be YYYY-MM-DD")
    if not 1 <= body.slots <= MAX_SLOTS_PER_BOOKING:
        raise HTTPException(400, f"slots must be an integer from 1 to {MAX_SLOTS_PER_BOOKING}")

    start_min = parse_time_to_minutes(body.start_time)
    if start_min is None:
        raise HTTPException(400, "startTime must be HH:MM")
    end_min = start_min + body.slots * SLOT_MINUTES
    aligned = (start_min - OPEN_HOUR * 60) % SLOT_MINUTES == 0
    if not aligned or start_min < OPEN_HOUR * 60 or end_min > CLOSE_HOUR * 60:
        raise HTTPException(400, "That time is outside opening hours")

    today, now_min = venue_now()
    if body.date < today or (body.date == today and start_min <= now_min):
        raise HTTPException(400, "That time has already passed")
    if days_between(today, body.date) > MAX_DAYS_AHEAD:
        raise HTTPException(400, f"Bookings open up to {MAX_DAYS_AHEAD} days ahead")

    resource = db.fetch_one("SELECT price_per_slot FROM resources WHERE id = %s", (body.resource_id,))
    if not resource:
        raise HTTPException(404, "Car not found")
    # Price is always computed here from the DB, never taken from the client.
    total = resource["price_per_slot"] * body.slots

    def stamp(minute: int) -> str:
        return f"{body.date} {minute // 60:02d}:{minute % 60:02d}:00"

    try:
        with db.transaction() as cur:
            cur.execute(
                """INSERT INTO bookings (user_id, resource_id, starts_at, ends_at, customer_name, customer_email, notes, total)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (user["id"], body.resource_id, stamp(start_min), stamp(end_min), body.name.strip(),
                 user["email"], body.notes or "", total),
            )  # fmt: skip
            booking_id = cur.lastrowid
            # One row per slot; the PRIMARY KEY (resource_id, slot_start) is what makes double booking impossible.
            cur.executemany(
                "INSERT INTO booking_slots (resource_id, slot_start, booking_id) VALUES (%s, %s, %s)",
                [(body.resource_id, stamp(m), booking_id) for m in range(start_min, end_min, SLOT_MINUTES)],
            )
    except pymysql.err.IntegrityError as exc:
        if (
            exc.args[0] == 1062
        ):  # duplicate key: another booking holds one of these slots; whole transaction rolled back
            raise HTTPException(409, "That time was just taken. Please pick another slot.") from exc
        raise
    return {"bookingId": booking_id, "total": float(total)}


@router.get("/mine")
def my_bookings(user: dict = Depends(current_user)):
    rows = db.fetch_all(
        """SELECT b.id, b.resource_id, r.name AS resource_name,
                  DATE_FORMAT(b.starts_at, '%%Y-%%m-%%d') AS date,
                  DATE_FORMAT(b.starts_at, '%%H:%%i') AS start_time,
                  DATE_FORMAT(b.ends_at, '%%H:%%i') AS end_time,
                  b.notes, b.total, b.status,
                  DATE_FORMAT(b.created_at, '%%Y-%%m-%%dT%%H:%%i:%%sZ') AS created_at
             FROM bookings b JOIN resources r ON r.id = b.resource_id
            WHERE b.user_id = %s
            ORDER BY b.starts_at DESC""",
        (user["id"],),
    )
    return [to_booking(r) for r in rows]


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: int, user: dict = Depends(current_user)):
    with db.transaction() as cur:
        # Owner-scoped: someone else's id behaves exactly like a missing one (404).
        changed = cur.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = %s AND user_id = %s AND status = 'confirmed'",
            (booking_id, user["id"]),
        )
        if changed == 0:
            raise HTTPException(404, "Rental not found or already cancelled")
        cur.execute("DELETE FROM booking_slots WHERE booking_id = %s", (booking_id,))  # frees the slots
    return {"ok": True}
