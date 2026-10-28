"""Persistence contracts and records used by framework-independent services."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class ParkedVehicleRecord:
    ticket: str
    plate: str | None
    vehicle_type: str
    time_in: datetime

    def __post_init__(self) -> None:
        if self.time_in.tzinfo is None or self.time_in.utcoffset() is None:
            raise ValueError("time_in must be timezone-aware")
        object.__setattr__(self, "time_in", self.time_in.astimezone(timezone.utc))


@dataclass(frozen=True)
class UserCredentials:
    username: str
    password_hash: str


class VehicleRepositoryPort(Protocol):
    """Operations required by parking services, without a database dependency."""

    def get_by_ticket(self, ticket: str) -> ParkedVehicleRecord | None: ...

    def list_page(
        self, limit: int, offset: int
    ) -> tuple[list[ParkedVehicleRecord], int]:
        """Return one stable page and the total number of parked vehicles."""
        ...

    def find_match(
        self, ticket: str, plate: str | None, vehicle_type: str
    ) -> ParkedVehicleRecord | None: ...

    def add(self, vehicle: ParkedVehicleRecord) -> bool:
        """Return False only when the ticket already exists."""
        ...

    def delete_by_ticket(self, ticket: str) -> bool: ...


class UserRepositoryPort(Protocol):
    """Credential lookup contract required by authentication services."""

    def get_by_username(self, username: str) -> UserCredentials | None: ...
