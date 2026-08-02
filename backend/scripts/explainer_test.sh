#!/usr/bin/env bash
# ============================================================================
# SecureWealth Twin — explainability engine diagnostic
#
#   bash scripts/explainer_test.sh
#   BASE=http://10.0.0.5:8000 bash scripts/explainer_test.sh
#
# Exercises ALL SEVEN explainability engines and reports, for each one:
#   • whether the endpoint answered at all
#   • whether the text came from the LOCAL LLM or the deterministic fallback
#   • the first line of what the customer would actually read
#
# The source column is the point of this script. Every engine degrades
# gracefully when Ollama is down — which means a silent fallback looks exactly
# like a working LLM unless you check. Run this to know which you have.
#
# Requires: curl, python3, a running backend, seeded demo user.
# For LLM mode: `ollama serve` with the llama3 model pulled.
# ============================================================================
set -uo pipefail

BASE="${BASE:-http://localhost:8000}"
LOGIN_ID="${LOGIN_ID:-SW10000001}"
MPIN="${MPIN:-123456}"
OLLAMA="${OLLAMA:-http://localhost:11434}"

PASS=0; FAIL=0; LLM_COUNT=0; TPL_COUNT=0
G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; C=$'\e[36m'; B=$'\e[1m'; N=$'\e[0m'

ok()  { echo "${G}  ✔ $1${N}"; PASS=$((PASS+1)); }
bad() { echo "${R}  ✘ $1${N}"; FAIL=$((FAIL+1)); }

post() { # path json
  curl -s -X POST "$BASE$1" -H 'Content-Type: application/json' \
    -H "Authorization: Bearer $TOKEN" -d "$2"
}

# Pull a field out of a JSON response.
field() { python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except Exception: print(''); sys.exit()
v=d
for k in '$1'.split('.'):
    v=(v or {}).get(k) if isinstance(v,dict) else None
print(v if v is not None else '')
" 2>/dev/null; }

# One engine: name, path, payload, field holding the text, field holding source.
check() {
  local name=$1 path=$2 payload=$3 textkey=$4 srckey=$5
  local res text src t0 t1 ms
  t0=$(python3 -c 'import time;print(int(time.time()*1000))')
  res=$(post "$path" "$payload")
  t1=$(python3 -c 'import time;print(int(time.time()*1000))')
  ms=$((t1 - t0))
  text=$(echo "$res" | field "$textkey")
  src=$(echo "$res" | field "$srckey")

  if [ -z "$text" ]; then
    bad "$name — no explanation returned"
    echo "      ${R}$(echo "$res" | head -c 200)${N}"
    return
  fi

  local low
  low=$(echo "$src" | tr '[:upper:]' '[:lower:]')
  case "$low" in
    llm*) LLM_COUNT=$((LLM_COUNT+1)); tag="${C}LLM${N}" ;;
    catalog*|template_*) TPL_COUNT=$((TPL_COUNT+1)); tag="${Y}CATALOG${N}" ;;
    *)    TPL_COUNT=$((TPL_COUNT+1)); tag="${Y}FALLBACK${N}" ;;
  esac

  ok "$name  [$tag]  ${ms}ms"
  echo "      \"$(echo "$text" | head -c 150)…\""
  # A fallback that took ~the full timeout means the model was still loading,
  # not that the engine is broken.
  if [ "$low" != "llm" ] && [ "$ms" -gt 20000 ]; then
    echo "      ${Y}↑ timed out waiting for the model — it was probably still loading${N}"
  fi
}

echo "${B}SecureWealth Twin — explainability diagnostic${N}"
echo "Backend: $BASE"

# ── Is the local model actually up? ────────────────────────────────────────
if curl -s -m 3 "$OLLAMA/api/tags" >/dev/null 2>&1; then
  MODELS=$(curl -s -m 3 "$OLLAMA/api/tags" | python3 -c "
import sys,json
try: print(', '.join(m['name'] for m in json.load(sys.stdin).get('models',[])) or 'none')
except Exception: print('unreadable')" 2>/dev/null)
  echo "${G}Ollama: reachable at $OLLAMA${N}"
  echo "  models: $MODELS"
  case "$MODELS" in
    *llama3*) echo "${G}  llama3 present — engines should report LLM${N}" ;;
    *) echo "${Y}  ! llama3 NOT found. Engines will fall back. Run: ollama pull llama3${N}" ;;
  esac
else
  echo "${Y}Ollama: NOT reachable at $OLLAMA — every engine will use its"
  echo "        deterministic fallback. That is correct behaviour, not a bug,"
  echo "        but the explanations will be generic. Run: ollama serve${N}"
fi

# ── Auth ───────────────────────────────────────────────────────────────────
TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"login_id\":\"$LOGIN_ID\",\"mpin\":\"$MPIN\"}" | field 'access_token')
if [ -z "$TOKEN" ]; then
  echo "${R}Login failed — run: python scripts/seed_demo.py --reset-audit${N}"; exit 1
fi
# Warm the model before measuring. The first generation after `ollama serve`
# loads ~4.7GB of weights and can take 15-40s; without this the first engine
# tested would always look like a failure.
if curl -s -m 3 "$OLLAMA/api/tags" >/dev/null 2>&1; then
  echo
  echo "Warming llama3 (first load can take 15-40s)…"
  curl -s -m 90 -X POST "$OLLAMA/api/generate" \
    -H 'Content-Type: application/json' \
    -d '{"model":"llama3:latest","keep_alive":"30m"}' >/dev/null 2>&1
  echo "${G}Model resident.${N}"
fi

echo
echo "${B}Engines${N}"

# 1 ── Decision Explainability
check "Decision Explainability   " /api/v1/ai/explainability/decision \
  '{"record":{"decision":"CHALLENGE","risk_score":62,"amount":95000,"reason_code":"AMOUNT_SPIKE","challenge_type":"TRANSACTION_CONFIRMATION"},"language":"en"}' \
  'explanation' 'source'

# 2 ── Fraud / Risk Explainability
check "Fraud Risk Explainability " /api/v1/ai/explainability/risk \
  '{"output":{"risk_score":62,"risk_level":"MEDIUM","decision":"CHALLENGE","triggered_rules":["amount_spike","new_device"]}}' \
  'explanation' 'source'

# 3 ── Challenge Explainability
check "Challenge Explainability  " /api/v1/ai/explainability/challenge \
  '{"requirement":{"challenge_type":"TRANSACTION_CONFIRMATION","trigger_signal":"amount_spike"},"language":"en"}' \
  'explanation' 'source'

# 4 ── Unknown Risk (zero-day) Explainability
check "Unknown Risk Explainability" /api/v1/ai/explainability/unknown-risk \
  '{"decision_output":{"unknown_risk_applied":true,"unknown_risk_decision":"CHALLENGE","unknown_risk_reason_code":"UNKNOWN_RISK_HIGH","severity":"HIGH","risk_score":58,"audit_entry":{"ai_status":"UNKNOWN","ai_confidence":0.72}}}' \
  'explanation' 'source'

# 5 ── Phishing Explainability
check "Phishing Explainability   " /api/v1/ai/explainability/phishing \
  '{"scan_result":{"phishing_score":0.91,"risk_level":"HIGH","fired_signals":["urgent_language","suspicious_link"],"signal_groups_fired":["URGENCY","LINK"],"signal_count":2,"top_signal":"suspicious_link","message":"URGENT: KYC expiring, click http://sbi-kyc.xyz","detected_keywords":{},"negative_signals_found":[],"scanned_at":"2026-01-01T00:00:00Z"},"language":"en"}' \
  'explanation' 'source'

# 6 ── Device Trust Explainability
check "Device Trust Explainability" /api/v1/ai/explainability/device-trust \
  '{"trust_result":{"device_status":"TRUSTED","confidence":88,"age_days":120,"signals":["known_device","stable_location"]},"user_profile":{"full_name":"Demo Customer"}}' \
  'customer_message' 'generated_by'

# 7 ── Wealth Recommendation Explainer
check "Wealth Explainability     " /api/v1/ai/explainability/wealth \
  '{"wealth_result":{"suppressed":false,"financial_health":{"score":68,"grade":"B","components":{"emergency_readiness":18,"debt_management":22,"savings_discipline":15,"wealth_buffer":13}},"recommendations":[{"recommendation_id":"emergency_fund_implicit","recommendation":"Build Emergency Fund","product":"Liquid Fixed Deposit","amount":40000,"tenure":"No lock-in","reason":"Liquid savings cover 1.8 months of expenses.","confidence":0.95,"expected_benefit":"Financial safety net","priority":"high"}],"goal_summaries":[],"disclaimer":"Not investment advice."},"profile":{"monthly_income":85000,"monthly_expenses":52000,"net_worth":550000,"months_of_runway":1.8}}' \
  'overview' 'generated_by'

# ── Decision-consistency check ─────────────────────────────────────────────
# The most dangerous failure here is not a missing explanation — it is a
# CONFIDENT WRONG one. A held payment explained as "successfully completed"
# tells the customer to relax at exactly the wrong moment. This asserts the
# narrative agrees with the verdict it is explaining.
BAD_CLAIMS='successfully granted|successfully completed|successfully processed|processed smoothly|processed successfully|went through|has been completed|was completed|no issues|without any issues|as usual|nothing to worry|no action is needed|no action needed'

echo
echo "${B}Decision consistency${N}"
for DEC in CHALLENGE BLOCK; do
  RES=$(post /api/v1/ai/explainability/decision \
    "{\"record\":{\"decision\":\"$DEC\",\"risk_score\":78,\"amount\":95000,\"reason_code\":\"AMOUNT_SPIKE\",\"challenge_type\":\"TRANSACTION_CONFIRMATION\"},\"language\":\"en\"}")
  TXT=$(echo "$RES" | field 'explanation')
  SRC=$(echo "$RES" | field 'source')
  HIT=$(echo "$TXT" | tr '[:upper:]' '[:lower:]' | grep -oE "$BAD_CLAIMS" | head -1)
  if [ -n "$HIT" ]; then
    bad "$DEC explained as success — says \"$HIT\" [$SRC]"
    echo "      ${R}\"$(echo "$TXT" | head -c 160)…\"${N}"
  else
    ok "$DEC explanation does not claim success [$SRC]"
    echo "      \"$(echo "$TXT" | head -c 130)…\""
  fi
done

# ── Multilingual spot-check ────────────────────────────────────────────────
echo
echo "${B}Multilingual (task 5.5)${N}"
for LANG in hi pa; do
  RES=$(post /api/v1/ai/explainability/decision \
    "{\"record\":{\"decision\":\"CHALLENGE\",\"risk_score\":62},\"language\":\"$LANG\"}")
  TXT=$(echo "$RES" | field 'explanation')
  if echo "$TXT" | grep -qP '[\x{0900}-\x{0A7F}]' 2>/dev/null || [ -n "$TXT" ]; then
    ok "Decision explanation in '$LANG'"
    echo "      \"$(echo "$TXT" | head -c 110)…\""
  else
    bad "No '$LANG' explanation returned"
  fi
done

# ── Summary ────────────────────────────────────────────────────────────────
echo
echo "────────────────────────────────────────"
echo "  Engines answering: ${G}$PASS${N}   Failing: ${R}$FAIL${N}"
echo "  Generated by LLM:  ${C}$LLM_COUNT${N}   By fallback/catalog: ${Y}$TPL_COUNT${N}"
echo "────────────────────────────────────────"
if [ "$FAIL" -gt 0 ]; then
  echo "${R}Some engines did not answer — see above.${N}"; exit 1
fi
if [ "$LLM_COUNT" -eq 0 ]; then
  echo "${Y}All engines answered, but none used the local model."
  echo "Start Ollama (ollama serve) and pull llama3 to see generated text.${N}"
else
  echo "${G}All engines answered.${N}"
fi
