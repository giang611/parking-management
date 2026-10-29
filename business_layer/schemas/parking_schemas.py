"""Schema Pydantic cho request và response quản lý lượt gửi xe."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ParkEntryRequest(BaseModel):
    """Phần thân request POST /api/v1/parking/entries."""

    model_config = ConfigDict(extra="forbid")

    ticket: str = Field(..., min_length=1, max_length=64)
    plate: str | None = Field(default=None, max_length=15)
    type: str = Field(..., description="car | motorbike | bicycle")


class ParkEntryResponse(BaseModel):
    """Response của GET /api/v1/parking/entries/{ticket}."""

    ticket: str
    plate: str | None
    type: str
    time_in: datetime


class RetrieveEntryResponse(BaseModel):
    """Response sau khi lấy xe ra khỏi bãi."""

    ticket: str


class ParkEntryPageResponse(BaseModel):
    """Danh sách xe đang gửi được chia trang."""

    items: list[ParkEntryResponse]
    limit: int
    offset: int
    total: int


class ErrorResponse(BaseModel):
    """Cấu trúc response lỗi thống nhất."""

    error: str
