#!/usr/bin/env bash
# ============================================================================
# SecureWealth Twin — Admin Dashboard verification
#
#   bash scripts/dashboard_test.sh
#   BASE=http://10.0.0.5:8000 bash scripts/dashboard_test.sh
#
# Exercises every endpoint the dashboard calls, then RUNS ALL RED TEAM
# SCENARIOS end to end and asserts each one reports DEFENDED with no failed
# step. This is the dashboard's backing contract — if this passes, the only
# thing left to check by eye is the visuals.
#
# Run the backend first:  uvicorn main:app --reload --host 0.0.0.0 --port 8000
# ============================================================================
set -uo pipefail

BASE="${BASE:-http://localhost:8000}"
KEY="${ADMIN_KEY:-securewealth-admin-2026}"

PASS=0; FAIL=0
G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; B=$'\e[1m'; C=$'\e[36m'; N=$'\e[0m'

ok()  { echo "${G}  ✔${N} $1"; PASS=$((PASS+1)); }
bad() { echo "${R}  ✘${N} $1"; FAIL=$((FAIL+1)); }
sec() { echo; echo "${B}$1${N}"; }
jq_() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)" 2>/dev/null; }

api() { curl -s -w '\n%{http_code}' "$BASE$1" -H "X-Admin-Key: $KEY"; }
codeof() { echo "$1" | tail -n1; }
bodyof() { echo "$1" | sed '$d'; }

echo "${B}Admin Dashboard verification against $BASE${N}"

# ── 1. Panels the dashboard renders ────────────────────────────────────────
sec "1. Dashboard data endpoints"
for pair in \
  "/api/v1/admin/stats|Overview stat cards" \
  "/api/v1/admin/alerts?limit=15|Live fraud alerts" \
  "/api/v1/admin/security-events|Audit Defence feed" \
  "/api/v1/audit/integrity|Chain integrity seal" \
  "/api/v1/admin/audit?limit=10&offset=0|Audit log (page 1)" \
  "/api/v1/admin/audit?limit=10&offset=10|Audit log (page 2)" \
  "/api/v1/admin/audit?decision=CHALLENGE|Audit filter by decision" \
  "/api/v1/admin/audit?min_risk=40|Audit filter by risk" \
  "/api/v1/admin/investments?limit=50|Investment history" \
  "/api/v1/admin/investments?status=SUCCESS|Investment status filter" \
  "/api/v1/admin/redteam/scenarios|Red Team catalogue" ; do
  path="${pair%%|*}"; label="${pair##*|}"
  r=$(api "$path")
  [ "$(codeof "$r")" = "200" ] && ok "$label" || bad "$label — HTTP $(codeof "$r")"
done

# ── 2. Auth on the admin surface ───────────────────────────────────────────
sec "2. Admin authentication"
r=$(curl -s -w '\n%{http_code}' "$BASE/api/v1/admin/stats" -H "X-Admin-Key: wrong")
[ "$(codeof "$r")" = "401" ] && ok "Wrong key rejected (401)" || bad "Wrong key gave $(codeof "$r")"
r=$(curl -s -w '\n%{http_code}' "$BASE/api/v1/admin/stats")
[ "$(codeof "$r")" = "401" ] && ok "Missing key rejected (401)" || bad "No key gave $(codeof "$r")"

# ── 3. Stat card shape ─────────────────────────────────────────────────────
sec "3. Overview card data"
S=$(bodyof "$(api /api/v1/admin/stats)")
for f in total_audit_records average_risk_score audits_last_24h blocked_amount total_invested_amount; do
  v=$(echo "$S" | jq_ "d.get('$f')")
  [ -n "$v" ] && ok "$f = $v" || bad "$f missing from /admin/stats"
done
for d in ALLOW WARN CHALLENGE BLOCK; do
  v=$(echo "$S" | jq_ "d['decisions'].get('$d')")
  [ -n "$v" ] && ok "decisions.$d = $v" || bad "decisions.$d missing"
done

# ── 4. Every Red Team scenario, for real ───────────────────────────────────
sec "4. Red Team scenarios (each runs a live attack)"
SC=$(bodyof "$(api /api/v1/admin/redteam/scenarios)")
IDS=$(echo "$SC" | jq_ "' '.join(x['id'] for x in d['scenarios'])")
COUNT=$(echo "$SC" | jq_ "len(d['scenarios'])")
ok "$COUNT scenarios published"

for id in $IDS; do
  echo "${C}  ▸ $id${N}"
  r=$(curl -s -X POST "$BASE/api/v1/admin/redteam/run/$id" -H "X-Admin-Key: $KEY")
  outcome=$(echo "$r" | jq_ "d.get('outcome')")
  name=$(echo "$r" | jq_ "d.get('name', '?')")
  fails=$(echo "$r" | jq_ "sum(1 for s in d.get('steps',[]) if s['status']=='FAIL')")
  steps=$(echo "$r" | jq_ "len(d.get('steps',[]))")

  # "Tamper & Leave Broken" deliberately leaves the chain compromised.
  if [ "$id" = "audit_tamper_persist" ]; then
    [ "$outcome" = "DEFENDED" ] \
      && ok "$name — detected, healing intentionally skipped ($steps steps)" \
      || bad "$name — $outcome"
    echo "${Y}    repairing the chain before continuing…${N}"
    curl -s -X POST "$BASE/api/v1/admin/redteam/run/integrity_sweep" \
      -H "X-Admin-Key: $KEY" >/dev/null
    continue
  fi

  if [ "$outcome" = "DEFENDED" ] && [ "${fails:-1}" = "0" ]; then
    ok "$name — DEFENDED ($steps steps, 0 failures)"
  else
    bad "$name — $outcome with ${fails:-?} failed step(s)"
    echo "$r" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for s in d.get('steps',[]):
    if s['status']=='FAIL': print('        ↳', s['label'],'—',s['detail'][:120])
" 2>/dev/null
  fi
done

# ── 5. Chain must end healthy ──────────────────────────────────────────────
sec "5. Post-attack integrity"
I=$(bodyof "$(api /api/v1/audit/integrity)")
valid=$(echo "$I" | jq_ "d['hash_chain_valid']")
inv=$(echo "$I" | jq_ "d['signatures_invalid']")
recs=$(echo "$I" | jq_ "d['checked_records']")
[ "$valid" = "True" ] && [ "$inv" = "0" ] \
  && ok "Chain intact after every attack — $recs records, 0 invalid signatures" \
  || bad "Chain not clean (valid=$valid invalid_sigs=$inv)"

E=$(bodyof "$(api /api/v1/admin/security-events)")
n=$(echo "$E" | jq_ "d['total']")
[ "${n:-0}" -gt 0 ] \
  && ok "Audit Defence feed has $n tamper/recovery events to display" \
  || bad "Audit Defence feed is empty — the dashboard panel will look dead"

# ── Summary ────────────────────────────────────────────────────────────────
echo
echo "${B}────────────────────────────────────────${N}"
echo "${B}  Passed: ${G}$PASS${N}${B}   Failed: ${R}$FAIL${N}"
echo "${B}────────────────────────────────────────${N}"
if [ "$FAIL" -eq 0 ]; then
  echo "${G}Dashboard backing contract fully verified.${N}"
  echo "Now check the visuals at http://localhost:3001 (hard-refresh: Cmd+Shift+R)."
else
  echo "${R}Review the failures above.${N}"
fi
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
