from .accounts import router as accounts_router
from .aggregation import router as aggregation_router
from .auth import router as auth_router
from .cards import router as cards_router
from .dashboard import router as dashboard_router
from .deposits import router as deposits_router
from .devices import router as devices_router
from .health import router as health_router
from .loans import router as loans_router
from .transactions import router as transactions_router
from .users import router as users_router

# AI engines
from .ai import fraud_router, wealth_router, profile_router, explainability_router

# Security engines
from .security import risk_router, decision_router

# Phishing detection
from .phishing import phishing_router

__all__ = [
    # Original routers
    "accounts_router",
    "aggregation_router",
    "auth_router", 
    "cards_router",
    "dashboard_router",
    "deposits_router",
    "devices_router",
    "health_router",
    "loans_router",
    "transactions_router",
    "users_router",
    
    # AI routers
    "fraud_router",
    "wealth_router",
    "profile_router",
    "explainability_router",
    
    # Security routers
    "risk_router", 
    "decision_router",
    
    # Phishing router
    "phishing_router",
]