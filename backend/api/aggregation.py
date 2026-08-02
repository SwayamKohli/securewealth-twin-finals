from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import (get_current_user,get_db)
from models.user import User
from schemas.aggregation_schema import (
    AggregatedAccountResponse,
    ConsentResponse,
    AggregationStatusResponse,
    CashflowResponse,
    LinkAccountRequest,
    NetWorthResponse,
    SyncRequest,
    SyncResponse,
)
from services.aggregation_service import AggregationService

router = APIRouter(
    prefix="/api/v1/aggregation",
    tags=["Aggregation"],
)


# ── Task 2.1: Consent-based Account Aggregation ──────────────────────────────
# Flow: User -> Consent -> Account Aggregator -> Linked Banks -> Dashboard.
# Aggregated data endpoints require explicit, revocable consent.

def require_aa_consent(
    current_user: User = Depends(get_current_user),
) -> User:
    if not getattr(current_user, "aa_consent", False):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Account Aggregation consent required. "
                "Grant consent via POST /api/v1/aggregation/consent to view "
                "your unified wealth dashboard."
            ),
        )
    return current_user


@router.post(
    "/consent",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
)
def grant_consent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record the customer's explicit consent for account aggregation."""
    from datetime import datetime, timezone

    current_user.aa_consent = True
    current_user.aa_consent_at = datetime.now(timezone.utc)
    db.commit()
    return ConsentResponse(
        aa_consent=True,
        aa_consent_at=current_user.aa_consent_at,
        message="Consent granted. Your accounts can now be aggregated securely.",
    )


@router.delete(
    "/consent",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
)
def revoke_consent(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke aggregation consent. Aggregated views stop immediately."""
    current_user.aa_consent = False
    current_user.aa_consent_at = None
    db.commit()
    return ConsentResponse(
        aa_consent=False,
        aa_consent_at=None,
        message="Consent revoked. Aggregated data is no longer accessible.",
    )


@router.get(
    "/consent",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
)
def get_consent(
    current_user: User = Depends(get_current_user),
):
    granted = bool(getattr(current_user, "aa_consent", False))
    return ConsentResponse(
        aa_consent=granted,
        aa_consent_at=current_user.aa_consent_at,
        message="Consent granted." if granted else "Consent not granted.",
    )


@router.get(
    "/accounts",
    response_model=list[AggregatedAccountResponse],
    status_code=status.HTTP_200_OK,
)
def get_accounts(
    current_user: User = Depends(require_aa_consent),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_accounts(
        user_id=current_user.user_id,
    )


@router.get(
    "/accounts/{account_id}",
    response_model=AggregatedAccountResponse,
    status_code=status.HTTP_200_OK,
)
def get_account(
    account_id: UUID,
    current_user: User = Depends(require_aa_consent),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_account(
        account_id=account_id,
        user_id=current_user.user_id,
    )


@router.post(
    "/accounts/link",
    status_code=status.HTTP_201_CREATED,
)
def link_account(
    request: LinkAccountRequest,
    current_user: User = Depends(require_aa_consent),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.link_account(
        user_id=current_user.user_id,
        request=request,
    )


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    service.remove_account(
        account_id=account_id,
        user_id=current_user.user_id,
    )


@router.post(
    "/sync",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
)
def sync_aggregation(
    request: SyncRequest,
    current_user: User = Depends(require_aa_consent),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.sync(
        user_id=current_user.user_id,
    )


@router.get(
    "/status",
    response_model=AggregationStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_status(
        user_id=current_user.user_id,
    )


@router.get(
    "/net-worth",
    response_model=NetWorthResponse,
    status_code=status.HTTP_200_OK,
)
def get_net_worth(
    current_user: User = Depends(require_aa_consent),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_net_worth(
        user_id=current_user.user_id,
    )


@router.get(
    "/cashflow",
    response_model=CashflowResponse,
    status_code=status.HTTP_200_OK,
)
def get_cashflow(
    current_user: User = Depends(require_aa_consent),
    db: Session = Depends(get_db),
):
    service = AggregationService(db)

    return service.get_cashflow(
        user_id=current_user.user_id,
    )