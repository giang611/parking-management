"""Khai báo engine SQLAlchemy, lớp nền ORM và bộ tạo phiên làm việc."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator

from business_layer.config import settings


class Base(DeclarativeBase):
    """Lớp nền chung cho các model lưu trữ."""


class UTCDateTime(TypeDecorator[datetime]):
    """Lưu thời điểm theo UTC và luôn trả về giá trị có múi giờ UTC."""

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
    """Tạo engine cho DB đã cấu hình; SQLite cho phép dùng qua nhiều luồng."""

    url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite:") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_schema() -> None:
    """Tạo các bảng còn thiếu cho lần triển khai đầu."""

    # Nạp model để đăng ký bảng trước khi gọi create_all.
    from database_persistent.models import ParkedVehicle, User  # noqa: F401  # Đăng ký model vào metadata SQLAlchemy.

    Base.metadata.create_all(bind=engine)
