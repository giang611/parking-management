"""FastAPI security dependency — verifies Bearer JWT before any handler runs."""

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from business_layer.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=401,
    detail={"error": "UNAUTHORIZED"},
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> str:
    """Decode and validate a Bearer JWT.

    Returns the ``sub`` claim (username) when valid.
    Raises HTTP 401 for missing, malformed, or expired tokens.
    This must be declared as a ``Security()`` dependency so FastAPI runs it
    *before* validating the request body, ensuring auth errors surface first.
    """
    if credentials is None:
        raise _UNAUTHORIZED

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
        )
    except ExpiredSignatureError:
        raise _UNAUTHORIZED
    except InvalidTokenError:
        raise _UNAUTHORIZED

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise _UNAUTHORIZED

    return sub
