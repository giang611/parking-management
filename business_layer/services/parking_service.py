"""Pure Python parking workflows backed by a repository port."""

from datetime import datetime, timezone
from typing import Callable, Mapping

from business_layer.services.exceptions import BusinessError
from business_layer.services.repository_ports import (
    ParkedVehicleRecord,
    VehicleRepositoryPort,
)


class ParkingService:
    VEHICLE_TYPES = {"car", "motorbike", "bicycle"}

    def __init__(
        self,
        vehicles: VehicleRepositoryPort,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._vehicles = vehicles
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def park(self, payload: Mapping[str, object]) -> ParkedVehicleRecord:
        if not isinstance(payload, Mapping):
            raise BusinessError("INVALID_FORMAT")
        ticket = self._ticket(payload.get("ticket"))
        plate, vehicle_type = self._details(payload, {"ticket", "plate", "type"})
        record = ParkedVehicleRecord(ticket, plate, vehicle_type, self._clock())
        if not self._vehicles.add(record):
            raise BusinessError("TICKET_IN_USE")
        return record

    def lookup(
        self, ticket: str, query: Mapping[str, object]
    ) -> ParkedVehicleRecord:
        normalized_ticket = self._ticket(ticket)
        plate, vehicle_type = self._details(query, {"plate", "type"})
        record = self._vehicles.find_match(normalized_ticket, plate, vehicle_type)
        if record is None:
            raise BusinessError("VEHICLE_NOT_FOUND")
        return record

    def retrieve(
        self, ticket: str, query: Mapping[str, object]
    ) -> ParkedVehicleRecord:
        record = self.lookup(ticket, query)
        if not self._vehicles.delete_by_ticket(record.ticket):
            raise BusinessError("VEHICLE_NOT_FOUND")
        return record

    def list_parked(
        self, limit: int, offset: int
    ) -> tuple[list[ParkedVehicleRecord], int]:
        return self._vehicles.list_page(limit, offset)

    @staticmethod
    def _ticket(value: object) -> str:
        if not isinstance(value, str):
            raise BusinessError("INVALID_FORMAT")
        ticket = value.strip()
        if not ticket or len(ticket) > 64:
            raise BusinessError("INVALID_FORMAT")
        return ticket

    @classmethod
    def _details(
        cls, payload: Mapping[str, object], allowed: set[str]
    ) -> tuple[str | None, str]:
        if not isinstance(payload, Mapping) or set(payload) - allowed:
            raise BusinessError("INVALID_FORMAT")
        vehicle_type = payload.get("type")
        if not isinstance(vehicle_type, str):
            raise BusinessError("INVALID_FORMAT")
        if vehicle_type not in cls.VEHICLE_TYPES:
            raise BusinessError("INVALID_TYPE")

        if vehicle_type == "bicycle":
            if "plate" in payload:
                raise BusinessError("PLATE_NOT_ALLOWED")
            return None, vehicle_type

        raw_plate = payload.get("plate")
        if not isinstance(raw_plate, str):
            raise BusinessError("PLATE_REQUIRED")
        plate = raw_plate.strip().upper()
        if not plate or len(plate) > 15:
            raise BusinessError("INVALID_FORMAT")
        return plate, vehicle_type
