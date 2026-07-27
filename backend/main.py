# venv\Scripts\activate
# swagger: http://127.0.0.1:8000/docs
# uvicorn main:app --reload

from fastapi import FastAPI

from api.health import router as health_router
from api.auth import router as auth_router
from api.users import router as users_router
from api.devices import router as devices_router
from api.accounts import router as accounts_router
from api.transactions import router as transactions_router
from api.deposits import router as deposits_router
from api.loans import router as loans_router
from api.cards import router as cards_router
from api.dashboard import router as dashboard_router
from api.aggregation import router as aggregation_router
from api.audit import router as audit_router

# AI, Security and Phishing routers
from api.ai import (
    fraud_router,
    wealth_router,
    profile_router,
    explainability_router,
)
from api.security import (
    risk_router,
    decision_router,
)
from api.phishing.phishing_api import router as phishing_router

from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    debug=True,
)


@app.get("/")
def root():
    return {
        "message": "Secure Wealth Twin Backend Running"
    }


# Core API routes
app.include_router(health_router, prefix="/api/v1")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(devices_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(deposits_router)
app.include_router(loans_router)
app.include_router(cards_router)
app.include_router(dashboard_router)
app.include_router(aggregation_router)

# Audit
app.include_router(audit_router, prefix="/api/v1")

# AI
app.include_router(fraud_router)
app.include_router(wealth_router)
app.include_router(profile_router)
app.include_router(explainability_router)

# Security
app.include_router(risk_router)
app.include_router(decision_router)

# Phishing
app.include_router(phishing_router)