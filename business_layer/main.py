"""ASGI application bootstrap."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from database_persistent.seed import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Prepare the local schema and initial account before serving requests."""

    initialize_database()
    yield


app = FastAPI(
    title="Parking Management API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
