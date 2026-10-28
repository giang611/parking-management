"""Authentication endpoints."""

from fastapi import APIRouter, Depends

from business_layer.config import settings
from business_layer.dependencies import get_auth_service
from business_layer.schemas.auth_schemas import LoginRequest, TokenResponse
from business_layer.schemas.parking_schemas import ErrorResponse
from business_layer.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse, "description": "INVALID_CREDENTIALS"}},
)
def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    """Issue a JWT access token for valid credentials.

    Returns 401 with ``{"error": "INVALID_CREDENTIALS"}`` when username or
    password is wrong.
    """
    token = service.login(body.username, body.password)
    return TokenResponse(access_token=token, expires_in=settings.jwt_expire_seconds)
