"""Upsert seed data by id so re-running edits rows instead of failing or duplicating."""

from app.data.resources import RESOURCES
from app.db import connect

SQL = """INSERT INTO resources (id, name, category, price_per_slot, rating, image, description, capacity)
         VALUES (%(id)s, %(name)s, %(category)s, %(price_per_slot)s, %(rating)s, %(image)s, %(description)s, %(capacity)s)
         ON DUPLICATE KEY UPDATE name = VALUES(name), category = VALUES(category),
           price_per_slot = VALUES(price_per_slot), rating = VALUES(rating), image = VALUES(image),
           description = VALUES(description), capacity = VALUES(capacity)"""

conn = connect()
try:
    with conn.cursor() as cur:
        cur.executemany(SQL, RESOURCES)
    print(f"Seeded {len(RESOURCES)} cars.")
finally:
    conn.close()
