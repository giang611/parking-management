from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pytest

from business_layer.config import settings
from business_layer.middleware.auth_middleware import get_current_user
from business_layer.services.auth_service import AuthService
from business_layer.services.exceptions import BusinessError
from business_layer.services.repository_ports import UserCredentials
from fastapi.security import HTTPAuthorizationCredentials


class MemoryUsers:
    def __init__(self, password_hash: str | None):
        self.password_hash = password_hash

    def get_by_username(self, username: str):
        if username != "operator" or self.password_hash is None:
            return None
        return UserCredentials(username="operator", password_hash=self.password_hash)


def test_login_issues_hs256_token_with_subject_and_expiration(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", type(settings.jwt_secret)("integration-test-signing-key-32-bytes"))
    password_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode("ascii")

    token = AuthService(MemoryUsers(password_hash)).login("operator", "correct-password")
    claims = jwt.decode(token, "integration-test-signing-key-32-bytes", algorithms=["HS256"])

    assert claims["sub"] == "operator"
    assert claims["exp"] > datetime.now(timezone.utc).timestamp()


@pytest.mark.parametrize("username,password", [
    ("missing", "correct-password"),
    ("operator", "wrong-password"),
])
def test_login_rejects_unknown_user_and_wrong_password(username, password):
    password_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode("ascii")

    with pytest.raises(BusinessError) as error:
        AuthService(MemoryUsers(password_hash)).login(username, password)

    assert error.value.code == "INVALID_CREDENTIALS"


def test_token_verification_returns_subject(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", type(settings.jwt_secret)("integration-test-signing-key-32-bytes"))
    token = jwt.encode(
        {"sub": "operator", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "integration-test-signing-key-32-bytes",
        algorithm="HS256",
    )

    user = get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert user == "operator"


@pytest.mark.parametrize("token", [
    "not-a-token",
    jwt.encode(
        {"sub": "operator", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        "integration-test-signing-key-32-bytes",
        algorithm="HS256",
    ),
])
def test_token_verification_rejects_malformed_and_expired_tokens(token, monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", type(settings.jwt_secret)("integration-test-signing-key-32-bytes"))

    with pytest.raises(BusinessError) as error:
        get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert error.value.code == "UNAUTHORIZED"


def test_missing_token_is_unauthorized():
    with pytest.raises(BusinessError) as error:
        get_current_user(None)
    assert error.value.code == "UNAUTHORIZED"


def test_login_api_returns_flat_error_for_bad_credentials(api_env):
    response = api_env.post(
        "/api/v1/auth/login",
        json={"username": "operator", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "INVALID_CREDENTIALS"}


def test_login_api_returns_bearer_and_expiration(api_env):
    response = api_env.post(
        "/api/v1/auth/login",
        json={"username": "operator", "password": "correct-password"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "Bearer"
    assert response.json()["expires_in"] == settings.jwt_expire_seconds
