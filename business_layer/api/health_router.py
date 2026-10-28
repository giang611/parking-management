"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service liveness check")
def health() -> dict[str, str]:
    """Return 200 when the service is running."""
    return {"status": "ok"}
