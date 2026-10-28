"""FastAPI security dependency — verifies Bearer JWT before any handler runs."""

from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from business_layer.config import settings
from business_layer.services.exceptions import BusinessError

_bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> str:
    """Decode and validate a Bearer JWT.

    Returns the ``sub`` claim (username) when valid.
    Raises a domain UNAUTHORIZED error for missing, malformed, or expired tokens.
    This must be declared as a ``Security()`` dependency so FastAPI runs it
    *before* validating the request body, ensuring auth errors surface first.
    """
    if credentials is None:
        raise BusinessError("UNAUTHORIZED")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
        )
    except ExpiredSignatureError:
        raise BusinessError("UNAUTHORIZED")
    except InvalidTokenError:
        raise BusinessError("UNAUTHORIZED")

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise BusinessError("UNAUTHORIZED")

    return sub
