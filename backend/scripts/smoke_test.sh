#!/usr/bin/env bash
# ============================================================================
# SecureWealth Twin — automated backend smoke test
#
#   bash scripts/smoke_test.sh                 # against http://localhost:8000
#   BASE=http://10.0.0.5:8000 bash scripts/smoke_test.sh
#
# Runs the whole Phase-1 API journey end to end: login as the SEEDED demo
# customer, pick a real Savings account, exercise validation, run an ALLOW
# investment and a large-amount escalation, complete any challenge, then check
# the audit chain, wealth AI, multilingual explanations and phishing engine.
#
# Requires: curl, python3. Run `python scripts/seed_demo.py --reset-audit`
# first so the demo customer and fraud baseline exist.
# ============================================================================
set -uo pipefail

BASE="${BASE:-http://localhost:8000}"
LOGIN_ID="${LOGIN_ID:-SW10000001}"
MPIN="${MPIN:-123456}"
ADMIN_KEY="${ADMIN_KEY:-securewealth-admin-2026}"

PASS=0; FAIL=0
G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; B=$'\e[1m'; N=$'\e[0m'

ok()   { echo "${G}  ✔ $1${N}"; PASS=$((PASS+1)); }
bad()  { echo "${R}  ✘ $1${N}"; FAIL=$((FAIL+1)); }
head_() { echo; echo "${B}$1${N}"; }
jget() { python3 -c "import sys,json;d=json.load(sys.stdin);print(d$1 if d else '')" 2>/dev/null; }

# code+body helper: prints "<http_code>\n<body>"
call() { # method path [data] [extra_header]
  local m=$1 p=$2 d=${3:-} h=${4:-}
  if [ -n "$d" ]; then
    curl -s -w '\n%{http_code}' -X "$m" "$BASE$p" \
      -H 'Content-Type: application/json' ${h:+-H "$h"} \
      ${TOKEN:+-H "Authorization: Bearer $TOKEN"} -d "$d"
  else
    curl -s -w '\n%{http_code}' -X "$m" "$BASE$p" \
      ${h:+-H "$h"} ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
  fi
}
code() { echo "$1" | tail -n1; }
body() { echo "$1" | sed '$d'; }

TOKEN=""

echo "${B}SecureWealth Twin — smoke test against $BASE${N}"

# ── 1. Auth ────────────────────────────────────────────────────────────────
head_ "1. Authentication"
R1=$(call POST /api/v1/auth/login "{\"login_id\":\"$LOGIN_ID\",\"mpin\":\"$MPIN\"}")
if [ "$(code "$R1")" = "200" ]; then
  TOKEN=$(body "$R1" | jget "['access_token']")
  ok "Login with SecureWealth ID $LOGIN_ID"
else
  bad "Login failed ($(code "$R1")) — run: python scripts/seed_demo.py --reset-audit"
  echo "$(body "$R1")"; exit 1
fi

R2=$(call POST /api/v1/auth/login '{"login_id":"9876543210","mpin":"123456"}')
[ "$(code "$R2")" = "401" ] && ok "Phone-number login correctly rejected (401)" \
                            || bad "Phone login returned $(code "$R2"), expected 401"

# ── 2. Consent gate ────────────────────────────────────────────────────────
head_ "2. Consent-based aggregation"
call DELETE /api/v1/aggregation/consent >/dev/null
R3=$(call GET /api/v1/aggregation/net-worth)
[ "$(code "$R3")" = "403" ] && ok "Aggregation blocked without consent (403)" \
                            || bad "Expected 403 without consent, got $(code "$R3")"
call POST /api/v1/aggregation/consent >/dev/null
R4=$(call GET /api/v1/aggregation/net-worth)
[ "$(code "$R4")" = "200" ] && ok "Aggregation allowed after consent (200)" \
                            || bad "Expected 200 after consent, got $(code "$R4")"

# ── 3. Pick a real Savings account ─────────────────────────────────────────
head_ "3. Accounts"
R5=$(call GET /api/v1/accounts/)
ACC=$(body "$R5" | python3 -c "
import sys,json
a=[x for x in json.load(sys.stdin) if str(x['account_type']).upper()=='SAVINGS']
print(a[0]['account_id'] if a else '')" 2>/dev/null)
BAL0=$(body "$R5" | python3 -c "
import sys,json
a=[x for x in json.load(sys.stdin) if str(x['account_type']).upper()=='SAVINGS']
print(a[0]['balance'] if a else 0)" 2>/dev/null)
if [ -n "$ACC" ]; then ok "Savings account $ACC (balance ₹$BAL0)"
else bad "No Savings account found — seed the demo user first"; exit 1; fi

# Each run spends real balance. Once it runs low the escalation sections cannot
# fire and would quietly report nothing, so say so up front.
BALINT=$(python3 -c "print(int(float('${BAL0:-0}')))" 2>/dev/null || echo 0)
if [ "${BALINT:-0}" -lt 120000 ]; then
  echo "${Y}  ! Balance is low (₹$BALINT). Each run spends it; escalation tests need"
  echo "    headroom. Re-seed with: python scripts/seed_demo.py --reset-audit${N}"
fi

# ── 4. Investment-only validation ──────────────────────────────────────────
head_ "4. Investment-only validation"
R6=$(call POST /api/v1/transactions/initiate \
  "{\"account_id\":\"$ACC\",\"amount\":1000,\"fund_name\":\"Ravi Kumar\",\"fund_category\":\"P2P_TRANSFER\",\"channel\":\"UPI\"}")
[ "$(code "$R6")" = "422" ] && ok "Person-to-person transfer rejected (422)" \
                            || bad "P2P expected 422, got $(code "$R6")"
R7=$(call POST /api/v1/transactions/initiate \
  "{\"account_id\":\"$ACC\",\"amount\":0,\"fund_name\":\"X\",\"fund_category\":\"SIP\",\"channel\":\"UPI\"}")
[ "$(code "$R7")" = "422" ] && ok "Zero amount rejected (422)" \
                            || bad "Zero amount expected 422, got $(code "$R7")"

# ── 5. ALLOW path ──────────────────────────────────────────────────────────
head_ "5. Normal investment (expect ALLOW / WARN)"
R8=$(call POST /api/v1/transactions/initiate \
  "{\"account_id\":\"$ACC\",\"amount\":4000,\"fund_name\":\"Bluechip Equity Fund SIP\",\"fund_category\":\"EQUITY_MUTUAL_FUND\",\"channel\":\"UPI\"}")
if [ "$(code "$R8")" = "201" ]; then
  D1=$(body "$R8" | jget "['decision']"); S1=$(body "$R8" | jget "['status']")
  RS1=$(body "$R8" | jget "['risk_score']")
  ok "₹4,000 investment → decision=$D1 status=$S1 risk=$RS1"
else
  bad "₹4,000 investment failed ($(code "$R8")): $(body "$R8")"
fi

# ── 6. Escalation path ─────────────────────────────────────────────────────
head_ "6. Large investment (expect escalation)"
# Must be a large multiple of the ₹4,000 norm to trip the spike rule, but must
# also fit inside the balance — a hardcoded amount fails once the demo account
# has been spent down by earlier runs.
BIG1=$(python3 -c "print(min(95000, max(0, int(${BALINT:-0} * 0.55))))" 2>/dev/null)
BIG1F=$(python3 -c "print(f'{${BIG1:-0}:,}')" 2>/dev/null)
R9=$(call POST /api/v1/transactions/initiate \
  "{\"account_id\":\"$ACC\",\"amount\":$BIG1,\"fund_name\":\"Bluechip Equity Fund SIP\",\"fund_category\":\"EQUITY_MUTUAL_FUND\",\"channel\":\"UPI\"}")
if [ "$(code "$R9")" = "201" ]; then
  D2=$(body "$R9" | jget "['decision']"); S2=$(body "$R9" | jget "['status']")
  RS2=$(body "$R9" | jget "['risk_score']"); TXN=$(body "$R9" | jget "['transaction_id']")
  ok "₹$BIG1F investment → decision=$D2 status=$S2 risk=$RS2"
  if [ "${RS2:-0}" -ge "${RS1:-0}" ] 2>/dev/null; then
    ok "Risk escalated with amount ($RS1 → $RS2)"
  else
    echo "${Y}  ! Risk did not increase ($RS1 → $RS2) — check risk bands${N}"
  fi
  [ "$D2" = "CHALLENGE" ] || [ "$D2" = "BLOCK" ] \
    && ok "Large outlier forced step-up verification ($D2)" \
    || bad "Expected CHALLENGE/BLOCK for a 20x outlier, got $D2"
else
  bad "₹$BIG1F investment failed ($(code "$R9")): $(body "$R9" | head -c 160)"; D2=""
fi

# ── 7. Challenge flow (only when held) ─────────────────────────────────────
if [ "${D2:-}" = "CHALLENGE" ]; then
  head_ "7. Challenge verification"
  RC=$(call POST "/api/v1/security/challenge/$TXN/start" '{}')
  STEP=$(body "$RC" | jget "['current_step']"); TOT=$(body "$RC" | jget "['total_steps']")
  OTP=$(body "$RC" | jget ".get('demo_otp','')")
  [ -n "$STEP" ] && ok "Challenge started: step $STEP of $TOT" || bad "Challenge start failed"

  RW=$(call POST "/api/v1/security/challenge/$TXN/verify" '{"answer":"000000"}')
  VW=$(body "$RW" | jget ".get('verified')")
  [ "$VW" = "False" ] && ok "Wrong answer rejected safely" || bad "Wrong answer not rejected"

  # The OTP is issued once and returned with whichever response first reaches
  # the OTP step — that may be /start OR the verify response of the PREVIOUS
  # step. Track it from both, or we end up submitting an empty code.
  RS=$(call POST "/api/v1/security/challenge/$TXN/start" '{}')
  STEP=$(body "$RS" | jget "['current_step']")
  OTP=$(body "$RS" | jget ".get('demo_otp','')")
  DONE=""
  for _ in 1 2 3 4; do
    [ -z "$STEP" ] && break
    case "$STEP" in
      MPIN)              ANS="$MPIN" ;;
      OTP)               ANS="$OTP" ;;
      SECURITY_QUESTION) ANS="2003-05-15" ;;
      *)                 ANS="" ;;
    esac
    RV=$(call POST "/api/v1/security/challenge/$TXN/verify" \
        "{\"answer\":\"$ANS\",\"acknowledged\":true}")
    VOK=$(body "$RV" | jget ".get('verified')")
    FIN=$(body "$RV" | jget ".get('transaction_status','')")
    if [ -n "$FIN" ]; then
      [ "$FIN" = "SUCCESS" ] && ok "Challenge completed → investment SUCCESS" \
                             || bad "Challenge ended as $FIN"
      DONE=1
      break
    fi
    [ "$VOK" = "True" ] && ok "Step $STEP verified" \
                        || bad "Step $STEP was NOT verified: $(body "$RV" | jget ".get('message','')")"
    PREV="$STEP"
    STEP=$(body "$RV" | jget ".get('current_step','')")
    NEXTOTP=$(body "$RV" | jget ".get('demo_otp','')")
    [ -n "$NEXTOTP" ] && OTP="$NEXTOTP"
    [ "$STEP" = "$PREV" ] && bad "Challenge stuck on step $STEP" && break
  done
  [ -n "$DONE" ] || bad "Challenge never reached a final state"
else
  head_ "7. Challenge verification"
  echo "${Y}  – skipped (decision was ${D2:-n/a}, not CHALLENGE)${N}"
fi

# ── 7b. Method choice + "this wasn't me" (task 4.3b / 4.3c) ────────────────
head_ "7b. Alternative verification + customer cancellation"
# Every run permanently spends money from the demo account, so a fixed ₹95,000
# eventually exceeds the balance and this whole section silently vanished behind
# a "skipped" line. Size the investment against the CURRENT balance instead: it
# only has to be a large multiple of normal spend to trigger escalation.
BALNOW=$(call GET /api/v1/accounts/)
BALNOW=$(body "$BALNOW" | python3 -c "
import sys,json
try:
    a=[x for x in json.load(sys.stdin) if str(x['account_type']).upper()=='SAVINGS']
    print(int(float(a[0]['balance'])) if a else 0)
except Exception: print(0)" 2>/dev/null)
BIG=$(python3 -c "print(min(95000, max(0, int($BALNOW * 0.6))))" 2>/dev/null)

if [ "${BIG:-0}" -lt 40000 ]; then
  echo "${Y}  – skipped: demo balance is only ₹${BALNOW:-0}, too low to trigger an"
  echo "    escalation. Re-seed to restore it:  python scripts/seed_demo.py --reset-audit${N}"
  D3=""
else
R9B=$(call POST /api/v1/transactions/initiate \
  "{\"account_id\":\"$ACC\",\"amount\":$BIG,\"fund_name\":\"Bluechip Equity Fund SIP\",\"fund_category\":\"EQUITY_MUTUAL_FUND\",\"channel\":\"UPI\"}")
C3=$(code "$R9B")
D3=$(body "$R9B" | jget "['decision']"); TXN2=$(body "$R9B" | jget "['transaction_id']")
if [ "$C3" != "201" ]; then
  bad "Could not open a second challenge (HTTP $C3): $(body "$R9B" | head -c 160)"
  D3=""
fi
fi

if [ "${D3:-}" = "CHALLENGE" ]; then
  call POST "/api/v1/security/challenge/$TXN2/start" '{}' >/dev/null

  RMT=$(call GET "/api/v1/security/challenge/$TXN2/methods")
  NM=$(body "$RMT" | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('methods',[])))" 2>/dev/null)
  CUR=$(body "$RMT" | jget "['current_step']")
  [ "${NM:-0}" -ge 3 ] && ok "Method options offered for step $CUR ($NM listed)" \
                       || bad "Expected ≥3 method options, got ${NM:-0}"

  # BIOMETRIC must be listed but honestly unavailable — the server cannot
  # verify a handset fingerprint without key attestation.
  BIO=$(body "$RMT" | python3 -c "
import sys,json
m=[x for x in json.load(sys.stdin).get('methods',[]) if x['method']=='BIOMETRIC']
print(m[0]['available'] if m else 'MISSING')" 2>/dev/null)
  [ "$BIO" = "False" ] && ok "Biometric correctly declared unavailable (no attestation)" \
                       || bad "Biometric availability wrong: $BIO"

  # Switching must never reduce the number of remaining checks below one.
  ALT=$(body "$RMT" | python3 -c "
import sys,json
m=[x for x in json.load(sys.stdin).get('methods',[]) if x['available'] and not x['is_current']]
print(m[0]['method'] if m else '')" 2>/dev/null)
  if [ -n "$ALT" ]; then
    RSW=$(call POST "/api/v1/security/challenge/$TXN2/method" "{\"method\":\"$ALT\"}")
    NEW=$(body "$RSW" | jget "['current_step']"); NTOT=$(body "$RSW" | jget "['total_steps']")
    [ "$NEW" = "$ALT" ] && ok "Switched verification method $CUR → $NEW (now $NTOT step(s))" \
                        || bad "Method switch failed: wanted $ALT, got $NEW"
    RBAD=$(call POST "/api/v1/security/challenge/$TXN2/method" "{\"method\":\"$NEW\"}")
    [ "$(code "$RBAD")" = "400" ] && ok "Switching to the already-active method rejected" \
                                  || bad "Duplicate switch not rejected ($(code "$RBAD"))"
  else
    echo "${Y}  – no alternative method available for step $CUR${N}"
  fi

  # "This wasn't me" → held investment dropped, reported to the audit chain.
  RCX=$(call POST "/api/v1/security/challenge/$TXN2/cancel" '{"reason":"not_me"}')
  CST=$(body "$RCX" | jget "['transaction_status']"); REP=$(body "$RCX" | jget "['reported']")
  { [ "$CST" = "FAILED" ] && [ "$REP" = "True" ]; } \
    && ok "Customer cancellation stopped the investment and reported it" \
    || bad "Cancellation wrong (status=$CST reported=$REP)"

  RCX2=$(call POST "/api/v1/security/challenge/$TXN2/cancel" '{"reason":"not_me"}')
  [ "$(code "$RCX2")" = "400" ] && ok "Cancelling an already-cancelled investment rejected" \
                                || bad "Double cancellation not rejected ($(code "$RCX2"))"
elif [ -n "${D3:-}" ]; then
  bad "Second large investment decided ${D3} — expected CHALLENGE, so method"
  echo "      switching and cancellation went untested."
fi

# ── 8. Audit chain ─────────────────────────────────────────────────────────
head_ "8. Immutable audit"
RA=$(call GET /api/v1/audit/chain)
NREC=$(body "$RA" | python3 -c "import sys,json;print(len(json.load(sys.stdin)))" 2>/dev/null)
[ "${NREC:-0}" -ge 2 ] && ok "$NREC audit records written (one per investment)" \
                       || bad "Expected ≥2 audit records, found ${NREC:-0}"
RI=$(call GET /api/v1/audit/integrity)
VALID=$(body "$RI" | jget "['hash_chain_valid']"); INV=$(body "$RI" | jget "['signatures_invalid']")
[ "$VALID" = "True" ] && [ "${INV:-1}" = "0" ] && ok "Chain intact — hashes and signatures verified" \
                       || bad "Integrity check failed (valid=$VALID invalid_sigs=$INV)"

RM=$(call GET /api/v1/security/my-activity)
NACT=$(body "$RM" | jget "['count']")
[ "${NACT:-0}" -ge 1 ] && ok "Customer activity feed returns $NACT entries" \
                       || bad "my-activity returned ${NACT:-0} entries"

# ── 9. Wealth AI ───────────────────────────────────────────────────────────
head_ "9. Wealth intelligence"
PDATA='"profile_data":{"user_id":"demo","monthly_income":85000,"monthly_expenses":52000,
 "accounts":[{"account_id":"a1","account_type":"SAVINGS","balance":"250000.00","bank_name":"SBI"}],
 "deposits":[{"deposit_id":"d1","deposit_type":"FD","principal":"300000.00","interest_rate":"7.10","maturity_date":"2027-02-15"}],
 "loans":[],"goals":[]}'
RW1=$(call POST /api/v1/ai/wealth/recommendations "{$PDATA,\"fraud_probability\":0.0}")
NW=$(body "$RW1" | jget "['wealth_position']['net_worth']")
NRECS=$(body "$RW1" | jget "['recommendations'].__len__()")
[ -n "$NW" ] && ok "Net worth exposed (₹$NW) with $NRECS recommendations" || bad "Wealth API failed"
STOCKS=$(body "$RW1" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(sum(1 for r in d.get('recommendations',[]) if 'stock' in str(r.get('product','')).lower()))" 2>/dev/null)
[ "${STOCKS:-1}" = "0" ] && ok "No stock recommendations (mutual funds only)" || bad "Stock leaked into advice"

RW2=$(call POST /api/v1/ai/wealth/recommendations "{$PDATA,\"fraud_probability\":0.9}")
SUP=$(body "$RW2" | jget "['suppressed']")
[ "$SUP" = "True" ] && ok "Advice suppressed at high fraud probability" || bad "Fraud gate did not suppress"

# ── 10. Multilingual explainability ────────────────────────────────────────
head_ "10. Multilingual explanations"
for L in hi pa; do
  RX=$(call POST /api/v1/ai/explainability/decision "{\"record\":{\"decision\":\"CHALLENGE\"},\"language\":\"$L\"}")
  TXT=$(body "$RX" | jget "['explanation']")
  echo "$TXT" | grep -qP '[\x{0900}-\x{0A7F}]' 2>/dev/null \
    && ok "$L explanation returned in native script" \
    || { [ -n "$TXT" ] && ok "$L explanation returned" || bad "$L explanation missing"; }
done

# ── 11. Phishing ───────────────────────────────────────────────────────────
head_ "11. Phishing engine"
RP=$(call POST /api/v1/phishing/bulk-scan '[
 {"message":"URGENT: Your bank account will be BLOCKED today! Update KYC at http://sbi-kyc-verify.xyz"},
 {"message":"Beta, dinner at 8. Call me when you leave office."}]')
L1=$(body "$RP" | jget "[0]['risk_level']"); L2=$(body "$RP" | jget "[1]['risk_level']")
[ "$L1" = "HIGH" ] && ok "KYC scam detected as HIGH risk" || bad "Scam scored $L1, expected HIGH"
[ "$L2" = "SAFE" ] && ok "Genuine message marked SAFE" || bad "Genuine message scored $L2"

# ── 12. Admin APIs ─────────────────────────────────────────────────────────
head_ "12. Admin dashboard APIs"
SAVED=$TOKEN; TOKEN=""
RS1=$(call GET /api/v1/admin/stats "" "X-Admin-Key: $ADMIN_KEY")
[ "$(code "$RS1")" = "200" ] && ok "Admin stats reachable with key" || bad "Admin stats $(code "$RS1")"
RS2=$(call GET /api/v1/admin/stats "" "X-Admin-Key: wrong-key")
[ "$(code "$RS2")" = "401" ] && ok "Wrong admin key rejected (401)" || bad "Bad key gave $(code "$RS2")"
RS3=$(call GET "/api/v1/admin/audit?decision=ALLOW&limit=5" "" "X-Admin-Key: $ADMIN_KEY")
[ "$(code "$RS3")" = "200" ] && ok "Audit search + filters working" || bad "Audit search $(code "$RS3")"
RS4=$(call GET "/api/v1/admin/investments?limit=5" "" "X-Admin-Key: $ADMIN_KEY")
[ "$(code "$RS4")" = "200" ] && ok "Investment history working" || bad "Investments $(code "$RS4")"
TOKEN=$SAVED

# ── 13. Remaining endpoint coverage ────────────────────────────────────────
head_ "13. Endpoint coverage sweep"
cov() { # method path expected_code label
  local m=$1 p=$2 want=$3 label=$4
  local r; r=$(call "$m" "$p")
  [ "$(code "$r")" = "$want" ] && ok "$label" || bad "$label — got $(code "$r"), want $want"
}
cov GET  /api/v1/health/                 200 "Health check"
cov GET  /api/v1/health/services         200 "Service health"
cov GET  /api/v1/auth/session            200 "Session lookup"
cov GET  /api/v1/users/me                200 "User profile"
cov GET  /api/v1/devices                 200 "Device list"
cov GET  /api/v1/devices/current         200 "Current device"
cov GET  /api/v1/deposits/               200 "Deposits"
cov GET  /api/v1/loans/                  200 "Loans"
cov GET  /api/v1/cards/                  200 "Cards"
cov GET  /dashboard/                     200 "Dashboard summary"
cov GET  /dashboard/activity             200 "Dashboard activity"
cov GET  /dashboard/health               200 "Financial health"
cov GET  /api/v1/aggregation/accounts    200 "Aggregated accounts"
cov GET  /api/v1/aggregation/status      200 "Aggregation status"
cov GET  /api/v1/aggregation/cashflow    200 "Cashflow"
cov GET  /api/v1/transactions/           200 "Transaction list"
cov GET  /api/v1/audit/summary           200 "Audit summary"
cov GET  /api/v1/audit/recovery-history  200 "Recovery history"

RP=$(call POST /api/v1/ai/profile/build '{"aa_data":{"user_id":"demo","monthly_income":85000,"monthly_expenses":52000,"accounts":[],"deposits":[],"loans":[],"goals":[]}}')
[ "$(code "$RP")" = "200" ] && ok "AI profile builder" || bad "AI profile builder — $(code "$RP")"

RX=$(call POST /api/v1/ai/explainability/phishing '{"scan_result":{"risk_level":"HIGH","top_signal":"otp_request","phishing_score":0.9},"language":"en"}')
[ "$(code "$RX")" = "200" ] && ok "Phishing explainability" || bad "Phishing explainability — $(code "$RX")"

RCH=$(call POST /api/v1/ai/explainability/challenge '{"requirement":{"challenge_type":"TRANSACTION_CONFIRMATION","trigger_signal":"amount_spike"},"language":"en"}')
[ "$(code "$RCH")" = "200" ] && ok "Challenge explainability" || bad "Challenge explainability — $(code "$RCH")"

RSC=$(call POST /api/v1/phishing/scan '{"message":"Your account will be blocked. Click http://fake-bank.xyz"}')
[ "$(code "$RSC")" = "200" ] && ok "Single phishing scan" || bad "Single phishing scan — $(code "$RSC")"

RRT=$(call GET /api/v1/admin/redteam/scenarios "" "X-Admin-Key: $ADMIN_KEY")
[ "$(code "$RRT")" = "200" ] && ok "Red Team scenario catalogue" || bad "Red Team catalogue — $(code "$RRT")"

# ── Summary ────────────────────────────────────────────────────────────────
echo
echo "${B}────────────────────────────────────────${N}"
echo "${B}  Passed: ${G}$PASS${N}${B}   Failed: ${R}$FAIL${N}"
echo "${B}────────────────────────────────────────${N}"
[ "$FAIL" -eq 0 ] && echo "${G}All backend checks passed.${N}" \
                  || echo "${R}Review the failures above.${N}"
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
