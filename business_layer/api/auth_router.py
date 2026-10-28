"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from business_layer.dependencies import get_auth_service
from business_layer.schemas.auth_schemas import LoginRequest, TokenResponse
from business_layer.services.auth_service import AuthService
from business_layer.services.exceptions import BusinessError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    """Issue a JWT access token for valid credentials.

    Returns 401 with ``{"error": "INVALID_CREDENTIALS"}`` when username or
    password is wrong.
    """
    try:
        token = service.login(body.username, body.password)
    except BusinessError as exc:
        raise HTTPException(status_code=401, detail={"error": exc.code})
    return TokenResponse(access_token=token)
