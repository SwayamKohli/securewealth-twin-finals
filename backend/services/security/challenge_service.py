"""
services/security/challenge_service.py
======================================
Task 4.3 — Challenge Flow (adaptive verification, OTP only when required).

    Challenge
        ↓
    Security Question / MPIN / Risk Acknowledgement   (step 1, type-dependent)
        ↓
    Registered OTP                                     (only when required)
        ↓
    Investment completes

Step plans per challenge type (from security_rules.Challenge):
    DEVICE_CONFIRMATION      -> SECURITY_QUESTION + OTP   (unknown device)
    OTP_RECONFIRMATION       -> OTP                        (OTP distress signal)
    TRANSACTION_CONFIRMATION -> MPIN + OTP                 (amount spike)
    RISK_WARNING_ACCEPTANCE  -> ACKNOWLEDGE + MPIN         (softer risk)

Demo notes:
  * Challenge sessions + OTPs are held in process memory (fine for the demo;
    swap for Redis in production).
  * The generated OTP is returned in the /start response as `demo_otp` and
    logged server-side — in production it would be sent via SMS instead.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import verify_mpin
from database.repositories.auth_repository import AuthRepository
from models.enums import TransactionStatus
from models.user import User

logger = logging.getLogger(__name__)

OTP_TTL_MINUTES = 5
MAX_ATTEMPTS = 3

STEP_PLANS: dict[str, list[str]] = {
    "DEVICE_CONFIRMATION": ["SECURITY_QUESTION", "OTP"],
    "OTP_RECONFIRMATION": ["OTP"],
    "TRANSACTION_CONFIRMATION": ["MPIN", "OTP"],
    "RISK_WARNING_ACCEPTANCE": ["ACKNOWLEDGE", "MPIN"],
}
DEFAULT_PLAN = ["MPIN", "OTP"]

STEP_PROMPTS: dict[str, str] = {
    "SECURITY_QUESTION": "For your security, confirm your date of birth (YYYY-MM-DD).",
    "MPIN": "Re-enter your 6-digit MPIN to confirm this investment.",
    "OTP": "Enter the one-time password sent to your registered mobile number.",
    "ACKNOWLEDGE": "This investment looks unusual for you. Review the details and confirm you want to continue.",
}

# ── Task 4.3b — alternative verification methods ─────────────────────────────
#
# The customer may choose HOW to verify, never WHETHER to verify. A customer
# who cannot receive the OTP (travelling, no signal, lost SIM) must not be
# dead-ended after three failed attempts — that pushes them toward calling an
# "agent" who is often the fraudster.
#
# The rule that keeps this safe is COMPENSATION, not substitution:
#
#   Authentication factors fall into three classes —
#       possession  : OTP        (something you have — the registered SIM)
#       inherence   : BIOMETRIC  (something you are)
#       knowledge   : MPIN, SECURITY_QUESTION (something you know)
#
#   Swapping a possession/inherence factor for a KNOWLEDGE one is a downgrade,
#   so it costs TWO distinct knowledge factors instead of one. Swapping within
#   the same class, or upward, is one-for-one.
#
# Net effect: every alternative path is at least as strong as the path the risk
# engine originally asked for. ACKNOWLEDGE is excluded entirely — it is a
# comprehension gate, not an identity check, so there is nothing to substitute.

FACTOR_CLASS: dict[str, str] = {
    "OTP": "possession",
    "BIOMETRIC": "inherence",
    "MPIN": "knowledge",
    "SECURITY_QUESTION": "knowledge",
}
_STRONG_CLASSES = {"possession", "inherence"}

METHOD_LABELS: dict[str, str] = {
    "OTP": "One-time password",
    "MPIN": "Your 6-digit MPIN",
    "SECURITY_QUESTION": "Security question",
    "BIOMETRIC": "Fingerprint or Face ID",
}

METHOD_DESCRIPTIONS: dict[str, str] = {
    "OTP": "Sent to your registered mobile number.",
    "MPIN": "The PIN you use to sign in.",
    "SECURITY_QUESTION": "Confirm a detail only you would know.",
    "BIOMETRIC": "Verified on this device.",
}

SWITCHABLE_STEPS = frozenset({"OTP", "MPIN", "SECURITY_QUESTION", "BIOMETRIC"})

# In-memory challenge sessions: {transaction_id: session}
_sessions: dict[str, dict[str, Any]] = {}


def register_challenge(
    transaction_id: UUID | str,
    challenge_type: str,
    trigger_signal: str = "",
) -> None:
    """Called by the transaction pipeline when a decision comes back CHALLENGE."""
    plan = STEP_PLANS.get(challenge_type, DEFAULT_PLAN)
    _sessions[str(transaction_id)] = {
        "challenge_type": challenge_type or "RISK_WARNING_ACCEPTANCE",
        "trigger_signal": trigger_signal,
        "steps": list(plan),
        "current_step": 0,
        "otp": None,
        "otp_expires": None,
        "attempts": 0,
        "switched_methods": [],
        "created_at": datetime.now(timezone.utc),
    }


class ChallengeService:
    def __init__(self, db: Session):
        self.db = db

    # ── helpers ───────────────────────────────────────────────────────────

    def _get_pending_transaction(self, transaction_id: UUID, user_id: UUID):
        from database.repositories.transaction_repository import (
            TransactionRepository,
        )

        txn = TransactionRepository(self.db).get_by_id_and_user(
            transaction_id=transaction_id, user_id=user_id
        )
        if txn is None:
            raise HTTPException(status_code=404, detail="Transaction not found.")
        if txn.status != TransactionStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This transaction is not awaiting verification.",
            )
        return txn

    def _get_session(self, transaction_id: UUID, txn) -> dict[str, Any]:
        session = _sessions.get(str(transaction_id))
        if session is None:
            # Server restarted mid-challenge — rebuild a default session.
            register_challenge(transaction_id, txn.decision or "", "")
            session = _sessions[str(transaction_id)]
        return session

    @staticmethod
    def _issue_otp(session: dict[str, Any]) -> str:
        otp = f"{secrets.randbelow(1_000_000):06d}"
        session["otp"] = otp
        session["otp_expires"] = datetime.now(timezone.utc) + timedelta(
            minutes=OTP_TTL_MINUTES
        )
        logger.info("Challenge OTP issued (demo): %s", otp)
        return otp

    def _step_payload(self, session: dict[str, Any]) -> dict[str, Any]:
        steps = session["steps"]
        idx = session["current_step"]
        current = steps[idx] if idx < len(steps) else None
        payload: dict[str, Any] = {
            "challenge_type": session["challenge_type"],
            "trigger_signal": session["trigger_signal"],
            "steps": steps,
            "current_step": current,
            "step_number": idx + 1 if current else len(steps),
            "total_steps": len(steps),
            "prompt": STEP_PROMPTS.get(current or "", ""),
            "completed": current is None,
            "attempts_left": MAX_ATTEMPTS - session["attempts"],
        }
        if current == "OTP" and session.get("otp") is None:
            payload["demo_otp"] = self._issue_otp(session)
        payload["switched_methods"] = session.get("switched_methods", [])
        return payload

    # ── Task 4.3b — alternative method offers ─────────────────────────────

    def _method_available(self, method: str, user: User) -> tuple[bool, str]:
        """Can this customer actually complete this method right now?"""
        if method == "SECURITY_QUESTION":
            if user.date_of_birth is None:
                return False, "We do not have the details needed for this on file."
            return True, ""
        if method == "MPIN":
            creds = AuthRepository(self.db).get_credentials(user.user_id)
            if not creds or not creds.mpin_hash:
                return False, "No MPIN is set on this account."
            return True, ""
        if method == "OTP":
            if not getattr(user, "phone", None):
                return False, "No registered mobile number on file."
            return True, ""
        if method == "BIOMETRIC":
            # Deliberately NOT offered. A fingerprint match happens on the
            # handset; the bank server sees only a boolean it cannot verify,
            # so accepting it would be theatre. Real deployment needs hardware
            # key attestation (Android Keystore / iOS Secure Enclave) signing a
            # server challenge — out of scope here, and we say so rather than
            # pretending.
            return False, "Needs device key attestation — not available in this build."
        return False, "Unsupported method."

    def _substitution_for(
        self,
        current_step: str,
        method: str,
        session: dict[str, Any],
        user: User,
    ) -> list[str] | None:
        """
        The step(s) that replace `current_step` if the customer picks `method`.
        Returns None when the swap is not permitted.
        """
        if current_step not in SWITCHABLE_STEPS or method not in SWITCHABLE_STEPS:
            return None
        if method == current_step:
            return None

        idx = session["current_step"]
        done = session["steps"][:idx]          # already verified in this flow
        remaining = session["steps"][idx + 1:]  # still to come

        # Asking for the same factor twice adds no assurance, only friction.
        if method in remaining:
            return None

        from_class = FACTOR_CLASS.get(current_step, "knowledge")
        to_class = FACTOR_CLASS.get(method, "knowledge")

        # Same class, or upgrading to a stronger class → one-for-one.
        if to_class in _STRONG_CLASSES or from_class == to_class:
            return [method]

        # Downgrade (strong factor → knowledge): the customer must present TWO
        # distinct knowledge factors so overall assurance does not drop. One
        # already verified earlier in this same flow counts.
        others = [
            m
            for m, cls in FACTOR_CLASS.items()
            if cls == "knowledge" and m != method
        ]
        for other in others:
            if other in done or other in remaining:
                return [method]

        # Otherwise pair it with a knowledge factor the customer can actually use.
        for other in others:
            usable, _ = self._method_available(other, user)
            if usable:
                return [method, other]
        return None

    def available_methods(
        self, transaction_id: UUID, user: User
    ) -> dict[str, Any]:
        """Methods the customer may switch to for the CURRENT step."""
        txn = self._get_pending_transaction(transaction_id, user.user_id)
        session = self._get_session(transaction_id, txn)
        idx = session["current_step"]
        steps = session["steps"]
        current = steps[idx] if idx < len(steps) else None

        options: list[dict[str, Any]] = []
        if current in SWITCHABLE_STEPS:
            for method in ("OTP", "MPIN", "SECURITY_QUESTION", "BIOMETRIC"):
                usable, reason = self._method_available(method, user)
                substitution = self._substitution_for(current, method, session, user)
                is_current = method == current
                options.append(
                    {
                        "method": method,
                        "label": METHOD_LABELS[method],
                        "description": METHOD_DESCRIPTIONS[method],
                        "is_current": is_current,
                        "available": bool(
                            is_current or (usable and substitution is not None)
                        ),
                        "unavailable_reason": (
                            ""
                            if is_current or (usable and substitution)
                            else (reason or "Not a valid alternative for this step.")
                        ),
                        # Transparency: tell the customer up front that a weaker
                        # factor costs an extra step. No surprises mid-flow.
                        "extra_step_required": bool(
                            substitution and len(substitution) > 1
                        ),
                        "replaces_with": substitution or [],
                    }
                )

        return {
            "current_step": current,
            "switchable": current in SWITCHABLE_STEPS,
            "methods": options,
            "note": (
                "You choose how to verify, not whether to verify. Every "
                "alternative is at least as strong as the check we originally "
                "asked for."
            ),
        }

    def switch_method(
        self, transaction_id: UUID, user: User, method: str
    ) -> dict[str, Any]:
        """Replace the current verification step with the customer's choice."""
        txn = self._get_pending_transaction(transaction_id, user.user_id)
        session = self._get_session(transaction_id, txn)

        idx = session["current_step"]
        steps = session["steps"]
        if idx >= len(steps):
            raise HTTPException(status_code=400, detail="Challenge already completed.")

        current = steps[idx]
        method = (method or "").strip().upper()

        if method == current:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already verifying with this method.",
            )
        if current not in SWITCHABLE_STEPS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This step cannot be changed.",
            )

        usable, reason = self._method_available(method, user)
        if not usable:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

        substitution = self._substitution_for(current, method, session, user)
        if not substitution:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That method is not a valid alternative for this step.",
            )

        # Swap in the replacement step(s).
        session["steps"] = steps[:idx] + substitution + steps[idx + 1:]
        session["attempts"] = 0
        # Any OTP tied to the abandoned step is void — never let a stale code
        # stay live once the customer has moved on.
        session["otp"] = None
        session["otp_expires"] = None
        session.setdefault("switched_methods", []).append(
            {"from": current, "to": method, "at": datetime.now(timezone.utc).isoformat()}
        )

        logger.info(
            "Challenge method switched for txn %s: %s -> %s",
            transaction_id,
            current,
            method,
        )

        payload = self._step_payload(session)
        payload.update(
            switched=True,
            message=(
                f"Verification method changed to {METHOD_LABELS.get(method, method)}."
                + (
                    " Because this is a weaker check on its own, we will ask for "
                    "one more detail as well."
                    if len(substitution) > 1
                    else ""
                )
            ),
        )
        return payload

    def resend_otp(self, transaction_id: UUID, user: User) -> dict[str, Any]:
        """Issue a fresh OTP for the current step, invalidating the previous one."""
        txn = self._get_pending_transaction(transaction_id, user.user_id)
        session = self._get_session(transaction_id, txn)
        idx = session["current_step"]
        steps = session["steps"]
        if idx >= len(steps) or steps[idx] != "OTP":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No OTP is being requested right now.",
            )
        # A resend replaces the old code outright — two live codes would double
        # an attacker's guessing surface for no customer benefit.
        session["otp"] = None
        payload = self._step_payload(session)
        payload.update(
            resent=True,
            message="A new one-time password has been sent. The previous one no longer works.",
        )
        return payload

    # ── Task 4.3c — "This wasn't me" ──────────────────────────────────────

    def cancel(
        self, transaction_id: UUID, user: User, reason: str | None = None
    ) -> dict[str, Any]:
        """
        The customer says they did not start this investment.

        The money never moved (a CHALLENGE holds the transaction as PENDING),
        so cancelling is safe and immediate. It is also the single most valuable
        fraud signal the bank can get, so it is written to the tamper-protected
        audit chain as a customer-reported fraud attempt.
        """
        txn = self._get_pending_transaction(transaction_id, user.user_id)
        session = _sessions.get(str(transaction_id), {})

        txn.status = TransactionStatus.FAILED
        self.db.commit()
        _sessions.pop(str(transaction_id), None)

        self._log_reported_fraud(txn, user, session, reason)

        return {
            "cancelled": True,
            "transaction_status": "FAILED",
            "reported": True,
            "message": (
                "Investment stopped. No money left your account. We have recorded "
                "this as a suspected fraud attempt and your account is being "
                "monitored more closely."
            ),
            "next_steps": [
                "Change your MPIN if you think someone else knows it.",
                "Do not share OTPs with anyone, including bank staff.",
                "Call the Punjab & Sind Bank helpline if you were contacted by someone.",
            ],
        }

    def _log_reported_fraud(
        self,
        txn,
        user: User,
        session: dict[str, Any],
        reason: str | None,
    ) -> None:
        """Write the report to the audit chain. Never breaks the cancellation."""
        try:
            from core.dependencies import (
                get_hash_chain_service,
                get_signature_service,
            )
            from database.repositories.audit_repository import AuditRepository
            from services.audit_service import AuditLogData, AuditService

            AuditService(
                audit_repo=AuditRepository(self.db),
                hash_service=get_hash_chain_service(),
                signature_service=get_signature_service(),
            ).log_security_decision(
                AuditLogData(
                    transaction_id=txn.transaction_id,
                    user_id=user.user_id,
                    device_id=None,
                    account_id=txn.account_id,
                    event_type="CUSTOMER_REPORTED_FRAUD",
                    final_decision="BLOCK",
                    risk_score=100,
                    amount=txn.amount,
                    channel=txn.channel.value if txn.channel else None,
                    ai_status="NORMAL",
                    ai_confidence=None,
                    unknown_risk_severity=None,
                    unknown_risk_applied=False,
                    unknown_risk_decision=None,
                    unknown_risk_reason_code=None,
                    challenge_required=True,
                    challenge_type=session.get("challenge_type"),
                    challenge_trigger_signal=session.get("trigger_signal"),
                    security_signals={
                        "customer_reported": True,
                        "reason": reason or "not_me",
                        "steps_planned": session.get("steps", []),
                        "step_reached": session.get("current_step", 0),
                    },
                    audit_note=(
                        "Customer rejected this investment at the verification "
                        "step, reporting it as not initiated by them."
                    ),
                    compliance_reference=None,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception(
                "Failed to write reported-fraud audit record for txn %s "
                "(the investment WAS still cancelled).",
                txn.transaction_id,
            )

    # ── public API ────────────────────────────────────────────────────────

    def start(self, transaction_id: UUID, user: User) -> dict[str, Any]:
        txn = self._get_pending_transaction(transaction_id, user.user_id)
        session = self._get_session(transaction_id, txn)
        return self._step_payload(session)

    def verify(
        self,
        transaction_id: UUID,
        user: User,
        answer: str | None = None,
        acknowledged: bool = False,
    ) -> dict[str, Any]:
        txn = self._get_pending_transaction(transaction_id, user.user_id)
        session = self._get_session(transaction_id, txn)

        steps = session["steps"]
        idx = session["current_step"]
        if idx >= len(steps):
            raise HTTPException(status_code=400, detail="Challenge already completed.")

        step = steps[idx]
        ok = self._verify_step(step, session, user, answer, acknowledged)

        if not ok:
            session["attempts"] += 1
            if session["attempts"] >= MAX_ATTEMPTS:
                self._fail_transaction(txn)
                _sessions.pop(str(transaction_id), None)
                return {
                    "verified": False,
                    "completed": True,
                    "transaction_status": "FAILED",
                    "message": (
                        "Verification failed too many times. The investment was "
                        "cancelled to protect your account."
                    ),
                }
            payload = self._step_payload(session)
            payload.update(
                verified=False,
                message="That did not match. Please try again.",
            )
            return payload

        # Step passed → advance
        session["current_step"] += 1
        session["attempts"] = 0

        if session["current_step"] >= len(steps):
            # All steps passed → complete the investment
            from services.transaction_service import TransactionService

            TransactionService(self.db).complete_challenged_transaction(
                transaction_id=transaction_id, user_id=user.user_id
            )
            _sessions.pop(str(transaction_id), None)
            return {
                "verified": True,
                "completed": True,
                "transaction_status": "SUCCESS",
                "message": "Identity verified. Your investment has been completed.",
            }

        payload = self._step_payload(session)
        payload.update(verified=True, message="Verified. One more step.")
        return payload

    # ── step validators ───────────────────────────────────────────────────

    def _verify_step(
        self,
        step: str,
        session: dict[str, Any],
        user: User,
        answer: str | None,
        acknowledged: bool,
    ) -> bool:
        if step == "ACKNOWLEDGE":
            return bool(acknowledged)

        if step == "SECURITY_QUESTION":
            if not answer or user.date_of_birth is None:
                return False
            return answer.strip() == user.date_of_birth.isoformat()

        if step == "MPIN":
            if not answer:
                return False
            creds = AuthRepository(self.db).get_credentials(user.user_id)
            return bool(creds and verify_mpin(answer.strip(), creds.mpin_hash))

        if step == "OTP":
            otp = session.get("otp")
            expires = session.get("otp_expires")
            if not answer or otp is None or expires is None:
                return False
            if datetime.now(timezone.utc) > expires:
                session["otp"] = None  # force reissue on next /start
                return False
            return answer.strip() == otp

        return False

    def _fail_transaction(self, txn) -> None:
        txn.status = TransactionStatus.FAILED
        self.db.commit()
