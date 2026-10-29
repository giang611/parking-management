"""Model lượt xe hiện đang được gửi trong bãi."""

from datetime import datetime

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from database_persistent.db_config import Base, UTCDateTime


class ParkedVehicle(Base):
    __tablename__ = "parked_vehicles"
    __table_args__ = (
        CheckConstraint(
            "length(ticket) BETWEEN 1 AND 64",
            name="ck_parked_vehicles_ticket_length",
        ),
        CheckConstraint(
            "plate IS NULL OR length(plate) BETWEEN 1 AND 15",
            name="ck_parked_vehicles_plate_length",
        ),
        CheckConstraint(
            "type IN ('car', 'motorbike', 'bicycle')",
            name="ck_parked_vehicles_type",
        ),
        CheckConstraint(
            "(type = 'bicycle' AND plate IS NULL) OR "
            "(type IN ('car', 'motorbike') AND plate IS NOT NULL)",
            name="ck_parked_vehicles_plate_by_type",
        ),
    )

    ticket: Mapped[str] = mapped_column(String(64), primary_key=True)
    plate: Mapped[str | None] = mapped_column(String(15), nullable=True)
    vehicle_type: Mapped[str] = mapped_column("type", String(20), nullable=False)
    time_in: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
