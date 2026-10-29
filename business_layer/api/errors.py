"""Chuyển lỗi nghiệp vụ và lỗi kiểm tra request thành response API ổn định."""

from collections.abc import Mapping, Sequence

from fastapi.responses import JSONResponse

from business_layer.services.exceptions import BusinessError


BUSINESS_STATUS: dict[str, int] = {
    "TICKET_IN_USE": 409,
    "VEHICLE_NOT_FOUND": 404,
    "INVALID_CREDENTIALS": 401,
    "UNAUTHORIZED": 401,
    "INVALID_FORMAT": 400,
    "INVALID_TYPE": 400,
    "PLATE_REQUIRED": 422,
    "PLATE_NOT_ALLOWED": 422,
}


def business_error_response(error: BusinessError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if error.code == "UNAUTHORIZED" else None
    return JSONResponse(
        status_code=BUSINESS_STATUS.get(error.code, 422),
        content={"error": error.code},
        headers=headers,
    )


def validation_error_response(errors: Sequence[Mapping[str, object]]) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "INVALID_FORMAT"})
