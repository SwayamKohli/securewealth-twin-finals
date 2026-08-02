"""
seed_demo.py — One-command demo environment
===========================================
Creates a complete, realistic demo user from scratch:

  * User + login credentials      (SecureWealth ID SW10000001 / MPIN 123456)
  * Trusted primary device        (120 days old -> low device risk)
  * 2 Savings accounts            (SBI ₹2,50,000 / PNB ₹1,20,000)
  * FD + RD deposits, home loan, debit card
  * Behavioural profile           (daytime user, ~₹4k typical investment)
  * 30 days of SIP history        (so the fraud engine has a real baseline)
  * OPTIONAL: wipes the audit chain (fixes "Chain broken at audit_id=...")

Usage (from backend/, venv active):
    python scripts/seed_demo.py                 # seed / re-seed demo user
    python scripts/seed_demo.py --reset-audit   # also wipe + restart audit chain

Safe to re-run: deletes and recreates the demo user's data each time.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEMO_PHONE = "9876543210"
DEMO_MPIN = "123456"
DEMO_CUSTOMER_ID = "SW10000001"

SIP_FUNDS = [
    ("Bluechip Equity Fund SIP", "EQUITY_MUTUAL_FUND"),
    ("Corporate Bond Debt Fund SIP", "DEBT_MUTUAL_FUND"),
    ("Balanced Advantage Fund SIP", "BALANCED_MUTUAL_FUND"),
    ("Nifty 50 Index Fund SIP", "INDEX_MUTUAL_FUND"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the SecureWealth Twin demo user.")
    parser.add_argument(
        "--reset-audit",
        action="store_true",
        help="Wipe audit_logs + replicas so the hash chain restarts cleanly.",
    )
    args = parser.parse_args()

    from core.security import hash_mpin
    from database.connection import SessionLocal
    from models.account import Account
    from models.auth_credential import AuthCredential
    from models.behavioural_profile import BehaviouralProfile
    from models.card import Card
    from models.deposit import Deposit
    from models.device import Device
    from models.loan import Loan
    from models.transaction import Transaction
    from models.user import User
    from models.enums import (
        AccountType,
        CardType,
        DepositType,
        DeviceType,
        LoanType,
        TransactionChannel,
        TransactionStatus,
        TrustStatus,
    )

    now = datetime.now(timezone.utc)
    db = SessionLocal()

    try:
        # ── 0) Optional audit chain reset ────────────────────────────────
        if args.reset_audit:
            from models.audit import AuditLog
            from models.audit_replica import AuditReplica1, AuditReplica2, AuditReplica3

            for model in (AuditReplica1, AuditReplica2, AuditReplica3, AuditLog):
                deleted = db.query(model).delete()
                print(f"  audit reset: removed {deleted} rows from {model.__tablename__}")
            db.commit()
            print("✔ Audit chain wiped — it will restart cleanly on the next investment.")

        # ── 1) Remove any previous demo user and all of their data ───────
        # The ORM relationships are not configured with delete-orphan cascade,
        # so child rows are removed explicitly (deepest dependency first) and
        # the DB-level ON DELETE CASCADE handles anything left.
        existing = (
            db.query(User)
            .filter(
                (User.phone == DEMO_PHONE)
                | (User.customer_id == DEMO_CUSTOMER_ID)
            )
            .first()
        )
        if existing:
            uid = existing.user_id
            for model in (
                Transaction,
                BehaviouralProfile,
                Card,
                Loan,
                Deposit,
                Account,
                Device,
                AuthCredential,
            ):
                db.query(model).filter(model.user_id == uid).delete(
                    synchronize_session=False
                )
            db.flush()
            db.query(User).filter(User.user_id == uid).delete(
                synchronize_session=False
            )
            db.commit()
            db.expunge_all()
            print("✔ Previous demo user and all related data removed.")

        # ── 2) User + credentials ────────────────────────────────────────
        user = User(
            customer_id=DEMO_CUSTOMER_ID,  # demo SecureWealth ID (login credential)
            full_name="Swayam Kohli",
            phone=DEMO_PHONE,
            email="swayam.demo@securewealth.in",
            date_of_birth=date(2003, 5, 15),
            is_active=True,
            aa_consent=True,  # demo user has already consented to aggregation
            aa_consent_at=now,
        )
        db.add(user)
        db.flush()

        db.add(AuthCredential(user_id=user.user_id, mpin_hash=hash_mpin(DEMO_MPIN)))

        # ── 3) Trusted primary device (120 days old) ─────────────────────
        device = Device(
            user_id=user.user_id,
            device_name="Swayam's Pixel 8",
            device_type=DeviceType.ANDROID,
            sim_id="SIM-AIRTEL-01",
            trust_status=TrustStatus.TRUSTED,
            first_seen=now - timedelta(days=120),
            last_seen=now,
            is_active=True,
        )
        db.add(device)

        # ── 4) Accounts ──────────────────────────────────────────────────
        primary = Account(
            user_id=user.user_id,
            bank_name="State Bank of India",
            account_type=AccountType.SAVINGS,
            account_number_masked="XXXXXX4821",
            balance=Decimal("250000.00"),
            currency="INR",
        )
        secondary = Account(
            user_id=user.user_id,
            bank_name="Punjab National Bank",
            account_type=AccountType.SAVINGS,
            account_number_masked="XXXXXX7710",
            balance=Decimal("120000.00"),
            currency="INR",
        )
        db.add_all([primary, secondary])
        db.flush()

        # ── 5) Deposits, loan, card ──────────────────────────────────────
        db.add_all(
            [
                Deposit(
                    user_id=user.user_id,
                    deposit_type=DepositType.FD,
                    principal=Decimal("300000.00"),
                    interest_rate=Decimal("7.10"),
                    start_date=(now - timedelta(days=165)).date(),
                    maturity_date=(now + timedelta(days=200)).date(),
                    institution="State Bank of India",
                ),
                Deposit(
                    user_id=user.user_id,
                    deposit_type=DepositType.RD,
                    principal=Decimal("60000.00"),
                    interest_rate=Decimal("6.80"),
                    start_date=(now - timedelta(days=365)).date(),
                    maturity_date=(now + timedelta(days=365)).date(),
                    institution="Punjab National Bank",
                ),
                Loan(
                    user_id=user.user_id,
                    loan_type=LoanType.HOME,
                    outstanding_amount=Decimal("1200000.00"),
                    emi=Decimal("18000.00"),
                    interest_rate=Decimal("8.40"),
                    remaining_tenure=132,
                ),
                Card(
                    user_id=user.user_id,
                    card_type=CardType.DEBIT,
                    issuer="State Bank of India",
                    reward_type="CASHBACK",
                    cashback_rate=Decimal("1.00"),
                    credit_limit=Decimal("0.00"),
                ),
            ]
        )

        # ── 6) Behavioural profile ───────────────────────────────────────
        db.add(
            BehaviouralProfile(
                user_id=user.user_id,
                active_hours="09-22",
                average_otp_time=Decimal("8.50"),
                round_number_frequency=Decimal("0.40"),
                transaction_velocity=Decimal("3.00"),
                baseline_metadata={"typical_amount": 4000, "seeded": True},
                last_updated=now,
            )
        )

        # ── 7) 30 days of SIP history (fraud-engine baseline) ────────────
        rng = random.Random(42)  # deterministic seed data
        txn_count = 0
        for days_ago in range(30, 0, -1):
            if rng.random() < 0.35:  # ~10-12 investments over the month
                fund_name, _ = rng.choice(SIP_FUNDS)
                when = now - timedelta(
                    days=days_ago, hours=rng.randint(-4, 4), minutes=rng.randint(0, 59)
                )
                when = when.replace(hour=max(9, min(21, when.hour)))
                db.add(
                    Transaction(
                        user_id=user.user_id,
                        account_id=primary.account_id,
                        amount=Decimal(str(rng.choice([2000, 2500, 3000, 4000, 5000, 6000]))),
                        merchant_name=fund_name,
                        merchant_category="MUTUAL_FUND",
                        channel=TransactionChannel.UPI,
                        transaction_time=when,
                        status=TransactionStatus.SUCCESS,
                        decision="ALLOW",
                        decision_timestamp=when,
                    )
                )
                txn_count += 1

        db.commit()

        print(
            f"""
✔ Demo environment ready.

  Login       : SecureWealth ID {DEMO_CUSTOMER_ID} / MPIN {DEMO_MPIN}
  Accounts    : SBI Savings ₹2,50,000 (primary) | PNB Savings ₹1,20,000
  Wealth      : FD ₹3,00,000 @7.1% | RD ₹60,000 @6.8% | Home loan ₹12,00,000
  Device      : Trusted Android, 120 days old
  History     : {txn_count} SIP investments over the last 30 days (₹2k–₹6k)

  Demo hints:
    • Invest ₹3,000–5,000  -> expect ALLOW (matches baseline)
    • Invest ₹90,000+      -> expect WARN / CHALLENGE (amount spike)
    • Fire 4+ investments in a minute -> velocity escalation
"""
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
