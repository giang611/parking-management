"""Parking entry endpoints — all protected by JWT authentication."""

from fastapi import APIRouter, Depends, HTTPException, Query, Security, Response

from business_layer.dependencies import get_parking_service
from business_layer.middleware.auth_middleware import get_current_user
from business_layer.schemas.parking_schemas import ParkEntryRequest, ParkEntryResponse
from business_layer.services.exceptions import BusinessError
from business_layer.services.parking_service import ParkingService

router = APIRouter(prefix="/parking", tags=["parking"])

# Map domain error codes to HTTP status codes
_ERROR_STATUS: dict[str, int] = {
    "TICKET_IN_USE": 409,
    "VEHICLE_NOT_FOUND": 404,
    "INVALID_FORMAT": 422,
    "INVALID_TYPE": 422,
    "PLATE_REQUIRED": 422,
    "PLATE_NOT_ALLOWED": 422,
}


def _raise_business(exc: BusinessError) -> None:
    status = _ERROR_STATUS.get(exc.code, 422)
    raise HTTPException(status_code=status, detail={"error": exc.code})


@router.post(
    "/entries",
    status_code=204,
    response_class=Response,
    dependencies=[Security(get_current_user)],
    summary="Record a vehicle entering the parking lot",
)
def park_vehicle(
    body: ParkEntryRequest,
    service: ParkingService = Depends(get_parking_service),
) -> Response:
    """Park a vehicle. Returns 204 No Content on success."""
    payload: dict = {"ticket": body.ticket, "type": body.type}
    if body.plate is not None:
        payload["plate"] = body.plate

    try:
        service.park(payload)
    except BusinessError as exc:
        _raise_business(exc)

    return Response(status_code=204)


@router.get(
    "/entries/{ticket}",
    response_model=ParkEntryResponse,
    dependencies=[Security(get_current_user)],
    summary="Look up a parked vehicle without removing it",
)
def lookup_vehicle(
    ticket: str,
    type: str = Query(..., description="car | motorbike | bicycle"),
    plate: str | None = Query(default=None),
    service: ParkingService = Depends(get_parking_service),
) -> ParkEntryResponse:
    """Return the parking record for the given ticket without modifying state."""
    query: dict = {"type": type}
    if plate is not None:
        query["plate"] = plate

    try:
        record = service.lookup(ticket, query)
    except BusinessError as exc:
        _raise_business(exc)

    return ParkEntryResponse(
        ticket=record.ticket,
        plate=record.plate,
        type=record.vehicle_type,
        time_in=record.time_in,
    )


@router.delete(
    "/entries/{ticket}",
    status_code=204,
    response_class=Response,
    dependencies=[Security(get_current_user)],
    summary="Retrieve a vehicle and remove its parking record",
)
def retrieve_vehicle(
    ticket: str,
    type: str = Query(..., description="car | motorbike | bicycle"),
    plate: str | None = Query(default=None),
    service: ParkingService = Depends(get_parking_service),
) -> Response:
    """Verify the ticket/plate/type triple then delete the parking record."""
    query: dict = {"type": type}
    if plate is not None:
        query["plate"] = plate

    try:
        service.retrieve(ticket, query)
    except BusinessError as exc:
        _raise_business(exc)

    return Response(status_code=204)
