"""Health service handling health status aggregation and DB connectivity check."""

from datetime import datetime, timezone
from typing import Literal

from app.core.config import settings
from app.core.database import db_manager
from app.models.health import HealthResponse


class HealthService:
    """Aggregates system health, database connection status, and agent module readiness."""

    @staticmethod
    async def get_health_status() -> HealthResponse:
        """Perform system diagnostics and construct HealthResponse."""
        db_connected = await db_manager.ping_database()

        db_status: Literal["connected", "disconnected"] = (
            "connected" if db_connected else "disconnected"
        )
        overall_status: Literal["healthy", "degraded", "unhealthy"] = (
            "healthy" if db_connected else "degraded"
        )

        # List modular agent subsystem architectural readiness
        modules_status = {
            "core_api": "active",
            "auth": "active",  # Activated in Phase 7
            "llm": "active",
            "tools": "active",
            "reasoning": "active",
            "memory": "active",
            "rag": "active",
            "code_analysis": "initialized_placeholder",
        }

        return HealthResponse(
            status=overall_status,
            service=settings.PROJECT_NAME,
            environment=settings.ENVIRONMENT,
            timestamp=datetime.now(timezone.utc).isoformat(),
            database=db_status,
            modules=modules_status,
        )
