from .fraud_api import router as fraud_router
from .wealth_api import router as wealth_router
from .profile_api import router as profile_router
from .explainability_api import router as explainability_router

__all__ = [
    "fraud_router",
    "wealth_router", 
    "profile_router",
    "explainability_router",
]