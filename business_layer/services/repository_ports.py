"""Hợp đồng lưu trữ và bản ghi dùng bởi service không phụ thuộc framework."""

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
    """Các thao tác service gửi xe cần, không phụ thuộc cơ sở dữ liệu cụ thể."""

    def get_by_ticket(self, ticket: str) -> ParkedVehicleRecord | None: ...

    def list_page(
        self, limit: int, offset: int
    ) -> tuple[list[ParkedVehicleRecord], int]:
        """Trả một trang kết quả ổn định cùng tổng số xe đang gửi."""
        ...

    def find_match(
        self, ticket: str, plate: str | None, vehicle_type: str
    ) -> ParkedVehicleRecord | None: ...

    def add(self, vehicle: ParkedVehicleRecord) -> bool:
        """Chỉ trả False khi mã vé đã tồn tại."""
        ...

    def delete_by_ticket(self, ticket: str) -> bool: ...


class UserRepositoryPort(Protocol):
    """Hợp đồng tra cứu thông tin đăng nhập mà service xác thực cần."""

    def get_by_username(self, username: str) -> UserCredentials | None: ...
