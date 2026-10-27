"""SQLAlchemy ORM models."""

from database_persistent.models.user import User
from database_persistent.models.vehicle import ParkedVehicle

__all__ = ["ParkedVehicle", "User"]
