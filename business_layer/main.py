"""ASGI application bootstrap — wires routers and exception handlers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from business_layer.services.exceptions import BusinessError
from database_persistent.seed import initialize_database

# Error-code → HTTP status mapping
_BUSINESS_STATUS: dict[str, int] = {
    "TICKET_IN_USE": 409,
    "VEHICLE_NOT_FOUND": 404,
    "INVALID_CREDENTIALS": 401,
    "UNAUTHORIZED": 401,
    "INVALID_FORMAT": 422,
    "INVALID_TYPE": 422,
    "PLATE_REQUIRED": 422,
    "PLATE_NOT_ALLOWED": 422,
}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create tables and seed the initial admin account before serving requests."""
    initialize_database()
    yield


app = FastAPI(
    title="Parking Management API",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(BusinessError)
async def business_error_handler(_: Request, exc: BusinessError) -> JSONResponse:
    status = _BUSINESS_STATUS.get(exc.code, 422)
    return JSONResponse(status_code=status, content={"error": exc.code})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": "INVALID_FORMAT"})


# ── Routers ───────────────────────────────────────────────────────────────────

from business_layer.api import auth_router, health_router, parking_router  # noqa: E402

app.include_router(health_router.router)
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(parking_router.router, prefix="/api/v1")
