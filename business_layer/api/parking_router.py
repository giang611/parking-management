"""Parking entry endpoints — all protected by JWT authentication."""

from fastapi import APIRouter, Depends, Query, Security, Response

from business_layer.dependencies import get_parking_service
from business_layer.middleware.auth_middleware import get_current_user
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
    summary="Record a vehicle entering the parking lot",
)
def park_vehicle(
    body: ParkEntryRequest,
    service: ParkingService = Depends(get_parking_service),
) -> Response:
    """Park a vehicle. Returns 204 No Content on success."""
    service.park(_build_park_payload(body))

    return Response(status_code=204)


@router.get(
    "/entries",
    response_model=ParkEntryPageResponse,
    summary="List parked vehicles with pagination",
)
def list_parked_vehicles(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ParkingService = Depends(get_parking_service),
) -> ParkEntryPageResponse:
    """Return a stable, ticket-sorted page of currently parked vehicles."""
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
    summary="Retrieve a vehicle and remove its parking record",
)
def retrieve_vehicle(
    ticket: str,
    type: str = Query(..., description="car | motorbike | bicycle"),
    plate: str | None = Query(default=None),
    service: ParkingService = Depends(get_parking_service),
) -> RetrieveEntryResponse:
    """Verify the ticket/plate/type triple, delete it and return its ticket."""
    query: dict = {"type": type}
    if plate is not None:
        query["plate"] = plate

    record = service.retrieve(ticket, query)

    return RetrieveEntryResponse(ticket=record.ticket)
