"""Các schema Pydantic dùng trong request và response của API."""

from business_layer.schemas.auth_schemas import LoginRequest, TokenResponse
from business_layer.schemas.parking_schemas import ErrorResponse, ParkEntryRequest, ParkEntryResponse

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "ParkEntryRequest",
    "ParkEntryResponse",
    "ErrorResponse",
]
