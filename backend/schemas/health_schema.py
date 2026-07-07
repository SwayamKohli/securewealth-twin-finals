from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """
    Response schema for overall system health.
    """

    model_config = ConfigDict(from_attributes=True)

    status: Literal["healthy", "unhealthy"] = Field(
        ...,
        description="Overall health status of the application."
    )

    application: str = Field(
        ...,
        description="Application name."
    )

    version: str = Field(
        ...,
        description="Current application version."
    )

    environment: str = Field(
        ...,
        description="Current runtime environment."
    )

    database: Literal["connected", "disconnected"] = Field(
        ...,
        description="Database connectivity status."
    )

    timestamp: datetime = Field(
        ...,
        description="Time when the health check was performed."
    )


class ServiceHealthResponse(BaseModel):
    """
    Response schema for individual service health.
    """

    model_config = ConfigDict(from_attributes=True)

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="Overall status considering all services."
    )

    services: Dict[str, Literal["up", "down"]] = Field(
        ...,
        description="Health status of each internal service."
    )

    timestamp: datetime = Field(
        ...,
        description="Time when the service health check was performed."
    )