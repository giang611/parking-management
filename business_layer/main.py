"""ASGI application bootstrap — wires routers and exception handlers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from business_layer.api.errors import business_error_response, validation_error_response
from business_layer.services.exceptions import BusinessError
from database_persistent.seed import initialize_database

HTTP_ERRORS = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}

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
    return business_error_response(exc)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return validation_error_response(exc.errors())


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": HTTP_ERRORS.get(exc.status_code, "HTTP_ERROR")},
        headers=exc.headers,
    )


# ── Routers ───────────────────────────────────────────────────────────────────

from business_layer.api import auth_router, health_router, parking_router  # noqa: E402

app.include_router(health_router.router)
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(parking_router.router, prefix="/api/v1")
