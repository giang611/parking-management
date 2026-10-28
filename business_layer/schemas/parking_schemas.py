"""Pydantic schemas for parking entry endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ParkEntryRequest(BaseModel):
    """Body for POST /api/v1/parking/entries."""

    ticket: str = Field(..., min_length=1, max_length=64)
    plate: str | None = Field(default=None, max_length=15)
    type: str = Field(..., description="car | motorbike | bicycle")


class ParkEntryResponse(BaseModel):
    """Response for GET /api/v1/parking/entries/{ticket}."""

    ticket: str
    plate: str | None
    type: str
    time_in: datetime


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
