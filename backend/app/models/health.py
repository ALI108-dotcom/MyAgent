"""Pydantic schemas for API Health Status responses."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check endpoint response model."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall API health status"
    )
    service: str = Field(..., description="Project / Service Name")
    environment: str = Field(..., description="Running environment")
    timestamp: str = Field(..., description="ISO 8601 server timestamp")
    database: Literal["connected", "disconnected"] = Field(
        ..., description="MongoDB connection state"
    )
    modules: dict[str, str] = Field(
        ..., description="Status of modular agent architecture components"
    )
