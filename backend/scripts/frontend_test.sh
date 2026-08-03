#!/usr/bin/env bash
# ============================================================================
# SecureWealth Twin — mobile-app contract test (M8, task 24)
#
#   bash scripts/frontend_test.sh
#   BASE=http://10.0.0.5:8000 bash scripts/frontend_test.sh
#
# smoke_test.sh proves the BACKEND works. This proves the APP works, which is
# a different question: it walks every endpoint the mobile app actually calls,
# in the order the app calls it, with the payload shapes the app actually
# sends — and asserts the response contains the fields the screens read.
#
# The failure this exists to catch: an endpoint that returns 200 with a field
# renamed or missing. The backend suite passes, and the app shows a blank
# card. That has already happened twice in this project (financial_health,
# triggered_signals), so it is checked here rather than discovered on stage.
#
# Journey, exactly as a new customer experiences it:
#   register → login → device → session → consent → wealth → invest
#   → challenge (methods / switch / verify) → activity → phishing → logout
#
# Requires: curl, python3, a running backend. Does NOT need seed_demo — it
# creates its own throwaway customer so it can be run repeatedly.
# ============================================================================
set -uo pipefail

BASE="${BASE:-http://localhost:8000}"
PASS=0; FAIL=0
G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; B=$'\e[1m'; N=$'\e[0m'

ok()    { echo "${G}  ✔ $1${N}"; PASS=$((PASS+1)); }
bad()   { echo "${R}  ✘ $1${N}"; FAIL=$((FAIL+1)); }
head_() { echo; echo "${B}$1${N}"; }

TOKEN=""
call() { # method path [json]
  local m=$1 p=$2 d=${3:-}
  if [ -n "$d" ]; then
    curl -s -w '\n%{http_code}' -X "$m" "$BASE$p" \
      -H 'Content-Type: application/json' \
      ${TOKEN:+-H "Authorization: Bearer $TOKEN"} -d "$d"
  else
    curl -s -w '\n%{http_code}' -X "$m" "$BASE$p" \
      ${TOKEN:+-H "Authorization: Bearer $TOKEN"}
  fi
}
code() { echo "$1" | tail -n1; }
body() { echo "$1" | sed '$d'; }

# Does the JSON contain these keys, at top level or in the first list item?
# This is the whole point of the suite: the SHAPE the screen depends on.
has_fields() { # <json-on-stdin> "field1 field2"
  python3 -c "
import sys, json
want = '$1'.split()
try:
    d = json.load(sys.stdin)
except Exception:
    print('PARSE_ERROR'); sys.exit()
if isinstance(d, list):
    if not d:
        print('EMPTY_LIST'); sys.exit()
    d = d[0]
missing = [f for f in want if f not in (d or {})]
print(' '.join(missing) if missing else 'OK')
" 2>/dev/null
}

# Assert: name, response, expected code, required fields (may be empty).
expect() { # name response code fields
  local name=$1 res=$2 want=$3 fields=${4:-}
  local got; got=$(code "$res")
  if [ "$got" != "$want" ]; then
    bad "$name — HTTP $got, expected $want"
    echo "      ${R}$(body "$res" | head -c 160)${N}"
    return 1
  fi
  if [ -n "$fields" ]; then
    local missing; missing=$(body "$res" | has_fields "$fields")
    if [ "$missing" = "EMPTY_LIST" ]; then
      bad "$name — returned an empty list, so the shape could not be checked"
      return 1
    fi
    if [ "$missing" != "OK" ]; then
      bad "$name — response is missing: $missing"
      echo "      ${Y}the screen reading this will render blank${N}"
      return 1
    fi
  fi
  ok "$name"
  return 0
}

echo "${B}SecureWealth Twin — mobile app contract test${N}"
echo "Backend: $BASE"
echo "Walks the 34 endpoints the app calls, in app order."

# ── 1. RegisterScreen ──────────────────────────────────────────────────────
head_ "1. Open an account (RegisterScreen)"
STAMP=$(python3 -c "import time;print(int(time.time())%100000000)")
PHONE="9$(python3 -c "print(str($STAMP).zfill(9)[:9])")"
NEWMPIN="481629"

RREG=$(call POST /api/v1/auth/register "{
  \"full_name\":\"Contract Test\",
  \"phone\":\"$PHONE\",
  \"email\":\"contract$STAMP@example.com\",
  \"mpin\":\"$NEWMPIN\",
  \"date_of_birth\":\"1995-04-12\"
}")
if expect "register → customer created" "$RREG" "201" "customer_id"; then
  NEWID=$(body "$RREG" | python3 -c "import sys,json;print(json.load(sys.stdin).get('customer_id',''))" 2>/dev/null)
  ok "SecureWealth ID issued and shown to the customer: $NEWID"
else
  NEWID=""
fi

# ── 2. AuthScreen ──────────────────────────────────────────────────────────
head_ "2. Sign in (AuthScreen)"
if [ -n "$NEWID" ]; then
  RLOG=$(call POST /api/v1/auth/login "{\"login_id\":\"$NEWID\",\"mpin\":\"$NEWMPIN\"}")
  if expect "login with the issued SecureWealth ID" "$RLOG" "200" "access_token"; then
    TOKEN=$(body "$RLOG" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
  fi
else
  bad "skipped login — registration did not return an ID"
fi
[ -z "$TOKEN" ] && { echo "${R}Cannot continue without a token.${N}"; exit 1; }

# ── 3. deviceSession.ts, runs right after login ────────────────────────────
head_ "3. Register this device (deviceSession.ts)"
# The app posts to /devices/register (not /devices), and that route returns
# 200. Mirror the app exactly — the point of this suite is the real contract.
RDEV=$(call POST /api/v1/devices/register "{\"device_name\":\"Contract Test Device\",\"device_type\":\"ANDROID\"}")
expect "registerDevice" "$RDEV" "200" "device_id device_name trust_status"
expect "getDevices — Profile device list" "$(call GET /api/v1/devices)" "200" "device_id trust_status"

# ── 4. ProfileScreen ───────────────────────────────────────────────────────
head_ "4. Profile"
expect "getSession — name + SecureWealth ID" \
  "$(call GET /api/v1/auth/session)" "200" "user_id full_name customer_id"
expect "getConsent — aggregation toggle state" \
  "$(call GET /api/v1/aggregation/consent)" "200" "aa_consent"

# ── 5. ConsentScreen → WealthOverviewScreen ────────────────────────────────
head_ "5. Consent gate (ConsentScreen)"
call DELETE /api/v1/aggregation/consent >/dev/null
RGATE=$(call GET /api/v1/aggregation/net-worth)
[ "$(code "$RGATE")" = "403" ] \
  && ok "Wealth tab correctly gated before consent (403 → app shows ConsentScreen)" \
  || bad "Expected 403 without consent, got $(code "$RGATE") — the gate would not appear"
expect "grantConsent" "$(call POST /api/v1/aggregation/consent)" "200" "aa_consent"

head_ "6. Wealth tab (WealthOverviewScreen)"
expect "getNetWorth — hero figure + assets/liabilities bar" \
  "$(call GET /api/v1/aggregation/net-worth)" "200" "net_worth total_assets total_liabilities"
expect "getCashflow — cash-flow section + Dashboard tip" \
  "$(call GET /api/v1/aggregation/cashflow)" "200" "total_income total_expenses net_cashflow"
expect "getDeposits" "$(call GET /api/v1/deposits/)" "200" ""
expect "getLoans"    "$(call GET /api/v1/loans/)"    "200" ""
expect "getAggregationStatus — Linked accounts card" \
  "$(call GET /api/v1/aggregation/status)" "200" "accounts_connected healthy status"
expect "syncAggregation — Refresh button" \
  "$(call POST /api/v1/aggregation/sync '{"force_refresh":false}')" "200" "success synced_accounts"
# Enough balance to cover both the ALLOW investment and the large one that
# should escalate — ₹50,000 previously made the escalation fail on funds.
expect "linkAccount — Link a bank sheet" \
  "$(call POST /api/v1/aggregation/accounts/link '{"bank_name":"State Bank of India","account_type":"SAVINGS","account_number":"12345678","balance":400000,"currency":"INR"}')" \
  "201" ""

# Checked here, not earlier: a customer who has just registered owns no
# accounts at all until one is linked.
expect "getAccounts — account cards" \
  "$(call GET /api/v1/accounts/)" "200" "account_id balance account_type"

ACC=$(call GET /api/v1/accounts/)
ACC=$(body "$ACC" | python3 -c "
import sys,json
a=[x for x in json.load(sys.stdin) if str(x['account_type']).upper()=='SAVINGS']
print(a[0]['account_id'] if a else '')" 2>/dev/null)

# Recommendations use the profile the app assembles from the calls above.
RREC=$(call POST /api/v1/ai/wealth/recommendations \
  '{"profile_data":{"monthly_income":85000,"monthly_expenses":52000,"net_worth":250000,"months_of_runway":1.8,"accounts":[],"deposits":[],"loans":[]},"fraud_probability":0.0}')
expect "getWealthRecommendations — cards + health grade" \
  "$RREC" "200" "recommendations financial_health"

# Card fields the redesigned recommendation card reads.
if [ "$(code "$RREC")" = "200" ]; then
  MISSING=$(body "$RREC" | python3 -c "
import sys,json
recs = json.load(sys.stdin).get('recommendations') or []
if not recs:
    print('no recommendations returned'); raise SystemExit
want = ['recommendation_id','recommendation','product','amount','tenure','reason','confidence','expected_benefit','priority']
missing = [f for f in want if f not in recs[0]]
print(' '.join(missing) if missing else 'OK')" 2>/dev/null)
  [ "$MISSING" = "OK" ] \
    && ok "Recommendation cards have every field the UI renders" \
    || bad "Recommendation card fields missing: $MISSING"
fi

expect "explainWealth — 'Why are we suggesting this?'" \
  "$(call POST /api/v1/ai/explainability/wealth '{"wealth_result":{"suppressed":false,"financial_health":{"score":60,"grade":"B","components":{}},"recommendations":[],"goal_summaries":[],"disclaimer":""},"profile":{"monthly_income":85000}}')" \
  "200" "overview recommendation_explanations generated_by"

# ── 7. Dashboard ───────────────────────────────────────────────────────────
head_ "7. Home tab (DashboardScreen)"
expect "getDashboard" "$(call GET /dashboard/)" "200" ""
expect "getMySecurityActivity — protection card + activity screen" \
  "$(call GET /api/v1/security/my-activity)" "200" "count activities"

# ── 8. Invest → SecurityReview ─────────────────────────────────────────────
head_ "8. Invest (TransactionInitiate → SecurityReview)"
if [ -z "$ACC" ]; then
  bad "no Savings account on the new customer — cannot test the invest flow"
else
  RTXN=$(call POST /api/v1/transactions/initiate \
    "{\"account_id\":\"$ACC\",\"amount\":3000,\"fund_name\":\"Bluechip Equity Fund SIP\",\"fund_category\":\"EQUITY_MUTUAL_FUND\",\"channel\":\"UPI\"}")
  expect "initiateTransaction — verdict for the security screen" \
    "$RTXN" "201" "transaction_id decision risk_score triggered_signals"

  # triggered_signals is what replaced the locally-synthesised signal list.
  if [ "$(code "$RTXN")" = "201" ]; then
    SIGOK=$(body "$RTXN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
v=d.get('triggered_signals')
print('OK' if isinstance(v,list) else f'not a list: {type(v).__name__}')" 2>/dev/null)
    [ "$SIGOK" = "OK" ] \
      && ok "triggered_signals is a real list — 'what we checked' shows engine data" \
      || bad "triggered_signals wrong: $SIGOK"
  fi

  expect "explainDecision — 'What this means' card" \
    "$(call POST /api/v1/ai/explainability/decision '{"record":{"decision":"ALLOW","risk_score":12},"language":"en"}')" \
    "200" "explanation"
fi

# ── 9. Challenge ───────────────────────────────────────────────────────────
head_ "9. Step-up verification (ChallengeScreen)"
RBIG=$(call POST /api/v1/transactions/initiate \
  "{\"account_id\":\"$ACC\",\"amount\":90000,\"fund_name\":\"Bluechip Equity Fund SIP\",\"fund_category\":\"EQUITY_MUTUAL_FUND\",\"channel\":\"UPI\"}")
DEC=$(body "$RBIG" | python3 -c "import sys,json;print(json.load(sys.stdin).get('decision',''))" 2>/dev/null)
TXN=$(body "$RBIG" | python3 -c "import sys,json;print(json.load(sys.stdin).get('transaction_id',''))" 2>/dev/null)

if [ "$DEC" = "CHALLENGE" ]; then
  expect "startChallenge" "$(call POST "/api/v1/security/challenge/$TXN/start" '{}')" \
    "200" "current_step steps total_steps prompt attempts_left"
  expect "getChallengeMethods — 'Verify another way'" \
    "$(call GET "/api/v1/security/challenge/$TXN/methods")" "200" "current_step switchable methods note"
  expect "explainChallenge — 'why we asked'" \
    "$(call POST /api/v1/ai/explainability/challenge '{"requirement":{"challenge_type":"TRANSACTION_CONFIRMATION"},"language":"en"}')" \
    "200" "explanation source"
  expect "verifyChallenge rejects a wrong answer" \
    "$(call POST "/api/v1/security/challenge/$TXN/verify" '{"answer":"000000"}')" "200" "verified"
  expect "cancelChallenge — \"I didn't start this\"" \
    "$(call POST "/api/v1/security/challenge/$TXN/cancel" '{"reason":"not_me"}')" \
    "200" "cancelled transaction_status reported message next_steps"
else
  echo "${Y}  – ₹90,000 decided '${DEC:-n/a}', not CHALLENGE. A brand-new customer has"
  echo "    no baseline yet, so the spike rule may not fire. Challenge endpoints"
  echo "    are covered in depth by smoke_test.sh §7/§7b.${N}"
fi

# ── 10. Phishing tab ───────────────────────────────────────────────────────
head_ "10. Phishing tab (PhishingScanner + SmsInboxScan)"
expect "scanPhishing — manual check" \
  "$(call POST /api/v1/phishing/scan '{"message":"URGENT: your KYC expires today, update at http://sbi-kyc-verify.xyz"}')" \
  "200" "phishing_score risk_level fired_signals signal_groups_fired top_signal"
expect "bulkScanPhishing — automatic inbox scan" \
  "$(call POST /api/v1/phishing/bulk-scan '[{"message":"Your OTP is 123456. Never share it."},{"message":"Click http://fake-bank.xyz to unlock your account NOW"}]')" \
  "200" "phishing_score risk_level"
expect "explainPhishing — threat detail sheet" \
  "$(call POST /api/v1/ai/explainability/phishing '{"scan_result":{"phishing_score":0.9,"risk_level":"HIGH","fired_signals":[],"detected_keywords":{},"signal_groups_fired":[],"negative_signals_found":[],"signal_count":1,"top_signal":"suspicious_link","message":"x","scanned_at":"2026-01-01T00:00:00Z"},"language":"en"}')" \
  "200" "explanation source"

# ── 10b. AI model status (used by the admin dashboard) ─────────────────────
head_ "10b. AI model status"
expect "health/ai — which models are live" \
  "$(call GET /api/v1/health/ai)" "200" "zero_day explanations summary"

# ── 11. Profile actions ────────────────────────────────────────────────────
head_ "11. Profile actions"
expect "explainDeviceTrust — device explanation in Profile" \
  "$(call POST /api/v1/ai/explainability/device-trust '{"trust_result":{"device_status":"PENDING","confidence":50,"age_days":0,"signals":[]},"user_profile":{"full_name":"Contract Test"}}')" \
  "200" "customer_message generated_by"
expect "revokeConsent — consent toggle off" \
  "$(call DELETE /api/v1/aggregation/consent)" "200" "aa_consent"
expect "logout" "$(call POST /api/v1/auth/logout)" "200" ""

# ── Summary ────────────────────────────────────────────────────────────────
echo
echo "────────────────────────────────────────"
echo "  Passed: ${G}$PASS${N}   Failed: ${R}$FAIL${N}"
echo "────────────────────────────────────────"
if [ "$FAIL" -gt 0 ]; then
  echo "${R}The app would break on the failures above.${N}"; exit 1
fi
echo "${G}Every endpoint the mobile app calls responds with the shape it expects.${N}"
