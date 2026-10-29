"""Các endpoint quản lý lượt gửi xe; mọi endpoint đều yêu cầu JWT."""

from fastapi import APIRouter, Depends, Query, Security, Response

from business_layer.dependencies import get_parking_service
from business_layer.security import get_current_user
from business_layer.schemas.parking_schemas import (
    ErrorResponse,
    ParkEntryPageResponse,
    ParkEntryRequest,
    ParkEntryResponse,
    RetrieveEntryResponse,
)
from business_layer.services.parking_service import ParkingService

router = APIRouter(
    prefix="/parking",
    tags=["parking"],
    dependencies=[Security(get_current_user)],
    responses={
        400: {"model": ErrorResponse, "description": "INVALID_FORMAT / INVALID_TYPE"},
        401: {"model": ErrorResponse, "description": "UNAUTHORIZED"},
        422: {
            "model": ErrorResponse,
            "description": "PLATE_REQUIRED / PLATE_NOT_ALLOWED",
        },
    },
)

def _build_park_payload(body: ParkEntryRequest) -> dict[str, object]:
    payload: dict[str, object] = {"ticket": body.ticket, "type": body.type}
    if "plate" in body.model_fields_set:
        payload["plate"] = body.plate
    return payload


@router.post(
    "/entries",
    status_code=204,
    response_class=Response,
    responses={409: {"model": ErrorResponse, "description": "TICKET_IN_USE"}},
    summary="Ghi nhận xe vào bãi",
)
def park_vehicle(
    body: ParkEntryRequest,
    service: ParkingService = Depends(get_parking_service),
) -> Response:
    """Ghi nhận xe vào bãi; trả HTTP 204 khi thành công."""
    service.park(_build_park_payload(body))

    return Response(status_code=204)


@router.get(
    "/entries",
    response_model=ParkEntryPageResponse,
    summary="Liệt kê xe đang gửi theo trang",
)
def list_parked_vehicles(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ParkingService = Depends(get_parking_service),
) -> ParkEntryPageResponse:
    """Trả một trang xe đang gửi, sắp xếp ổn định theo mã vé."""
    records, total = service.list_parked(limit, offset)
    return ParkEntryPageResponse(
        items=[
            ParkEntryResponse(
                ticket=record.ticket,
                plate=record.plate,
                type=record.vehicle_type,
                time_in=record.time_in,
            )
            for record in records
        ],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get(
    "/entries/{ticket}",
    response_model=ParkEntryResponse,
    responses={404: {"model": ErrorResponse, "description": "VEHICLE_NOT_FOUND"}},
    summary="Tra cứu xe đang gửi mà không xóa lượt gửi",
)
def lookup_vehicle(
    ticket: str,
    type: str = Query(..., description="car | motorbike | bicycle"),
    plate: str | None = Query(default=None),
    service: ParkingService = Depends(get_parking_service),
) -> ParkEntryResponse:
    """Trả thông tin lượt gửi theo vé và không làm thay đổi dữ liệu."""
    query: dict = {"type": type}
    if plate is not None:
        query["plate"] = plate

    record = service.lookup(ticket, query)

    return ParkEntryResponse(
        ticket=record.ticket,
        plate=record.plate,
        type=record.vehicle_type,
        time_in=record.time_in,
    )


@router.delete(
    "/entries/{ticket}",
    status_code=200,
    response_model=RetrieveEntryResponse,
    responses={404: {"model": ErrorResponse, "description": "VEHICLE_NOT_FOUND"}},
    summary="Lấy xe ra và xóa lượt gửi tương ứng",
)
def retrieve_vehicle(
    ticket: str,
    type: str = Query(..., description="car | motorbike | bicycle"),
    plate: str | None = Query(default=None),
    service: ParkingService = Depends(get_parking_service),
) -> RetrieveEntryResponse:
    """Đối chiếu vé/biển số/loại xe, xóa lượt gửi và trả mã vé."""
    query: dict = {"type": type}
    if plate is not None:
        query["plate"] = plate

    record = service.retrieve(ticket, query)

    return RetrieveEntryResponse(ticket=record.ticket)
