from .risk_api import router as risk_router
from .decision_api import router as decision_router
from .challenge_api import router as challenge_router
from .activity_api import router as activity_router

__all__ = [
    "risk_router",
    "decision_router",
    "challenge_router",
    "activity_router",
]
