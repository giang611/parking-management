"""SQLAlchemy engine, base class, and session factory."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator

from business_layer.config import settings


class Base(DeclarativeBase):
    """Base class for persistence models."""


class UTCDateTime(TypeDecorator[datetime]):
    """Store UTC timestamps and return timezone-aware UTC values on every dialect."""

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("time_in must be timezone-aware")
        utc_value = value.astimezone(timezone.utc)
        if dialect.name == "sqlite":
            return utc_value.replace(tzinfo=None)
        return utc_value

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create an engine for the configured database; SQLite supports worker threads."""

    url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite:") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_schema() -> None:
    """Create missing tables for the baseline deployment."""

    # Import models here so their tables are registered before create_all.
    from database_persistent.models import ParkedVehicle, User  # noqa: F401

    Base.metadata.create_all(bind=engine)
