"""
zero_day_check.py — prove the novelty detector actually discriminates
=====================================================================

    python scripts/zero_day_check.py

/health/ai tells you WHICH detector is loaded. This tells you whether it
WORKS: it scores a transaction that looks like the customer's normal
behaviour against one that looks nothing like it, and prints both
reconstruction errors and verdicts side by side.

Worth having because "the autoencoder is loaded" and "the autoencoder can
tell these apart" are different claims, and only the second one matters.
A loaded model that scores everything identically is useless.

Runs against whichever detector is active, so it is also a fair way to
compare the autoencoder with the statistical fallback.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

G = "\033[32m"; R = "\033[31m"; Y = "\033[33m"; C = "\033[36m"; B = "\033[1m"; N = "\033[0m"

now = datetime.now(timezone.utc)

# Two transactions for the same customer profile. The only thing that changes
# is how far the behaviour sits from their baseline.
NORMAL = {
    "user_id": "demo",
    "amount": 4000.0,
    "timestamp": now.replace(hour=14).isoformat(),
    "is_new_device": False,
    "is_new_recipient": False,
    "otp_time_sec": 18.0,
    "session_duration": 240.0,
    "txns_last_1h": 1,
    "txns_last_24h": 2,
    "merchant_category": "MUTUAL_FUND",
}

# Every dimension pushed at once: middle of the night, unknown device, unknown
# recipient, OTP entered impossibly fast (relay), a burst of activity, and a
# round amount 20x the usual. This is what a takeover looks like.
ANOMALOUS = {
    "user_id": "demo",
    "amount": 250000.0,
    "timestamp": now.replace(hour=3).isoformat(),
    "is_new_device": True,
    "is_new_recipient": True,
    "otp_time_sec": 1.5,
    "session_duration": 12.0,
    "txns_last_1h": 7,
    "txns_last_24h": 11,
    "merchant_category": "MUTUAL_FUND",
}


def main() -> None:
    from services.security.security_pipeline import (
        get_zero_day_detector,
        zero_day_status,
    )

    status = zero_day_status()
    print(f"{B}Zero-day detector check{N}")
    print(f"  detector : {C}{status['detector']}{N}")
    print(f"  engine   : {status['engine']}")
    print(f"  detail   : {status['detail']}")

    detector = get_zero_day_detector()
    if detector is None:
        print(f"{R}\nNo detector available — novelty detection is OFF.{N}")
        sys.exit(1)

    print()
    results = {}
    for label, txn in (("normal", NORMAL), ("anomalous", ANOMALOUS)):
        try:
            res = detector.detect(txn)
        except Exception as exc:
            print(f"{R}  {label}: detect() raised {type(exc).__name__}: {exc}{N}")
            sys.exit(1)

        results[label] = res
        st = str(res.get("status", "?"))
        colour = G if st == "NORMAL" else (Y if st == "ANOMALOUS" else R)
        err = res.get("reconstruction_error", res.get("deviation_score", "n/a"))
        pct = res.get("error_percentile", "n/a")

        print(f"  {B}{label:<10}{N} -> {colour}{st}{N}")
        print(f"      score      : {err}")
        print(f"      percentile : {pct}")
        print(f"      confidence : {res.get('confidence', 'n/a')}")

    # TWO assertions, and the first one matters more.
    #
    # An earlier version of this script only checked that the anomalous case
    # scored HIGHER than the normal one. It passed while the detector was
    # flagging literally every transaction as UNKNOWN_RISK — including an
    # ordinary SIP — because "higher" was still true. Relative ordering is not
    # enough: a detector that alarms on everything is as useless as one that
    # alarms on nothing, and in a bank it is worse, because it trains customers
    # to click through warnings.
    print("\n" + "─" * 60)
    n_status = str(results["normal"].get("status", ""))
    a_status = str(results["anomalous"].get("status", ""))

    n_err = results["normal"].get("reconstruction_error") or results["normal"].get("deviation_score") or 0
    a_err = results["anomalous"].get("reconstruction_error") or results["anomalous"].get("deviation_score") or 0

    failed = False

    # 1. Normal behaviour must read as normal.
    if n_status == "NORMAL":
        print(f"{G}✔ A routine investment is classified NORMAL — no false alarm.{N}")
    else:
        failed = True
        print(f"{R}✘ A routine ₹4,000 investment was classified {n_status}.{N}")
        print(f"  Its score ({n_err}) is above the threshold, so EVERY customer")
        print("  would be challenged on ordinary activity. Usually means the")
        print("  runtime features do not match what the model was trained on.")

    # 2. Novel behaviour must separate from it.
    if a_err > n_err and a_status != "NORMAL":
        ratio = (a_err / n_err) if n_err else float("inf")
        print(f"{G}✔ The takeover-shaped transaction scores {ratio:.1f}x higher "
              f"and is flagged {a_status}.{N}")
    else:
        failed = True
        print(f"{R}✘ The unusual transaction did not separate: {a_status} "
              f"at {a_err} vs {n_err}.{N}")

    print()
    if failed:
        print(f"{R}FAIL — the detector is not usable in this state.{N}")
        sys.exit(1)
    print(f"{G}PASS — quiet on normal activity, loud on novel activity.{N}")


if __name__ == "__main__":
    main()
