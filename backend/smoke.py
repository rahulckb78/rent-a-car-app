"""End-to-end smoke test against a RUNNING server (stdlib only).
  make smoke                          -> http://localhost:$PORT (default 8000)
  BASE_URL=https://app.onrender.com make smoke
Creates throwaway users, books a slot, proves double booking is rejected (also under 4 simultaneous
requests), checks ownership, then cancels."""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

BASE = os.environ.get("BASE_URL", f"http://localhost:{os.environ.get('PORT', '8000')}").rstrip("/")
failures = 0


def check(label: str, ok: bool, detail="") -> None:
    global failures
    print(f"{'PASS' if ok else 'FAIL'}  {label}{'' if ok else '  ' + str(detail)}")
    failures += 0 if ok else 1


class Client:
    def __init__(self):
        self.cookie = ""

    def call(self, path, method="GET", body=None, headers=None):
        req = urllib.request.Request(
            BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
            headers={"Origin": BASE, **({"Content-Type": "application/json"} if body is not None else {}),
                     **({"Cookie": self.cookie} if self.cookie else {}), **(headers or {})},
        )  # fmt: skip
        try:
            resp = urllib.request.urlopen(req, timeout=60)
        except urllib.error.HTTPError as err:
            resp = err
        cookies = resp.headers.get_all("Set-Cookie") or []
        if cookies:
            self.cookie = "; ".join(c.split(";")[0] for c in cookies)
        raw = resp.read()
        try:
            data = json.loads(raw)
        except ValueError:
            data = None
        return resp.status, data


a, b = Client(), Client()
s, d = a.call("/api/health")
check("health endpoint", s == 200 and d == {"ok": True}, (s, d))
s, d = a.call("/api/does-not-exist")
check("unknown /api path is a JSON 404", s == 404 and isinstance(d, dict) and "error" in d, (s, d))
s, d = a.call("/api/resources")
check("list resources", s == 200 and isinstance(d, list) and len(d) > 0, (s, d))
rid = d[0]["id"] if s == 200 and d else ""
s, _ = a.call("/api/bookings/mine")
check("protected route rejects anonymous", s == 401, s)
s, _ = a.call("/api/bookings", method="POST", body={}, headers={"Origin": "https://evil.example"})
check("foreign Origin rejected on state-changing request", s == 403, s)

stamp = int(time.time() * 1000)
email_a, email_b = f"smoke+a{stamp}@example.com", f"smoke+b{stamp}@example.com"
s, d = a.call(
    "/api/auth/sign-up", "POST", {"name": "Smoke A", "email": email_a, "password": "smoke-test-pass-1"}
)
check("sign up", s == 200 and a.cookie.startswith("session="), (s, d))
s, d = Client().call(
    "/api/auth/sign-up", "POST", {"name": "Dup", "email": email_a.upper(), "password": "smoke-test-pass-1"}
)
check("duplicate email (any case) rejected with 409", s == 409, (s, d))
s, d = a.call("/api/auth/me")
check("me returns the user", s == 200 and d["user"]["email"] == email_a, (s, d))
s, d = Client().call("/api/auth/sign-in", "POST", {"email": email_a, "password": "wrong-password"})
check("wrong password rejected with 401", s == 401, (s, d))
s, d = b.call(
    "/api/auth/sign-up", "POST", {"name": "Smoke B", "email": email_b, "password": "smoke-test-pass-1"}
)
check("second user signs up", s == 200, (s, d))

day = (date.today() + timedelta(days=3)).isoformat()
s, avail = a.call(f"/api/resources/{rid}/availability?date={day}")
free = next((x for x in avail if x["available"]), None) if s == 200 else None
check("availability has a free slot", free is not None, (s, str(avail)[:200]))
payload = {"resourceId": rid, "date": day, "startTime": free and free["start"], "slots": 1, "name": "Smoke A"}

s, first = a.call("/api/bookings", "POST", payload)
check("create booking", s == 201 and "bookingId" in first, (s, first))
s, d = a.call("/api/bookings", "POST", payload)
check("double booking rejected with 409", s == 409, (s, d))
s, d = b.call("/api/bookings", "POST", payload)
check("double booking by another user rejected with 409", s == 409, (s, d))
s, avail2 = a.call(f"/api/resources/{rid}/availability?date={day}")
check("slot now unavailable", next(x for x in avail2 if x["start"] == free["start"])["available"] is False)
s, d = a.call("/api/bookings", "POST", {**payload, "startTime": "03:07"})
check("invalid time rejected with 400", s == 400, (s, d))
s, d = a.call("/api/bookings", "POST", {**payload, "slots": "two"})
check("wrong type rejected with 400 (not 422)", s == 400, (s, d))
s, d = a.call("/api/bookings", "POST", {**payload, "date": "2020-01-01"})
check("past date rejected with 400", s == 400, (s, d))
s, d = a.call("/api/bookings/mine")
check("my bookings lists it", s == 200 and any(x["id"] == first.get("bookingId") for x in d), (s, d))
s, d = b.call(f"/api/bookings/{first.get('bookingId')}/cancel", "POST", {})
check("another user cannot cancel it (404)", s == 404, (s, d))
s, d = a.call(f"/api/bookings/{first.get('bookingId')}/cancel", "POST", {})
check("owner cancels", s == 200, (s, d))
s, d = a.call(f"/api/bookings/{first.get('bookingId')}/cancel", "POST", {})
check("cancelling twice is 404", s == 404, (s, d))

# Four simultaneous identical requests: exactly one may win.
with ThreadPoolExecutor(4) as pool:
    results = list(pool.map(lambda _: a.call("/api/bookings", "POST", payload), range(4)))
codes = sorted(r[0] for r in results)
check("4 concurrent requests -> exactly one 201, three 409", codes == [201, 409, 409, 409], codes)
winner = next((r[1]["bookingId"] for r in results if r[0] == 201), None)
if winner:
    a.call(f"/api/bookings/{winner}/cancel", "POST", {})

old_cookie = a.cookie
a.call("/api/auth/sign-out", "POST", {})
replay = Client()
replay.cookie = old_cookie  # replay the pre-sign-out token: it must be dead server-side
s, d = replay.call("/api/bookings/mine")
check("old session token is invalid after sign-out", s == 401, (s, d))

print(f"\n{failures} check(s) failed" if failures else "\nAll checks passed")
sys.exit(1 if failures else 0)
