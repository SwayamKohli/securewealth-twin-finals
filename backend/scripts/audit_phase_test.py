"""
audit_phase_test.py — Full audit architecture validation
=========================================================
Implements the complete phase-wise audit test plan:

  Phase 1  Seed the audit database through the PRODUCTION pipeline
  Phase 2  Baseline validation (chain / record / summary / integrity / history)
  Phase 3  Controlled tampering — Tests A, B, C, D, E
  Phase 4  Cryptographic validation (current_hash / signature / previous_hash)
  Phase 5  Recovery verification
  Phase 6  Scheduler validation (automatic, unattended recovery)

Usage (backend/, venv active):

    python scripts/audit_phase_test.py              # phases 1-5
    python scripts/audit_phase_test.py --scheduler  # also phase 6 (waits)
    python scripts/audit_phase_test.py --records 20 # seed size

Every record is created via AuditService.log_security_decision() — no direct
SQL, no manual INSERT, no bypassing the audit pipeline.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from decimal import Decimal
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

B = "\033[1m"; R = "\033[31m"; G = "\033[32m"; Y = "\033[33m"; C = "\033[36m"; O = "\033[0m"

PASS = 0
FAIL = 0
SKIP = 0


def phase(title: str) -> None:
    print(f"\n{B}{'═' * 74}{O}\n{B}  {title}{O}\n{B}{'═' * 74}{O}")


def test(name: str) -> None:
    print(f"\n{C}▸ {name}{O}")


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"   {G}✔{O} {msg}")


def bad(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"   {R}✘{O} {msg}")


def info(msg: str) -> None:
    print(f"     {msg}")


def check(condition: bool, good: str, bad_msg: str) -> bool:
    ok(good) if condition else bad(bad_msg)
    return condition


# ══════════════════════════════════════════════════════════════════════════
def main() -> None:
    ap = argparse.ArgumentParser(description="Full audit architecture validation.")
    ap.add_argument("--records", type=int, default=20, help="records to seed")
    ap.add_argument("--scheduler", action="store_true",
                    help="also run Phase 6 (waits for the background scheduler)")
    ap.add_argument("--scheduler-wait", type=int, default=310,
                    help="seconds to wait for the scheduler (default 310)")
    args = ap.parse_args()

    from audit.replica_verifier import ReplicaVerifier
    from audit.signature_service import SignatureService, SignatureStatus
    from core.dependencies import build_tamper_monitor, get_signature_service
    from database.connection import SessionLocal
    from database.repositories.audit_repository import AuditRepository
    from models.audit import AuditLog
    from models.audit_replica import AuditReplica1, AuditReplica2, AuditReplica3
    from services.audit_service import AuditLogData, AuditService
    from pathlib import Path

    db = SessionLocal()
    repo = AuditRepository(db)
    sig_service = get_signature_service()
    public_key = SignatureService.load_public_key(
        Path("keys/audit_public_key.pem").read_bytes()
    )
    verifier = ReplicaVerifier(repo, signature_service=sig_service, public_key=public_key)

    audit_service = AuditService(
        audit_repo=repo,
        hash_service=__import__(
            "core.dependencies", fromlist=["get_hash_chain_service"]
        ).get_hash_chain_service(),
        signature_service=sig_service,
    )

    REPLICAS = {
        "audit_replica_1": AuditReplica1,
        "audit_replica_2": AuditReplica2,
        "audit_replica_3": AuditReplica3,
    }

    def tamper(model, audit_id, **fields):
        """Direct database write — exactly what an attacker with DB access does."""
        row = db.query(model).filter(model.audit_id == audit_id).first()
        for k, v in fields.items():
            setattr(row, k, v)
        db.commit()
        return row

    def value_of(model, audit_id, field="final_decision"):
        row = db.query(model).filter(model.audit_id == audit_id).first()
        return getattr(row, field) if row else None

    try:
        # ═══ PHASE 1 — SEED ════════════════════════════════════════════════
        phase("PHASE 1 — Seed the Audit Database (production pipeline only)")

        for model in (AuditReplica1, AuditReplica2, AuditReplica3, AuditLog):
            db.query(model).delete()
        db.commit()
        info("Cleared audit_logs + all three replica tables.")

        # audit_logs has FOREIGN KEYS to transactions / users / devices /
        # accounts, so the seed must reference rows that actually exist.
        from models.account import Account
        from models.device import Device
        from models.transaction import Transaction
        from models.user import User

        real_user = db.query(User).first()
        if real_user is None:
            print(f"{R}No customer exists. Run first:{O}")
            print("   python scripts/seed_demo.py --reset-audit")
            sys.exit(1)

        real_account = (
            db.query(Account).filter(Account.user_id == real_user.user_id).first()
        )
        real_device = (
            db.query(Device).filter(Device.user_id == real_user.user_id).first()
        )
        real_txns = [
            t.transaction_id
            for t in db.query(Transaction)
            .filter(Transaction.user_id == real_user.user_id)
            .limit(args.records)
            .all()
        ]
        info(f"Linking audit records to customer {real_user.customer_id or real_user.user_id}")
        info(f"  account : {real_account.account_id if real_account else 'none'}")
        info(f"  device  : {real_device.device_id if real_device else 'none'}")
        info(f"  txns    : {len(real_txns)} available to reference")

        DECISIONS = [("ALLOW", 12), ("ALLOW", 18), ("ALLOW", 25), ("WARN", 45),
                     ("REVIEW", 55), ("REVIEW", 67), ("CHALLENGE", 73),
                     ("BLOCK", 91), ("BLOCK", 96)]
        CHANNELS = ["UPI", "CARD", "ATM", "NET_BANKING", "MOBILE_BANKING"]
        AI_STATUS = ["NORMAL", "ANOMALOUS", "UNKNOWN_RISK"]
        rng = random.Random(7)

        for i in range(args.records):
            decision, risk = rng.choice(DECISIONS)
            challenge = decision in ("CHALLENGE", "REVIEW")
            unknown = rng.random() < 0.25
            audit_service.log_security_decision(
                AuditLogData(
                    # Real FKs — audit records must point at real entities.
                    transaction_id=real_txns[i] if i < len(real_txns) else None,
                    user_id=real_user.user_id,
                    device_id=real_device.device_id if real_device else None,
                    account_id=real_account.account_id if real_account else None,
                    event_type="TRANSACTION_SECURITY",
                    final_decision=decision, risk_score=risk,
                    amount=Decimal(str(rng.choice([500, 1200, 25000, 50000, 100000]))),
                    channel=rng.choice(CHANNELS),
                    ai_status=rng.choice(AI_STATUS),
                    ai_confidence=Decimal(str(round(rng.uniform(0.5, 0.99), 2))),
                    unknown_risk_severity="HIGH" if unknown else None,
                    unknown_risk_applied=unknown,
                    unknown_risk_decision="CHALLENGE" if unknown else None,
                    unknown_risk_reason_code="UNKNOWN_RISK_HIGH" if unknown else None,
                    challenge_required=challenge,
                    challenge_type="OTP_RECONFIRMATION" if challenge else None,
                    challenge_trigger_signal="amount_spike" if challenge else None,
                    security_signals={"seeded": True, "index": i},
                    audit_note=f"Seeded {decision} decision #{i + 1}.",
                    compliance_reference="RBI/2025-26/219",
                )
            )
        db.commit()

        counts = {
            "audit_logs": db.query(AuditLog).count(),
            "audit_replica_1": db.query(AuditReplica1).count(),
            "audit_replica_2": db.query(AuditReplica2).count(),
            "audit_replica_3": db.query(AuditReplica3).count(),
        }
        for table, n in counts.items():
            check(n == args.records, f"{table}: {n} rows",
                  f"{table}: {n} rows (expected {args.records})")

        # ═══ PHASE 2 — BASELINE ════════════════════════════════════════════
        phase("PHASE 2 — Baseline Validation (before attacking anything)")

        test("Test 1 — GET /audit/chain returns all records")
        chain = audit_service.get_audit_chain()
        check(len(chain) == args.records,
              f"Chain returned {len(chain)} records",
              f"Chain returned {len(chain)}, expected {args.records}")

        test("Test 2 — GET /audit/{id} returns one record")
        sample_id = chain[len(chain) // 2].audit_id
        one = audit_service.get_audit_record(sample_id)
        check(one is not None and one.audit_id == sample_id,
              f"Fetched record {str(sample_id)[:8]}… ({one.final_decision})",
              "Could not fetch a single record")

        test("Test 3 — GET /audit/summary")
        summary = audit_service.get_audit_summary()
        total = getattr(summary, "total_records", None) or getattr(summary, "total", None)
        info(f"summary: {summary}")
        check(total == args.records or total is None,
              f"Total records = {total}", f"Total = {total}, expected {args.records}")

        test("Test 4 — GET /audit/integrity")
        report = build_tamper_monitor().run()
        check(report.hash_chain_valid, "Hash chain valid", "Hash chain INVALID")
        check(report.signatures_invalid == 0,
              f"All {report.signatures_valid} signatures valid",
              f"{report.signatures_invalid} signature(s) invalid")
        check(report.replicas_invalid == 0,
              f"All {report.replicas_valid} replica sets consistent",
              f"{report.replicas_invalid} replica set(s) corrupted")
        check(report.overall_status == "HEALTHY",
              f"Status = {report.overall_status}",
              f"Status = {report.overall_status}, expected HEALTHY")

        test("Test 5 — GET /audit/recovery-history is empty")
        history = audit_service.get_recovery_history()
        check(len(history) == 0, "No recovery events yet (as expected)",
              f"{len(history)} recovery events already exist")

        if FAIL:
            print(f"\n{R}Baseline failed — stopping before the attack phase.{O}")
            sys.exit(1)
        print(f"\n{G}Baseline healthy. Now attacking it.{O}")

        # ═══ PHASE 3 — CONTROLLED TAMPERING ════════════════════════════════
        phase("PHASE 3 — Controlled Tampering (Tests A–E)")

        def fresh_target(offset: int = 0):
            c = audit_service.get_audit_chain()
            return c[offset].audit_id, c[offset].final_decision

        # ── Test A: master only ────────────────────────────────────────────
        test("Test A — modify audit_logs (master) only; replicas untouched")
        aid, original = fresh_target(1)
        tamper(AuditLog, aid, final_decision="BLOCK" if original != "BLOCK" else "ALLOW",
               risk_score=1)
        res = verifier.verify(aid)
        check(res.corrupted_copies == ["master"],
              f"Detected corruption in: {res.corrupted_copies}",
              f"Expected ['master'], got {res.corrupted_copies}")
        info(f"authority = {res.comparison['_authority']['status']}, "
             f"signature-valid = {res.comparison['_authority']['signature_valid_copies']}")
        rep = build_tamper_monitor().run()
        db.expire_all()
        check(value_of(AuditLog, aid) == original,
              f"Master repaired back to '{original}'",
              f"Master still reads '{value_of(AuditLog, aid)}'")
        check(rep.recoveries_succeeded >= 1, "Recovery event created",
              "No recovery event was created")

        # ── Test B: replica 2 only ─────────────────────────────────────────
        test("Test B — modify audit_replica_2 only")
        aid, original = fresh_target(2)
        tamper(AuditReplica2, aid, final_decision="BLOCK" if original != "BLOCK" else "ALLOW")
        res = verifier.verify(aid)
        check(res.corrupted_copies == ["audit_replica_2"],
              f"Detected corruption in: {res.corrupted_copies}",
              f"Expected ['audit_replica_2'], got {res.corrupted_copies}")
        build_tamper_monitor().run()
        db.expire_all()
        check(value_of(AuditReplica2, aid) == original,
              f"Replica 2 repaired back to '{original}'",
              f"Replica 2 still reads '{value_of(AuditReplica2, aid)}'")

        # ── Test C: replica 1 + replica 2 ──────────────────────────────────
        test("Test C — modify replica 1 AND replica 2 (majority = master + replica 3)")
        aid, original = fresh_target(3)
        forged = "BLOCK" if original != "BLOCK" else "ALLOW"
        tamper(AuditReplica1, aid, final_decision=forged)
        tamper(AuditReplica2, aid, final_decision=forged)
        res = verifier.verify(aid)
        check(set(res.corrupted_copies) == {"audit_replica_1", "audit_replica_2"},
              f"Both corrupted replicas detected: {sorted(res.corrupted_copies)}",
              f"Expected the two replicas, got {res.corrupted_copies}")
        check(res.recovery_possible, "Recovery possible (majority intact)",
              "Recovery reported impossible")
        build_tamper_monitor().run()
        db.expire_all()
        check(value_of(AuditReplica1, aid) == original
              and value_of(AuditReplica2, aid) == original,
              f"Both replicas restored to '{original}'",
              "One or both replicas were not restored")

        # ── Test D: master + replica1 + replica2 (3 of 4 forged) ───────────
        test("Test D — modify master + replica 1 + replica 2 (only replica 3 clean)")
        aid, original = fresh_target(4)
        forged = "BLOCK" if original != "BLOCK" else "ALLOW"
        tamper(AuditLog, aid, final_decision=forged, risk_score=1)
        tamper(AuditReplica1, aid, final_decision=forged, risk_score=1)
        tamper(AuditReplica2, aid, final_decision=forged, risk_score=1)
        res = verifier.verify(aid)
        auth = res.comparison["_authority"]
        info(f"authority = {auth['status']}, "
             f"signature-valid = {auth['signature_valid_copies']}, "
             f"content-majority held by = {auth['majority_holders']}")
        # A pure head-count would hand victory to the 3 forged copies.
        # Cryptographic authority must override that.
        check(auth["status"] == "cryptographic_signature",
              "Cryptographic authority used (head-count overridden)",
              "Fell back to head-count — the forged majority would win!")
        check(set(res.corrupted_copies) == {"master", "audit_replica_1", "audit_replica_2"},
              f"All three forged copies detected: {sorted(res.corrupted_copies)}",
              f"Expected the three forged copies, got {sorted(res.corrupted_copies)}")
        check(res.recovery_possible,
              "Recovery possible from the one signature-verified copy",
              "Recovery impossible — the forged majority won")
        build_tamper_monitor().run()
        db.expire_all()
        check(value_of(AuditLog, aid) == original,
              f"Master restored to '{original}' from the single genuine copy",
              f"Master still reads '{value_of(AuditLog, aid)}'")

        # ── Test E: delete a replica row ───────────────────────────────────
        test("Test E — DELETE the replica 2 row (replication lag, not corruption)")
        aid, original = fresh_target(5)
        db.query(AuditReplica2).filter(AuditReplica2.audit_id == aid).delete()
        db.commit()
        res = verifier.verify(aid)
        check("audit_replica_2" in res.replicas_behind,
              "Classified as REPLICA_BEHIND",
              f"Not marked behind: behind={res.replicas_behind}")
        check("audit_replica_2" not in res.corrupted_copies,
              "NOT misclassified as CORRUPTED",
              "Wrongly flagged as CORRUPTED")

        # ═══ PHASE 4 — CRYPTOGRAPHIC VALIDATION ════════════════════════════
        phase("PHASE 4 — Cryptographic Validation")

        test("Change current_hash → hash verification must fail")
        aid, _ = fresh_target(6)
        rec = db.query(AuditLog).filter(AuditLog.audit_id == aid).first()
        good_hash, good_sig, good_prev = rec.current_hash, rec.digital_signature, rec.previous_hash
        tamper(AuditLog, aid, current_hash="deadbeef" * 8)
        rep = build_tamper_monitor().run()
        check(not rep.hash_chain_valid or rep.signatures_invalid > 0,
              "Tampered hash detected by the integrity sweep",
              "Altered current_hash went unnoticed")
        tamper(AuditLog, aid, current_hash=good_hash)

        test("Change digital_signature → signature verification must fail")
        rec = db.query(AuditLog).filter(AuditLog.audit_id == aid).first()
        record_dict = audit_service._record_to_dict(rec)
        status = sig_service.verify_signature(
            audit_record=record_dict, signature_b64=rec.digital_signature,
            public_key=public_key)
        check(status == SignatureStatus.VALID, "Baseline signature verifies",
              "Baseline signature already invalid")
        bogus = ("A" * 86) + "=="
        status_bad = sig_service.verify_signature(
            audit_record=record_dict, signature_b64=bogus, public_key=public_key)
        check(status_bad == SignatureStatus.INVALID,
              "Forged signature rejected",
              "Forged signature was accepted!")

        test("Change previous_hash → the whole chain must be reported invalid")
        tamper(AuditLog, aid, previous_hash="0" * 64)
        rep = build_tamper_monitor().run()
        check(not rep.hash_chain_valid,
              "Chain reported INVALID after breaking a previous_hash link",
              "Chain still reported valid despite a broken link")
        tamper(AuditLog, aid, previous_hash=good_prev, digital_signature=good_sig)
        build_tamper_monitor().run()

        # ═══ PHASE 5 — RECOVERY VERIFICATION ═══════════════════════════════
        phase("PHASE 5 — Recovery Verification")

        history = audit_service.get_recovery_history()
        check(len(history) > 0,
              f"{len(history)} recovery events recorded",
              "No recovery events were written")
        if history:
            h = history[0]
            info(f"latest: {h.audit_note}")
            check(h.event_type == "RECOVERY_EVENT" and h.final_decision == "RECOVERED",
                  "Recovery event has the correct type and outcome",
                  f"Unexpected event shape: {h.event_type}/{h.final_decision}")

        test("Before → attack → after, on a single record")
        aid, before = fresh_target(7)
        info(f"before attack   : {before}")
        forged = "BLOCK" if before != "BLOCK" else "ALLOW"
        tamper(AuditLog, aid, final_decision=forged)
        info(f"after attack    : {value_of(AuditLog, aid)}")
        build_tamper_monitor().run()
        db.expire_all()
        after = value_of(AuditLog, aid)
        info(f"after recovery  : {after}")
        check(after == before, "Value restored exactly", f"Restored to '{after}', expected '{before}'")

        test("Final integrity sweep")
        rep = build_tamper_monitor().run()
        check(rep.overall_status == "HEALTHY" and rep.hash_chain_valid,
              f"Chain {rep.overall_status} — {rep.checked_records} records verified",
              f"Chain {rep.overall_status} after all attacks")

        # ═══ PHASE 6 — SCHEDULER ═══════════════════════════════════════════
        phase("PHASE 6 — Scheduler Validation (unattended recovery)")
        if not args.scheduler:
            global SKIP
            SKIP += 1
            print(f"   {Y}⏭ Skipped. Re-run with --scheduler to test automatic recovery.{O}")
            info("It tampers a record, waits for the background scheduler (no manual")
            info("integrity call), and confirms the system healed itself.")
        else:
            aid, before = fresh_target(8)
            forged = "BLOCK" if before != "BLOCK" else "ALLOW"
            tamper(AuditLog, aid, final_decision=forged)
            info(f"Tampered {str(aid)[:8]}… : {before} → {forged}")
            info(f"Waiting {args.scheduler_wait}s for the scheduler "
                 "(the API is NOT being called)…")
            before_events = len(audit_service.get_recovery_history())
            for remaining in range(args.scheduler_wait, 0, -10):
                time.sleep(10)
                db.expire_all()
                if value_of(AuditLog, aid) == before:
                    break
                print(f"     …{remaining}s remaining", end="\r")
            db.expire_all()
            healed = value_of(AuditLog, aid) == before
            check(healed, "Scheduler repaired the record with no human action",
                  "Scheduler did not repair the record in time")
            check(len(audit_service.get_recovery_history()) > before_events,
                  "New recovery event written by the scheduler",
                  "No new recovery event appeared")

    finally:
        db.close()

    # ═══ SUMMARY ═══════════════════════════════════════════════════════════
    print(f"\n{B}{'═' * 74}{O}")
    print(f"{B}  Passed: {G}{PASS}{O}{B}   Failed: {R}{FAIL}{O}{B}   Skipped: {Y}{SKIP}{O}")
    print(f"{B}{'═' * 74}{O}")
    if FAIL == 0:
        print(f"{G}The audit architecture behaves exactly as designed.{O}\n")
    else:
        print(f"{R}Review the failures above.{O}\n")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
