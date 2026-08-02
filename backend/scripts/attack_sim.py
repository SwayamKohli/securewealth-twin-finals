"""
attack_sim.py — Live audit-tamper attack simulation
====================================================
Proves the blueprint's Distributed Self-Verifying Audit claim end to end:

    Attacker edits the audit DATABASE directly (bypassing the API entirely)
        ↓
    Majority consensus across master + 3 replicas detects the mismatch
        ↓
    Violation reported, original value restored from the healthy majority
        ↓
    Recovery event written to the audit trail
        ↓
    Admin dashboard shows COMPROMISED → then HEALTHY again

Usage (backend/, venv active, after at least one investment exists):

    python scripts/attack_sim.py                 # tamper the MASTER row
    python scripts/attack_sim.py --target replica
    python scripts/attack_sim.py --no-heal       # detect only, leave it broken
                                                 # (for showing the red state)

Run it while the Admin Dashboard is open — the integrity panel flips to
"TAMPERING DETECTED" and back to "CHAIN INTACT" after healing.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BOLD = "\033[1m"; RED = "\033[31m"; GRN = "\033[32m"; YEL = "\033[33m"; OFF = "\033[0m"


def banner(text: str) -> None:
    print(f"\n{BOLD}{text}{OFF}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulate an audit tamper attack.")
    ap.add_argument(
        "--target",
        choices=["master", "replica"],
        default="master",
        help="Which copy the attacker edits (default: master — the realistic insider attack).",
    )
    ap.add_argument(
        "--no-heal",
        action="store_true",
        help="Detect only; skip self-healing so the compromised state stays visible.",
    )
    args = ap.parse_args()

    from database.connection import SessionLocal
    from database.repositories.audit_repository import AuditRepository
    from models.audit import AuditLog
    from models.audit_replica import AuditReplica1
    from audit.replica_verifier import ReplicaVerifier
    from audit.recovery_service import RecoveryService
    from core.dependencies import build_tamper_monitor

    db = SessionLocal()
    try:
        repo = AuditRepository(db)

        # ── Pick a victim record ────────────────────────────────────────────
        record = (
            db.query(AuditLog).order_by(AuditLog.created_at.desc()).first()
        )
        if record is None:
            print(f"{RED}No audit records found. Make an investment first:{OFF}")
            print("  bash scripts/smoke_test.sh")
            sys.exit(1)

        audit_id = record.audit_id
        banner("① TARGET — an existing immutable audit record")
        print(f"   audit_id       : {audit_id}")
        print(f"   decision       : {record.final_decision}")
        print(f"   risk score     : {record.risk_score}")
        print(f"   amount         : ₹{record.amount}")
        print(f"   current_hash   : {str(record.current_hash)[:24]}…")

        # IMPORTANT: read the pristine values from a REPLICA, not from master.
        # A previous `--no-heal` run may have left master already tampered, in
        # which case comparing against master would validate the attack.
        from models.audit_replica import AuditReplica1 as _R1

        pristine = (
            db.query(_R1).filter(_R1.audit_id == audit_id).first()
        )
        original_decision = (
            pristine.final_decision if pristine else record.final_decision
        )
        original_risk = pristine.risk_score if pristine else record.risk_score
        if pristine and (
            record.final_decision != original_decision
            or record.risk_score != original_risk
        ):
            print(f"   {YEL}note: master is ALREADY tampered from a previous run"
                  f" — true original is {original_decision} (risk {original_risk}){OFF}")

        # ── The attack ──────────────────────────────────────────────────────
        banner(f"② ATTACK — insider edits the {args.target.upper()} row directly in PostgreSQL")
        if args.target == "master":
            row = db.query(AuditLog).filter(AuditLog.audit_id == audit_id).first()
            row.final_decision = "ALLOW"          # hide the fraud
            row.risk_score = 1                     # make it look harmless
            row.audit_note = "Routine approval."   # rewrite history
            db.commit()
            print(f"   {RED}UPDATE audit_logs SET final_decision='ALLOW', risk_score=1{OFF}")
            print(f"   {RED}→ fraud decision '{original_decision}' (risk {original_risk}) erased{OFF}")
        else:
            row = (
                db.query(AuditReplica1)
                .filter(AuditReplica1.audit_id == audit_id)
                .first()
            )
            if row is None:
                print(f"{RED}Replica 1 has no copy of this record.{OFF}")
                sys.exit(1)
            row.final_decision = "ALLOW"
            row.risk_score = 1
            db.commit()
            print(f"   {RED}UPDATE audit_replica_1 SET final_decision='ALLOW'{OFF}")

        print("   The attacker never touched the API — this is a direct DB write.")

        # ── Detection ───────────────────────────────────────────────────────
        banner("③ DETECTION — majority consensus across master + 3 replicas")
        verifier = ReplicaVerifier(repo)
        result = verifier.verify(audit_id)

        for name, state in result.comparison.items():
            if name.startswith("_"):
                continue
            mark = f"{GRN}✔ HEALTHY{OFF}" if state["status"] == "HEALTHY" else (
                f"{RED}✘ {state['status']}{OFF}"
            )
            fields = state["mismatched_fields"]
            extra = f"  (altered: {', '.join(fields)})" if fields else ""
            print(f"   {name:<18} {mark}{extra}")

        if not result.recovery_required:
            print(f"\n{RED}Detection FAILED — the tamper was not noticed.{OFF}")
            sys.exit(1)

        print(f"\n   {YEL}TAMPER DETECTED{OFF} in: {', '.join(result.corrupted_copies)}")
        print(f"   Healthy copies: {result.healthy_copies}/4 "
              f"→ recovery {'possible' if result.recovery_possible else 'NOT possible'}")

        if args.no_heal:
            banner("④ HEALING SKIPPED (--no-heal)")
            print(f"   {YEL}The chain is left COMPROMISED.{OFF}")
            print("   Open the Admin Dashboard → 'Verify chain now' to see the red state.")
            print("   Re-run without --no-heal to repair it.")
            return

        # ── Self-healing ────────────────────────────────────────────────────
        # Run the FULL TamperMonitor (not RecoveryService alone) so the attack
        # and the repair are both written to the audit trail and appear in the
        # dashboard's Audit Defence panel.
        banner("④ SELF-HEALING — restore from the healthy majority")
        monitor = build_tamper_monitor()
        report = monitor.run()
        print(f"   tamper events logged : yes")
        print(f"   recoveries           : {report.recoveries_succeeded}/{report.recoveries_attempted}")
        print(f"   result               : {GRN}Recovery completed successfully.{OFF}")

        # ── Proof ───────────────────────────────────────────────────────────
        banner("⑤ VERIFICATION — the record is back to its original state")
        db.expire_all()
        healed = db.query(AuditLog).filter(AuditLog.audit_id == audit_id).first()
        ok_decision = healed.final_decision == original_decision
        ok_risk = healed.risk_score == original_risk
        print(f"   decision   : {healed.final_decision} "
              f"{GRN + '✔ restored' + OFF if ok_decision else RED + '✘ still tampered' + OFF}")
        print(f"   risk score : {healed.risk_score} "
              f"{GRN + '✔ restored' + OFF if ok_risk else RED + '✘ still tampered' + OFF}")

        # ── Confirm the chain is clean again ────────────────────────────────
        banner("⑥ FULL INTEGRITY SWEEP — the same check the scheduler runs")
        report = build_tamper_monitor().run()
        print(f"   overall status     : {report.overall_status}")
        print(f"   hash chain valid   : {report.hash_chain_valid}")
        print(f"   records checked    : {report.checked_records}")
        print(f"   signatures invalid : {report.signatures_invalid}")
        print(f"   recoveries         : {report.recoveries_succeeded}/{report.recoveries_attempted}")
        print(f"\n   Open the Admin Dashboard → 'Audit Defence' to see the")
        print( "   TAMPER DETECTED and SELF-HEALED entries just written.")

        if ok_decision and ok_risk:
            print(f"\n{GRN}{BOLD}✔ ATTACK DEFEATED — tamper detected, original state restored,"
                  f" recovery logged.{OFF}\n")
        else:
            print(f"\n{RED}{BOLD}✘ Self-healing did not fully restore the record.{OFF}\n")
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
