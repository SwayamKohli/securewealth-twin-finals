from decimal import Decimal
import random

from database.connection import SessionLocal

from database.repositories.audit_repository import AuditRepository

from services.audit_service import (
    AuditLogData,
    AuditService,
)

from audit.hash_chain import HashChainService
from audit.signature_service import SignatureService

from core.dependencies import get_signature_service


DECISIONS = [
    ("ALLOW", 12),
    ("ALLOW", 18),
    ("ALLOW", 25),
    ("REVIEW", 55),
    ("REVIEW", 67),
    ("REVIEW", 73),
    ("BLOCK", 91),
    ("BLOCK", 96),
]

CHANNELS = [
    "UPI",
    "CARD",
    "ATM",
    "NET_BANKING",
    "MOBILE_BANKING",
]

AI_STATUS = [
    "APPROVED",
    "FLAGGED",
    "REVIEW_REQUIRED",
]

UNKNOWN_SEVERITY = [
    None,
    "LOW",
    "MEDIUM",
    "HIGH",
]

CHALLENGES = [
    None,
    "OTP",
    "BIOMETRIC",
    "DEVICE_BINDING",
]

COMPLIANCE = [
    "RBI-FDS-001",
    "AML-002",
    "PSD2-003",
    "KYC-004",
]


def random_record() -> AuditLogData:

    decision, risk = random.choice(DECISIONS)

    amount = Decimal(
        str(
            random.choice(
                [
                    500,
                    1200,
                    2500,
                    4500,
                    10000,
                    25000,
                    50000,
                    100000,
                    250000,
                ]
            )
        )
    )

    channel = random.choice(CHANNELS)

    ai_status = random.choice(AI_STATUS)

    ai_confidence = Decimal(
        str(
            round(
                random.uniform(0.65, 0.99),
                2,
            )
        )
    )

    unknown_applied = random.choice([True, False])

    severity = (
        random.choice(UNKNOWN_SEVERITY)
        if unknown_applied
        else None
    )

    challenge_required = (
        decision != "ALLOW"
        or risk >= 70
    )

    challenge_type = (
        random.choice(CHALLENGES[1:])
        if challenge_required
        else None
    )

    return AuditLogData(

        transaction_id=None,
        user_id=None,
        device_id=None,
        account_id=None,

        event_type="TRANSACTION_SECURITY",

        final_decision=decision,
        risk_score=risk,

        amount=amount,
        channel=channel,

        ai_status=ai_status,
        ai_confidence=ai_confidence,

        unknown_risk_severity=severity,
        unknown_risk_applied=unknown_applied,
        unknown_risk_decision=(
            "REVIEW"
            if unknown_applied
            else None
        ),
        unknown_risk_reason_code=(
            "ZERO_DAY_PATTERN"
            if unknown_applied
            else None
        ),

        challenge_required=challenge_required,
        challenge_type=challenge_type,
        challenge_trigger_signal=(
            "HIGH_RISK_SCORE"
            if challenge_required
            else None
        ),

        security_signals={
            "velocity_score": random.randint(0, 100),
            "device_trust": random.choice(
                [
                    "LOW",
                    "MEDIUM",
                    "HIGH",
                ]
            ),
            "location_change": random.choice(
                [
                    True,
                    False,
                ]
            ),
            "vpn_detected": random.choice(
                [
                    True,
                    False,
                ]
            ),
            "new_payee": random.choice(
                [
                    True,
                    False,
                ]
            ),
        },

        audit_note=f"Mock audit record for {channel} transaction.",

        compliance_reference=random.choice(COMPLIANCE),
    )


def main():

    random.seed(42)

    db = SessionLocal()

    try:

        repository = AuditRepository(db)

        audit_service = AuditService(
            audit_repo=repository,
            hash_service=HashChainService(),
            signature_service=get_signature_service(),
        )

        print("\nSeeding audit records...\n")

        for i in range(20):

            audit = audit_service.log_security_decision(
                random_record()
            )

            print(
                f"{i+1:02d}. "
                f"{audit.audit_id} | "
                f"{audit.final_decision} | "
                f"Risk={audit.risk_score}"
            )

        db.commit()

        print("\n=====================================")
        print("Audit Seed Completed Successfully")
        print("=====================================")

        print("Audit Logs      : 20")
        print("Audit Replica 1 : 20")
        print("Audit Replica 2 : 20")
        print("Audit Replica 3 : 20")

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()