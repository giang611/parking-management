"""Locust workload: authenticate, park, look up, then retrieve each vehicle."""

from __future__ import annotations

import os
import random
import time
from uuid import uuid4

from locust import HttpUser, StopUser, between, task


class GateParkingUser(HttpUser):
    """A simulated gate that completes one vehicle's full parking round trip."""

    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        self.username = os.getenv("ADMIN_USERNAME", "")
        self.password = os.getenv("ADMIN_PASSWORD", "")
        if not self.username or not self.password:
            raise StopUser("Set ADMIN_USERNAME and ADMIN_PASSWORD before starting Locust.")
        self.token: str | None = None
        self.token_expiry_seconds = 3600
        self.token_created_at = 0.0
        self._login()

    def _login(self) -> None:
        with self.client.post(
            "/api/v1/auth/login",
            json={"username": self.username, "password": self.password},
            name="POST /api/v1/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"login returned HTTP {response.status_code}")
                raise StopUser("Gate login failed; check test credentials.")
            try:
                body = response.json()
                self.token = body["access_token"]
                self.token_expiry_seconds = int(body["expires_in"])
            except (KeyError, TypeError, ValueError):
                response.failure("login response did not contain a valid token")
                raise StopUser("Gate login returned an invalid response.") from None
            response.success()
        self.token_created_at = time.monotonic()

    def _auth_headers(self) -> dict[str, str]:
        refresh_after = max(1, self.token_expiry_seconds - 60)
        if self.token is None or time.monotonic() - self.token_created_at >= refresh_after:
            self._login()
        return {"Authorization": f"Bearer {self.token}"}

    @task
    def park_lookup_retrieve_round_trip(self) -> None:
        headers = self._auth_headers()
        ticket = f"LT-{uuid4().hex}"
        vehicle_type = random.choice(("car", "motorbike", "bicycle"))
        plate = f"LT{uuid4().hex[:10].upper()}" if vehicle_type != "bicycle" else None
        entry: dict[str, str] = {"ticket": ticket, "type": vehicle_type}
        if plate is not None:
            entry["plate"] = plate
        params = {"type": vehicle_type}
        if plate is not None:
            params["plate"] = plate
        path = f"/api/v1/parking/entries/{ticket}"

        with self.client.post(
            "/api/v1/parking/entries",
            json=entry,
            headers=headers,
            name="POST /api/v1/parking/entries",
            catch_response=True,
        ) as response:
            if response.status_code != 204:
                response.failure(f"park returned HTTP {response.status_code}")
                return
            response.success()

        try:
            with self.client.get(
                path,
                params=params,
                headers=headers,
                name="GET /api/v1/parking/entries/{ticket}",
                catch_response=True,
            ) as response:
                if response.status_code != 200:
                    response.failure(f"lookup returned HTTP {response.status_code}")
                else:
                    try:
                        found = response.json()
                    except ValueError:
                        response.failure("lookup returned invalid JSON")
                    else:
                        if found.get("ticket") != ticket or found.get("type") != vehicle_type:
                            response.failure("lookup returned a different vehicle")
                        else:
                            response.success()
        finally:
            with self.client.delete(
                path,
                params=params,
                headers=self._auth_headers(),
                name="DELETE /api/v1/parking/entries/{ticket}",
                catch_response=True,
            ) as response:
                if response.status_code != 200:
                    response.failure(f"retrieve returned HTTP {response.status_code}")
                else:
                    try:
                        removed = response.json()
                    except ValueError:
                        response.failure("retrieve returned invalid JSON")
                    else:
                        if removed.get("ticket") != ticket:
                            response.failure("retrieve returned a different ticket")
                        else:
                            response.success()
