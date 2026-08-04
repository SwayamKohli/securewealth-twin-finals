"""
api/security/challenge_api.py — Challenge verification endpoints (task 4.3)

    POST /api/v1/security/challenge/{transaction_id}/start
        -> current step, prompt, total steps (issues demo OTP when needed)

    POST /api/v1/security/challenge/{transaction_id}/verify
        body: { "answer": "...", "acknowledged": true|false }
        -> verified?, next step or final transaction status
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, get_db
from models.user import User
from services.security.challenge_service import ChallengeService

router = APIRouter(
    prefix="/api/v1/security/challenge",
    tags=["Challenge Verification"],
)


class ChallengeVerifyRequest(BaseModel):
    answer: str | None = None
    acknowledged: bool = False


class ChallengeMethodRequest(BaseModel):
    """Task 4.3b — the customer chooses HOW to verify, not whether."""

    method: str


class ChallengeCancelRequest(BaseModel):
    """Task 4.3c — 'This wasn't me'."""

    reason: str | None = None


@router.post("/{transaction_id}/start")
def start_challenge(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Begin (or resume) the verification flow for a held investment."""
    return ChallengeService(db).start(transaction_id, current_user)


@router.post("/{transaction_id}/verify")
def verify_challenge(
    transaction_id: UUID,
    request: ChallengeVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify the current step. Completes the investment when all steps pass."""
    return ChallengeService(db).verify(
        transaction_id,
        current_user,
        answer=request.answer,
        acknowledged=request.acknowledged,
    )


@router.get("/{transaction_id}/methods")
def get_challenge_methods(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Alternative verification methods available for the current step."""
    return ChallengeService(db).available_methods(transaction_id, current_user)


@router.post("/{transaction_id}/method")
def switch_challenge_method(
    transaction_id: UUID,
    request: ChallengeMethodRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Switch the active verification step to another method.

    Verification remains mandatory — this only changes *how*. Downgrading to a
    weaker factor class costs an additional step so overall assurance holds.
    """
    return ChallengeService(db).switch_method(
        transaction_id, current_user, request.method
    )


@router.post("/{transaction_id}/resend-otp")
def resend_challenge_otp(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Issue a fresh OTP, invalidating the previous one."""
    return ChallengeService(db).resend_otp(transaction_id, current_user)


@router.post("/{transaction_id}/cancel")
def cancel_challenge(
    transaction_id: UUID,
    request: ChallengeCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Drop a held investment the customer says they did not start, and record it
    in the tamper-protected audit chain as a customer-reported fraud attempt.
    """
    return ChallengeService(db).cancel(
        transaction_id, current_user, reason=request.reason
    )
