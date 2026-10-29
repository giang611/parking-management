"""Dependency xác thực Bearer JWT dùng chung cho các router cần bảo vệ."""

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
    """Giải mã JWT và trả về tên tài khoản trong claim ``sub``.

    Ném lỗi nghiệp vụ ``UNAUTHORIZED`` khi thiếu token, token sai định dạng,
    hết hạn hoặc không có claim ``sub`` hợp lệ. Khai báo đây là dependency
    ``Security`` để FastAPI xác thực trước khi kiểm tra phần thân request.
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
