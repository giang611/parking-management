"""Pure Python authentication service — no FastAPI or SQLAlchemy dependency."""

from datetime import datetime, timezone, timedelta

import bcrypt
import jwt

from business_layer.config import settings
from business_layer.services.exceptions import BusinessError
from business_layer.services.repository_ports import UserRepositoryPort


class AuthService:
    """Verifies credentials and issues JWT tokens."""

    def __init__(
        self,
        users: UserRepositoryPort,
    ) -> None:
        self._users = users

    def login(self, username: str, password: str) -> str:
        """Authenticate username/password and return a signed JWT.

        Raises:
            BusinessError("INVALID_CREDENTIALS"): if username unknown or password wrong.
        """
        credentials = self._users.get_by_username(username)
        if credentials is None:
            raise BusinessError("INVALID_CREDENTIALS")

        password_bytes = password.encode("utf-8")
        hash_bytes = credentials.password_hash.encode("utf-8")
        if not bcrypt.checkpw(password_bytes, hash_bytes):
            raise BusinessError("INVALID_CREDENTIALS")

        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=settings.jwt_expire_seconds)
        payload = {
            "sub": credentials.username,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
        token = jwt.encode(
            payload,
            settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )
        return token
