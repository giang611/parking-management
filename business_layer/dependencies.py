"""Cung cấp dependency FastAPI để nối phiên DB với repository và service."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from database_persistent.db_config import SessionLocal
from database_persistent.repositories.user_repository import SqlAlchemyUserRepository
from database_persistent.repositories.vehicle_repository import SqlAlchemyVehicleRepository
from business_layer.services.repository_ports import UserRepositoryPort, VehicleRepositoryPort
from business_layer.services.auth_service import AuthService
from business_layer.services.parking_service import ParkingService


def get_db() -> Generator[Session, None, None]:
    """Cấp phiên SQLAlchemy theo transaction; commit khi thành công, rollback khi lỗi."""
    with SessionLocal.begin() as session:
        yield session


def get_vehicle_repo(db: Session = Depends(get_db)) -> VehicleRepositoryPort:
    return SqlAlchemyVehicleRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepositoryPort:
    return SqlAlchemyUserRepository(db)


def get_parking_service(
    repo: VehicleRepositoryPort = Depends(get_vehicle_repo),
) -> ParkingService:
    return ParkingService(repo)


def get_auth_service(
    repo: UserRepositoryPort = Depends(get_user_repo),
) -> AuthService:
    return AuthService(repo)
