CREATE TABLE IF NOT EXISTS resources (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  category VARCHAR(100) NOT NULL,
  price_per_slot DECIMAL(10, 2) NOT NULL,
  rating DECIMAL(2, 1) NOT NULL,
  image VARCHAR(500) NOT NULL,
  description TEXT NOT NULL,
  capacity INT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- starts_at / ends_at are WALL-CLOCK times at the venue (DATETIME has no timezone):
-- "Court 2 at 09:00" means 09:00 where the court is, whoever looks and from wherever.
CREATE TABLE IF NOT EXISTS bookings (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id CHAR(36) NOT NULL,
  resource_id VARCHAR(64) NOT NULL,
  starts_at DATETIME NOT NULL,
  ends_at DATETIME NOT NULL,
  customer_name VARCHAR(100) NOT NULL,
  customer_email VARCHAR(254) NOT NULL,
  notes VARCHAR(500) NOT NULL DEFAULT '',
  total DECIMAL(10, 2) NOT NULL,
  status ENUM('confirmed', 'cancelled') NOT NULL DEFAULT 'confirmed',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY bookings_user_idx (user_id, starts_at),
  CONSTRAINT bookings_user_fk FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT bookings_resource_fk FOREIGN KEY (resource_id) REFERENCES resources(id),
  CONSTRAINT bookings_range_ck CHECK (ends_at > starts_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- MySQL has no exclusion constraints (Postgres' EXCLUDE ... tsrange). The equivalent: one row per
-- occupied slot with a PRIMARY KEY on (resource, slot start). Two bookings can never claim the same
-- slot, so the DATABASE rejects a double booking (duplicate key 1062 -> HTTP 409). Cancelling deletes the rows.
CREATE TABLE IF NOT EXISTS booking_slots (
  resource_id VARCHAR(64) NOT NULL,
  slot_start DATETIME NOT NULL,
  booking_id INT NOT NULL,
  PRIMARY KEY (resource_id, slot_start),
  KEY booking_slots_booking_idx (booking_id),
  CONSTRAINT booking_slots_booking_fk FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
  CONSTRAINT booking_slots_resource_fk FOREIGN KEY (resource_id) REFERENCES resources(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
