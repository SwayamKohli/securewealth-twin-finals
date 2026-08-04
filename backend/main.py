# venv\Scripts\activate
# swagger: http://127.0.0.1:8000/docs
#
# LOCAL ONLY:      uvicorn main:app --reload
# MOBILE / DEMO:   uvicorn main:app --reload --host 0.0.0.0 --port 8000
#   (the phone cannot reach 127.0.0.1 — bind 0.0.0.0 and point
#    frontend/src/api/config.ts at your Mac's LAN IP)

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.admin import router as admin_router

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

# audit routers
from api.audit import router as audit_router
from audit.audit_scheduler import AuditScheduler
from core.dependencies import build_tamper_monitor, get_tamper_monitor

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
    challenge_router,
    activity_router,
)
from api.phishing.phishing_api import router as phishing_router
from core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    scheduler = AuditScheduler(
        build_tamper_monitor()
    )

    await scheduler.start()

    # Warm the local explanation model in the background.
    #
    # llama3:8b takes 15-40s to load into memory on first use. Without this,
    # the FIRST customer to see an explanation pays that cost — and because the
    # engines fall back silently on timeout, they would get generic text with
    # no indication anything was wrong. Warming at startup means the model is
    # already resident by the time anyone taps Invest.
    #
    # Non-blocking and failure-tolerant: if Ollama is not installed or not
    # running, the app starts exactly as before and every engine uses its
    # deterministic fallback.
    import threading

    def _warm():
        from ai.engines import llm_source

        if llm_source.warm_up():
            logger.info("Local explanation model warmed and resident.")
        else:
            logger.info(
                "Ollama not reachable — explanations will use deterministic "
                "fallbacks. Start it with `ollama serve` for generated text."
            )

    threading.Thread(target=_warm, name="llm-warmup", daemon=True).start()

    yield

    await scheduler.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    debug=True,
    lifespan=lifespan,
)


# CORS — required by the standalone web Admin Dashboard (task 7).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(challenge_router)
app.include_router(activity_router)

# Phishing
app.include_router(phishing_router)

# Admin Dashboard (standalone web app)
app.include_router(admin_router)