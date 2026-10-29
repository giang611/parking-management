"""Repository SQLAlchemy triển khai giao diện truy cập lượt gửi xe."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from business_layer.services.repository_ports import (
    ParkedVehicleRecord,
    VehicleRepositoryPort,
)
from database_persistent.models import ParkedVehicle


class SqlAlchemyVehicleRepository(VehicleRepositoryPort):
    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_record(vehicle: ParkedVehicle) -> ParkedVehicleRecord:
        return ParkedVehicleRecord(
            ticket=vehicle.ticket,
            plate=vehicle.plate,
            vehicle_type=vehicle.vehicle_type,
            time_in=vehicle.time_in,
        )

    def get_by_ticket(self, ticket: str) -> ParkedVehicleRecord | None:
        vehicle = self._session.get(ParkedVehicle, ticket)
        return self._to_record(vehicle) if vehicle is not None else None

    def list_page(
        self, limit: int, offset: int
    ) -> tuple[list[ParkedVehicleRecord], int]:
        total = self._session.scalar(select(func.count()).select_from(ParkedVehicle)) or 0
        statement = (
            select(ParkedVehicle)
            .order_by(ParkedVehicle.ticket.asc())
            .limit(limit)
            .offset(offset)
        )
        vehicles = self._session.scalars(statement).all()
        return [self._to_record(vehicle) for vehicle in vehicles], total

    def find_match(
        self, ticket: str, plate: str | None, vehicle_type: str
    ) -> ParkedVehicleRecord | None:
        statement = select(ParkedVehicle).where(
            ParkedVehicle.ticket == ticket,
            ParkedVehicle.plate == plate,
            ParkedVehicle.vehicle_type == vehicle_type,
        )
        vehicle = self._session.scalar(statement)
        return self._to_record(vehicle) if vehicle is not None else None

    def add(self, vehicle: ParkedVehicleRecord) -> bool:
        model = ParkedVehicle(
            ticket=vehicle.ticket,
            plate=vehicle.plate,
            vehicle_type=vehicle.vehicle_type,
            time_in=vehicle.time_in,
        )
        try:
            with self._session.begin_nested():
                self._session.add(model)
                self._session.flush()
        except IntegrityError:
            if self._session.get(ParkedVehicle, vehicle.ticket) is not None:
                return False
            raise
        return True

    def delete_by_ticket(self, ticket: str) -> bool:
        vehicle = self._session.get(ParkedVehicle, ticket)
        if vehicle is None:
            return False
        self._session.delete(vehicle)
        self._session.flush()
        return True
