"""Endpoint kiểm tra trạng thái hoạt động của dịch vụ."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Kiểm tra dịch vụ đang hoạt động")
def health() -> dict[str, str]:
    """Trả HTTP 200 khi dịch vụ đang chạy."""
    return {"status": "ok"}
