from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.config import settings
from schemas.health_schema import (
    HealthResponse,
    ServiceHealthResponse,
)


class HealthService:
    """
    Service responsible for system and application health checks.
    """

    @staticmethod
    def get_system_health(
        db: Session,
    ) -> HealthResponse:
        """
        Perform an overall system health check.

        Checks:
        - Database connectivity
        - Application metadata

        Returns:
            HealthResponse
        """

        database_status = "connected"
        overall_status = "healthy"

        try:
            db.execute(
                text("SELECT 1")
            )

        except SQLAlchemyError:

            database_status = "disconnected"
            overall_status = "unhealthy"

        return HealthResponse(
            status=overall_status,
            application=settings.PROJECT_NAME,
            version=settings.PROJECT_VERSION,
            environment=settings.ENVIRONMENT,
            database=database_status,
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def get_service_health(
        db: Session,
    ) -> ServiceHealthResponse:
        """
        Perform health checks for internal application services.

        UNDER DEVELOPMENT: This method currently checks only the database connectivity.
        Current checks:
        - Database

        Static services (same FastAPI process):
        - Authentication
        - Dashboard
        - Aggregation
        - Notifications
        - Audit

        Returns:
            ServiceHealthResponse
        """

        services = {
            "database": "up",
            "authentication": "up",
            "dashboard": "up",
            "aggregation": "up",
            "notifications": "up",
            "audit": "up",
        }

        overall_status = "healthy"

        try:
            db.execute(
                text("SELECT 1")
            )

        except SQLAlchemyError:

            services["database"] = "down"
            overall_status = "degraded"

        return ServiceHealthResponse(
            status=overall_status,
            services=services,
            timestamp=datetime.now(timezone.utc),
        )