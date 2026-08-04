"""
seed_personas.py — Five demo customers, five different stories
==============================================================

WHY THIS REPLACES seed_demo.py
------------------------------
The old seeder wrote ONLY positive investment rows. get_cashflow() treats every
positive amount as income, so the demo customer had:

    total_expenses  = 0
    monthly_expenses = 0
    months_of_runway = 0.0     <- the divide-by-zero fallback, not a real figure
    savings_rate     = 100%

Two consequences. First the numbers were nonsense: a customer who spends nothing
and saves everything, yet somehow has zero months of runway. Second, and the
reason you are reading this file: `runway 0.0 < EMERGENCY_FUND_MONTHS (4)` is
always true, so `emergency_fund_implicit` fired on every request and "Build
Emergency Fund — Liquid Fixed Deposit" was the only advice the demo could ever
produce. The wealth engine was working correctly on data that could not vary.

Each persona below therefore gets a real expense side — salary credits and
spending debits over 90 days — so income, expenses, runway, savings rate and
DTI are all derived from something true. Then their balances, deposits and
loans are tuned so that each one lands in a DIFFERENT branch of the engine.

THE FIVE PERSONAS
-----------------
                     runway   DTI    idle      the advice they get
  Swayam  SW10000001  5.2mo   0.14   normal    growth SIP — healthy, invests
  Mahak   SW10000002  1.4mo   0.09   normal    Build emergency fund first
  Archit  SW10000003  5.0mo   0.58   normal    Pay down the costliest loan
  Ayush   SW10000004  15mo    0.00   very high Deploy idle cash + FD maturing
  Vishwas SW10000005  4.6mo   0.22   normal    No surplus -> reduce expenses

All five share MPIN 123456 so nobody fumbles a login on stage.

SECURITY SCENARIOS
------------------
Each persona also carries a different behavioural baseline, so the same action
produces a different security verdict:

  Swayam   typical ₹3-6k SIPs      -> ₹4k ALLOW,  ₹95k CHALLENGE (amount spike)
  Mahak    typical ₹1-2k SIPs      -> ₹40k CHALLENGE at a much lower amount
  Archit   no history at all       -> first investment has no baseline to match
  Ayush    large regular investor  -> ₹90k is normal for him, still ALLOW
  Vishwas  night-time investor     -> daytime activity is the unusual one

Usage (from backend/, venv active):
    python scripts/seed_personas.py                 # rebuild all five
    python scripts/seed_personas.py --reset-audit   # also wipe the audit chain
    python scripts/seed_personas.py --only swayam   # rebuild one persona

Safe to re-run: each persona's data is deleted and recreated.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MPIN = "123456"

SIP_FUNDS = [
    "Bluechip Equity Fund SIP",
    "Corporate Bond Debt Fund SIP",
    "Balanced Advantage Fund SIP",
    "Nifty 50 Index Fund SIP",
]

# Everyday spending the expense side is built from. Category names only — no
# merchant is real, and none of this is shown to the customer as a brand.
SPEND = [
    ("Rent", 0.42),           # share of monthly expenses
    ("Groceries", 0.18),
    ("Utilities", 0.08),
    ("Fuel & Transport", 0.10),
    ("Dining", 0.09),
    ("Shopping", 0.08),
    ("Healthcare", 0.05),
]


@dataclass
class Persona:
    key: str
    customer_id: str
    full_name: str
    phone: str
    dob: date
    # Deliberately NOT a hardware model. The seeder cannot know what phone
    # the demo actually runs on, and the app shows this string next to
    # "Recognised device" — so "Vishwas's Redmi Note 13" appeared on a
    # phone that was not a Redmi. It also contradicted device_type, which
    # is ANDROID for everyone including the persona labelled iPhone.
    # "<Name>'s phone" is true on any handset.
    device_name: str
    device_age_days: int
    trusted: bool

    monthly_income: Decimal        # salary credit
    monthly_expenses: Decimal      # total debits per month
    primary_balance: Decimal       # main savings account
    second_balance: Decimal        # secondary account (0 = none)

    deposits: list = field(default_factory=list)   # (type, principal, rate, days_to_maturity)
    loans: list = field(default_factory=list)      # (type, outstanding, emi, rate, months_left)

    sip_range: tuple = (2000, 6000)
    sip_days: int = 90
    sip_density: float = 0.30      # chance of an investment on a given day
    night_owl: bool = False

    story: str = ""
    demo_hint: str = ""


# ── The five ─────────────────────────────────────────────────────────────────
#
# runway = primary_balance / monthly_expenses. Keep it ABOVE 4 for anyone who
# should not be told to build an emergency fund, and below it for Mahak, who
# should. DTI = emi / income; above 0.50 triggers the debt-reduction branch.

PERSONAS: list[Persona] = [
    Persona(
        key="swayam",
        customer_id="SW10000001",
        full_name="Swayam Kohli",
        phone="9876543210",
        dob=date(2003, 5, 15),
        device_name="Swayam's phone",
        device_age_days=120,
        trusted=True,
        monthly_income=Decimal("120000"),
        monthly_expenses=Decimal("54000"),
        primary_balance=Decimal("280000"),      # runway 5.2 months
        second_balance=Decimal("120000"),
        deposits=[("FD", "300000", "7.10", 400), ("RD", "60000", "6.80", 300)],
        loans=[("HOME", "1200000", "17000", "8.60", 96)],   # DTI 0.14
        sip_range=(3000, 6000),
        sip_density=0.35,
        story="Healthy investor. Emergency fund already covered, low debt, real "
              "surplus — the engine can finally recommend growth.",
        demo_hint="₹4,000 -> ALLOW  |  ₹95,000 -> CHALLENGE (amount spike)",
    ),
    Persona(
        key="mahak",
        customer_id="SW10000002",
        full_name="Mahak Singh",
        phone="9876543211",
        dob=date(2002, 11, 3),
        device_name="Mahak's phone",
        device_age_days=60,
        trusted=True,
        monthly_income=Decimal("70000"),
        monthly_expenses=Decimal("52000"),
        primary_balance=Decimal("74000"),       # runway 1.4 months -> EF gap
        second_balance=Decimal("0"),
        deposits=[],
        loans=[("PERSONAL", "180000", "6200", "13.50", 30)],   # DTI 0.09
        sip_range=(1000, 2000),                 # small baseline
        sip_density=0.22,
        story="Thin safety net. Four months of expenses is ₹2,08,000 and she "
              "holds ₹74,000 — the engine puts the emergency fund first, "
              "before any growth product.",
        demo_hint="₹1,500 -> ALLOW  |  ₹40,000 -> CHALLENGE (spike vs HER baseline)",
    ),
    Persona(
        key="archit",
        customer_id="SW10000003",
        full_name="Archit Sharma",
        phone="9876543212",
        dob=date(2001, 7, 22),
        device_name="Archit's phone",
        device_age_days=5,                      # new device
        trusted=False,
        monthly_income=Decimal("90000"),
        monthly_expenses=Decimal("38000"),
        primary_balance=Decimal("190000"),      # runway 5.0 months
        second_balance=Decimal("0"),
        deposits=[("FD", "120000", "6.90", 500)],
        # EMI 52,000 on 90,000 income -> DTI 0.58, above the 0.50 stress line
        loans=[
            ("HOME", "2600000", "31000", "9.20", 120),
            ("CAR", "480000", "13000", "11.40", 40),
            ("PERSONAL", "220000", "8000", "15.80", 30),
        ],
        sip_range=(2000, 3000),
        sip_density=0.08,                       # barely invests
        story="Debt-heavy. Over half his income goes to EMIs, so the engine "
              "tells him to clear the 15.8% personal loan before investing — "
              "a guaranteed return no fund can match.",
        demo_hint="New device + any investment -> extra verification",
    ),
    Persona(
        key="ayush",
        customer_id="SW10000004",
        full_name="Ayush Verma",
        phone="9876543213",
        dob=date(2000, 2, 9),
        device_name="Ayush's phone",
        device_age_days=200,
        trusted=True,
        monthly_income=Decimal("150000"),
        monthly_expenses=Decimal("58000"),
        primary_balance=Decimal("900000"),      # idle >> 2x expenses
        second_balance=Decimal("350000"),
        # FD maturing inside 90 days -> the reinvest nudge
        deposits=[("FD", "500000", "7.25", 45), ("FD", "250000", "7.00", 600)],
        loans=[],                               # DTI 0.00
        sip_range=(20000, 40000),               # large regular investor
        sip_density=0.40,
        story="Cash sitting idle. ₹12.5L in savings earning nothing, and a "
              "₹5L FD maturing in 45 days — the engine flags both.",
        demo_hint="₹90,000 -> ALLOW (normal for him)  |  ₹5,00,000 -> CHALLENGE",
    ),
    Persona(
        key="vishwas",
        customer_id="SW10000005",
        full_name="Vishwas Kesarwani",
        phone="9876543214",
        dob=date(2002, 9, 28),
        device_name="Vishwas's phone",
        device_age_days=45,
        trusted=True,
        monthly_income=Decimal("62000"),
        monthly_expenses=Decimal("61000"),      # spends almost all of it
        primary_balance=Decimal("280000"),
        second_balance=Decimal("0"),
        deposits=[],
        loans=[("EDUCATION", "400000", "9000", "10.20", 48)],
        sip_range=(1000, 1500),
        sip_density=0.10,
        night_owl=True,
        story="No investable surplus. Income ₹62,000 against ₹61,000 of "
              "spending, so the engine SUPPRESSES growth advice and tells him "
              "to fix expenses first — the honest answer, not a product pitch.",
        demo_hint="Advice suppressed  |  late-night investing is his normal",
    ),
]


def build(db, p: Persona, now: datetime, models: dict) -> int:
    """Create one persona from scratch. Returns the transaction count."""
    (User, AuthCredential, Device, Account, Deposit, Loan, Card, Transaction,
     BehaviouralProfile) = (
        models["User"], models["AuthCredential"], models["Device"],
        models["Account"], models["Deposit"], models["Loan"], models["Card"],
        models["Transaction"], models["BehaviouralProfile"])
    E = models["enums"]
    hash_mpin = models["hash_mpin"]

    # ── Remove any previous copy ─────────────────────────────────────────
    # Relationships have no delete-orphan cascade, so children go first, in
    # dependency order.
    existing = (
        db.query(User)
        .filter((User.phone == p.phone) | (User.customer_id == p.customer_id))
        .first()
    )
    if existing:
        uid = existing.user_id
        for model in (Transaction, BehaviouralProfile, Card, Loan, Deposit,
                      Account, Device, AuthCredential):
            db.query(model).filter(model.user_id == uid).delete(
                synchronize_session=False)
        db.flush()
        db.query(User).filter(User.user_id == uid).delete(synchronize_session=False)
        db.commit()
        db.expunge_all()

    # ── User ─────────────────────────────────────────────────────────────
    user = User(
        customer_id=p.customer_id,
        full_name=p.full_name,
        phone=p.phone,
        email=f"{p.key}.demo@securewealth.in",
        date_of_birth=p.dob,
        is_active=True,
        aa_consent=True,
        aa_consent_at=now,
    )
    db.add(user)
    db.flush()
    db.add(AuthCredential(user_id=user.user_id, mpin_hash=hash_mpin(MPIN)))

    # ── Device ───────────────────────────────────────────────────────────
    db.add(Device(
        user_id=user.user_id,
        device_name=p.device_name,
        device_type=E["DeviceType"].ANDROID,
        sim_id=f"SIM-{p.key.upper()}-01",
        trust_status=E["TrustStatus"].TRUSTED if p.trusted else E["TrustStatus"].PENDING,
        first_seen=now - timedelta(days=p.device_age_days),
        last_seen=now,
        is_active=True,
    ))

    # ── Accounts ─────────────────────────────────────────────────────────
    primary = Account(
        user_id=user.user_id,
        bank_name="Punjab & Sind Bank",
        account_type=E["AccountType"].SAVINGS,
        account_number_masked=f"XXXXXX{p.phone[-4:]}",
        balance=p.primary_balance,
        currency="INR",
    )
    db.add(primary)
    if p.second_balance > 0:
        db.add(Account(
            user_id=user.user_id,
            bank_name="State Bank of India",
            account_type=E["AccountType"].SAVINGS,
            account_number_masked=f"XXXXXX{int(p.phone[-4:]) % 9000 + 1000}",
            balance=p.second_balance,
            currency="INR",
        ))
    db.flush()

    # ── Deposits ─────────────────────────────────────────────────────────
    for dtype, principal, rate, days_to_maturity in p.deposits:
        db.add(Deposit(
            user_id=user.user_id,
            deposit_type=E["DepositType"][dtype],
            principal=Decimal(principal),
            interest_rate=Decimal(rate),
            start_date=(now - timedelta(days=365)).date(),
            maturity_date=(now + timedelta(days=days_to_maturity)).date(),
            institution="Punjab & Sind Bank",
        ))

    # ── Loans ────────────────────────────────────────────────────────────
    for ltype, outstanding, emi, rate, months_left in p.loans:
        db.add(Loan(
            user_id=user.user_id,
            loan_type=E["LoanType"][ltype],
            outstanding_amount=Decimal(outstanding),
            emi=Decimal(emi),
            interest_rate=Decimal(rate),
            remaining_tenure=months_left,
        ))

    db.add(Card(
        user_id=user.user_id,
        card_type=E["CardType"].DEBIT,
        issuer="Punjab & Sind Bank",
        reward_type="CASHBACK",
        cashback_rate=Decimal("1.00"),
        credit_limit=Decimal("0.00"),
    ))

    # ── Cashflow: salary in, spending out ────────────────────────────────
    #
    # THIS is the part the old seeder was missing. Without debit rows,
    # total_expenses is 0 and every ratio derived from it is meaningless.
    rng = random.Random(hash(p.key) % (2**31))
    txn_count = 0
    months = 3

    for m in range(months, 0, -1):
        month_start = now - timedelta(days=30 * m)

        # Salary credit near the start of the month.
        #
        # Deliberately month_start + 1 day, not month_start. The cash-flow
        # window is a rolling 30 days ending now, and the newest month_start is
        # exactly now - 30 days — so a salary posted ON it falls a hair outside
        # the window and the customer reads as having no income at all, while
        # their spending (spread 1-27 days in) stays inside. That produced a
        # negative surplus for every persona. The spending below is already
        # offset this way; the salary needs to be too.
        salary_at = month_start + timedelta(days=1)
        db.add(Transaction(
            user_id=user.user_id,
            account_id=primary.account_id,
            amount=p.monthly_income,
            merchant_name="Salary Credit",
            merchant_category="SALARY",
            channel=E["TransactionChannel"].NEFT,
            transaction_time=salary_at,
            status=E["TransactionStatus"].SUCCESS,
            decision="ALLOW",
            decision_timestamp=salary_at,
        ))
        txn_count += 1

        # Spending spread across the month, as NEGATIVE amounts so the
        # aggregation service counts them as expenses.
        for label, share in SPEND:
            amount = (p.monthly_expenses * Decimal(str(share))).quantize(Decimal("1"))
            when = month_start + timedelta(
                days=rng.randint(1, 27), hours=rng.randint(9, 20)
            )
            db.add(Transaction(
                user_id=user.user_id,
                account_id=primary.account_id,
                amount=-amount,
                merchant_name=label,
                merchant_category="EXPENSE",
                channel=E["TransactionChannel"].CARD,
                transaction_time=when,
                status=E["TransactionStatus"].SUCCESS,
                decision="ALLOW",
                decision_timestamp=when,
            ))
            txn_count += 1

    # ── Investment history: the fraud engine's baseline ──────────────────
    lo, hi = p.sip_range
    for days_ago in range(p.sip_days, 0, -1):
        if rng.random() >= p.sip_density:
            continue
        when = now - timedelta(days=days_ago, minutes=rng.randint(0, 59))
        hour = rng.randint(0, 4) if p.night_owl else rng.randint(9, 21)
        when = when.replace(hour=hour)
        db.add(Transaction(
            user_id=user.user_id,
            account_id=primary.account_id,
            amount=Decimal(str(rng.randrange(lo, hi + 1, 500))),
            merchant_name=rng.choice(SIP_FUNDS),
            merchant_category="MUTUAL_FUND",
            channel=E["TransactionChannel"].UPI,
            transaction_time=when,
            status=E["TransactionStatus"].SUCCESS,
            decision="ALLOW",
            decision_timestamp=when,
        ))
        txn_count += 1

    # ── Behavioural profile ──────────────────────────────────────────────
    db.add(BehaviouralProfile(
        user_id=user.user_id,
        active_hours="00:00-05:00" if p.night_owl else "09:00-21:00",
        average_otp_time=Decimal("18.5"),
        round_number_frequency=Decimal("0.15"),
        transaction_velocity=Decimal(str(round(p.sip_density * 10, 2))),
        baseline_metadata={
            "typical_amount_min": lo,
            "typical_amount_max": hi,
            "monthly_income": float(p.monthly_income),
            "monthly_expenses": float(p.monthly_expenses),
        },
        last_updated=now,
    ))

    db.commit()
    return txn_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed five demo personas, each exercising a different path."
    )
    parser.add_argument("--reset-audit", action="store_true",
                        help="Wipe audit_logs + replicas so the chain restarts clean.")
    parser.add_argument("--only", default=None,
                        help="Rebuild a single persona by key (swayam, mahak, …).")
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
    from models import enums as E

    models = {
        "User": User, "AuthCredential": AuthCredential, "Device": Device,
        "Account": Account, "Deposit": Deposit, "Loan": Loan, "Card": Card,
        "Transaction": Transaction, "BehaviouralProfile": BehaviouralProfile,
        "hash_mpin": hash_mpin,
        "enums": {
            "AccountType": E.AccountType, "CardType": E.CardType,
            "DepositType": E.DepositType, "DeviceType": E.DeviceType,
            "LoanType": E.LoanType, "TransactionChannel": E.TransactionChannel,
            "TransactionStatus": E.TransactionStatus, "TrustStatus": E.TrustStatus,
        },
    }

    now = datetime.now(timezone.utc)
    db = SessionLocal()

    try:
        if args.reset_audit:
            from models.audit import AuditLog
            from models.audit_replica import AuditReplica1, AuditReplica2, AuditReplica3
            for model in (AuditReplica1, AuditReplica2, AuditReplica3, AuditLog):
                removed = db.query(model).delete()
                print(f"  audit reset: removed {removed} rows from {model.__tablename__}")
            db.commit()
            print("✔ Audit chain wiped — it restarts cleanly on the next investment.\n")

        chosen = [p for p in PERSONAS if args.only is None or p.key == args.only]
        if not chosen:
            print(f"No persona named '{args.only}'. "
                  f"Known: {', '.join(p.key for p in PERSONAS)}")
            sys.exit(1)

        print("Seeding personas\n" + "─" * 72)
        for p in chosen:
            count = build(db, p, now, models)
            runway = float(p.primary_balance) / float(p.monthly_expenses)
            emi = sum(float(l[2]) for l in p.loans)
            dti = emi / float(p.monthly_income) if p.monthly_income else 0.0
            print(f"\n  {p.full_name}   {p.customer_id} / MPIN {MPIN}")
            print(f"    income ₹{int(p.monthly_income):,}/mo · "
                  f"expenses ₹{int(p.monthly_expenses):,}/mo · "
                  f"runway {runway:.1f} months · DTI {dti:.0%}")
            print(f"    {p.story}")
            print(f"    demo: {p.demo_hint}")
            print(f"    ({count} transactions seeded)")

        print("\n" + "─" * 72)
        print("All personas ready. Every login uses MPIN " + MPIN + ".")
        print("\nNOTE: goal-based advice (home purchase, retirement) cannot fire "
              "yet —\ngoals live in aa_data, which the mobile app does not send. "
              "The five\nstories above are the ones the engine can reach today.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
