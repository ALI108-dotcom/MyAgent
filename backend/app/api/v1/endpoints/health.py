"""Health check API endpoint."""

from fastapi import APIRouter, status

from app.models.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get system health and diagnostics",
    description=(
        "Returns overall API status, MongoDB connection status, "
        "server timestamp, and module readiness."
    ),
)
async def check_health() -> HealthResponse:
    """Retrieve current system health status."""
    return await HealthService.get_health_status()
