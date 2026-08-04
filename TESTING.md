# SecureWealth Twin — Full Test Plan

Work through the phases in order. Each test says **what to run**, **what you
should see**, and what it proves. Record failures with the exact error text.

Legend: ✅ pass · ❌ fail (note the error) · ⏭ skipped

---

## Phase 0 — Environment Setup

```bash
# ── Terminal 1: backend ──
cd backend
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head              # applies 2 new migrations (consent, customer_id)
python scripts/seed_demo.py --reset-audit

uvicorn main:app --reload
```

**Expect on startup:**
- `SecurityPipeline: Fraud ML engine loaded.`
- `SecurityPipeline: Zero-Day detector unavailable (...)` ← expected, weights file absent
- **NO** `Chain broken at audit_id=...` (the reset fixed it)
- Seed prints login `SW10000001 / 123456`

```bash
# ── Terminal 2: admin dashboard ──
cd admin-dashboard && python -m http.server 3001      # open http://localhost:3001

# ── Terminal 3: mobile app ──
cd frontend
npm install
# EDIT src/api/config.ts → API_BASE_URL = 'http://<your-LAN-IP>:8000'
npx expo start
```

☐ 0.1 Backend starts with no traceback
☐ 0.2 `alembic upgrade head` completes (no duplicate-column errors)
☐ 0.3 Seed script prints the demo summary
☐ 0.4 `http://127.0.0.1:8000/docs` loads
☐ 0.5 Expo bundles with no red screen

---

## Phase 1 — Backend API Tests (automated)

**Run the whole backend journey with one command:**

```bash
cd backend
bash scripts/smoke_test.sh
```

It logs in as the **seeded** demo customer, finds a real Savings account,
and checks: SecureWealth-ID login, phone login rejection, the consent gate,
P2P/zero-amount rejection, an ALLOW investment, a large-amount escalation,
the full challenge flow, audit chain + integrity, the customer activity feed,
wealth AI (net worth, MF-only, fraud gate), Hindi/Punjabi explanations,
the phishing engine, and all admin APIs including the wrong-key check.

It prints a pass/fail line per check and a summary. Against a different host:

```bash
BASE=http://10.209.250.173:8000 bash scripts/smoke_test.sh
```

### ✅ Result — 53/53 passed (verified)

All 13 sections green, including the full challenge flow and the 23-endpoint
coverage sweep. Backend validation is complete.

> ⚠️ **Do not test with a freshly registered user.** A new registration has no
> accounts, so every investment test will fail with an empty `account_id`.
> Always use the seeded customer `SW10000001 / 123456`.

<details>
<summary>Manual curl equivalents (only if you want to poke individual endpoints)</summary>

```bash
BASE=http://localhost:8000

# login as the SEEDED customer (not a new registration)
TOKEN=$(curl -s -X POST $BASE/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login_id":"SW10000001","mpin":"123456"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# grab a REAL savings account id (Swagger's placeholder UUID will 404)
ACC=$(curl -s $BASE/api/v1/accounts/ -H "Authorization: Bearer $TOKEN" | python3 -c '
import sys,json
print([a for a in json.load(sys.stdin) if a["account_type"].upper()=="SAVINGS"][0]["account_id"])')

# normal investment → expect ALLOW
curl -s -X POST $BASE/api/v1/transactions/initiate \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"account_id\":\"$ACC\",\"amount\":4000,\"fund_name\":\"Bluechip Equity Fund SIP\",\"fund_category\":\"EQUITY_MUTUAL_FUND\",\"channel\":\"UPI\"}"

# large investment → expect escalation; capture the id for the challenge flow
TXN=$(curl -s -X POST $BASE/api/v1/transactions/initiate \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"account_id\":\"$ACC\",\"amount\":95000,\"fund_name\":\"Bluechip Equity Fund SIP\",\"fund_category\":\"EQUITY_MUTUAL_FUND\",\"channel\":\"UPI\"}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["transaction_id"])')

curl -s -X POST $BASE/api/v1/security/challenge/$TXN/start -H "Authorization: Bearer $TOKEN"
curl -s $BASE/api/v1/audit/integrity -H "Authorization: Bearer $TOKEN"
```

Shell notes: use `TOKEN="..."` with **no spaces** around `=`, and don't paste
the `# comment` lines into zsh — it treats them as commands.

</details>

## Phase 1B — Audit Tamper Attack & Self-Healing (the USP)

This is the blueprint's core claim. Prove it in front of the judges.

**Keep the Admin Dashboard open on the Overview tab**, then:

```bash
cd backend

# 1. Attack the MASTER audit row directly in PostgreSQL (bypasses the API)
python scripts/attack_sim.py

# 2. Attack a replica instead
python scripts/attack_sim.py --target replica

# 3. Detect but DON'T heal — leaves the chain visibly compromised
python scripts/attack_sim.py --no-heal
#    → dashboard: "Verify chain now" shows ⚠ TAMPERING DETECTED
#    → then run `python scripts/attack_sim.py` to repair it
```

The script prints six stages: target record → attack → detection →
self-healing → verification → full integrity sweep.

☐ 1B.1 Master attack: `corrupted copies: ['master']` — the three untouched
       replicas **out-vote** the tampered master
☐ 1B.2 Original decision and risk score are restored exactly
☐ 1B.3 Replica attack: only that replica is flagged, master untouched
☐ 1B.4 `--no-heal` leaves the dashboard integrity seal RED
☐ 1B.5 Running the attack again repairs it → seal returns GREEN
☐ 1B.6 Dashboard **Audit Defence** panel lists the TAMPER / SELF-HEALED events

**Why this matters:** an insider editing `audit_logs` to hide a fraud is the
realistic attack. Because all four copies vote as equals, the attacker would
have to alter master *and* at least two replicas in the same instant to win.

---

## Phase 1A — Audit Architecture Deep Validation (Mahak's phase plan)

Implements the full phase-wise audit test plan — Tests A through E, plus
cryptographic and recovery validation.

```bash
cd backend
python scripts/audit_phase_test.py                 # phases 1–5 (~30s)
python scripts/audit_phase_test.py --scheduler     # also phase 6 (waits ~5 min)
```

> This **wipes and re-seeds the audit tables** through the production pipeline
> (`AuditService.log_security_decision`) — no direct SQL, no manual INSERT.
> Re-run `python scripts/seed_demo.py --reset-audit` afterwards if you want the
> customer demo data back.

| Phase | What it proves |
|---|---|
| 1 Seed | 20 records land in `audit_logs` + all 3 replicas via the real pipeline |
| 2 Baseline | chain / record / summary / integrity / recovery-history all clean |
| 3 Test A | master tampered → detected → repaired |
| 3 Test B | replica 2 tampered → detected → repaired |
| 3 Test C | replicas 1+2 tampered → majority (master+replica 3) wins → both repaired |
| 3 **Test D** | **master + replicas 1+2 forged (3 of 4!) → cryptographic signature overrides the forged majority → restored from the one genuine copy** |
| 3 Test E | replica row deleted → `REPLICA_BEHIND`, not `CORRUPTED` |
| 4 Crypto | altered `current_hash`, forged signature, broken `previous_hash` all rejected |
| 5 Recovery | recovery events written; before → attack → after values verified |
| 6 Scheduler | unattended repair with no API call (opt-in, waits ~5 min) |

### ✅ Result — 34/34 passed (verified)

```
Phase 1  20 records → audit_logs + all 3 replicas
Phase 2  chain 20 · record fetch · summary · integrity HEALTHY · history empty
Phase 3  A master ✔  B replica ✔  C two replicas ✔  D 3-of-4 forged ✔  E behind ✔
Phase 4  current_hash ✔  forged signature ✔  previous_hash ✔
Phase 5  4 recovery events · ALLOW → BLOCK → ALLOW restored · chain HEALTHY
Phase 6  scheduler repaired a tampered record unattended + logged it ✔  (36/36)
```

**Security assumption to state if asked:** this holds as long as the Ed25519
**private key is not compromised**. The key lives outside the database
(`keys/audit_private_key.pem`), so an attacker with full database access still
cannot forge a valid signature — which is exactly why Test D is survivable.

**Test D is the one to show judges.** A pure majority vote loses if an attacker
edits 3 of the 4 copies. Because every record is Ed25519-signed with a key the
attacker doesn't hold, any altered copy fails verification — so one genuine copy
outranks any number of agreeing forgeries.

---

## Phase 1C — Red Team Console (in the Admin Dashboard)

Everything from Phase 1B is now clickable — no terminal needed.

Open **http://localhost:3001 → Red Team tab**. Nine scenarios, each runs a
REAL attack and returns a step-by-step timeline.

☐ 1C.1 **Account Takeover — Large Transfer** → CHALLENGE/BLOCK, no money moves
☐ 1C.2 **Rapid Drain Attempt** → later attempts escalate on velocity
☐ 1C.3 **Zero-Day / Unknown Pattern** → classified ANOMALOUS or UNKNOWN_RISK
☐ 1C.4 **Insider Audit Tampering** → master out-voted, restored, evidence written
☐ 1C.5 **Replica Corruption** → replica out-voted and repaired
☐ 1C.6 **Tamper & Leave Broken** → integrity panel goes RED
☐ 1C.7 **Full Integrity Sweep** → repairs it, panel returns GREEN
☐ 1C.8 **Phishing Campaign** → 4 scams caught, genuine message untouched
☐ 1C.9 **Credential Brute Force** → all guessed MPINs rejected
☐ 1C.10 Each card shows **ATTACK DEFENDED** in green with a timeline
☐ 1C.11 Overview stats + Audit Defence update straight after a run

> Demo tip: run scenarios from the Red Team tab while the Overview tab is open
> in a second window — the judges see the attack and the response side by side.

---

## Phase 2 — Admin Dashboard

### 2A — Automated backing-contract check

```bash
cd backend
bash scripts/dashboard_test.sh
```

Exercises every endpoint the dashboard calls (all panels, filters, both audit
pages, admin auth), then **runs all 10 Red Team scenarios for real** and asserts
each reports DEFENDED with zero failed steps, finishing with a chain-integrity
check. If this passes, only the visuals remain to be eyeballed.

> It leaves the chain healthy: after "Tamper & Leave Broken" it automatically
> runs the integrity sweep to repair it.

### ✅ Result — 35/35 passed (verified)

```
11 dashboard endpoints ✔   admin auth (wrong + missing key) ✔
9 stat-card fields ✔       10/10 Red Team scenarios DEFENDED, 0 failed steps ✔
chain intact after every attack (18 records, 0 invalid signatures) ✔
8 tamper/recovery events available for the Audit Defence panel ✔
```

### 2B — Visual check (http://localhost:3001, hard-refresh ⌘⇧R)

☐ 2.1 Green connection dot after auto-connect (key `securewealth-admin-2026`)
☐ 2.2 **Overview** cards show non-zero counts matching your Phase 1 investments
☐ 2.3 Click **Verify chain now** → **✔ CHAIN INTACT** with record count
☐ 2.4 **Audit Log** tab → records listed with hash-chain links (⟵ prev / ⟶ current)
☐ 2.5 Filter by decision `CHALLENGE` → only challenge records show
☐ 2.6 Type a partial transaction ID into search → matching record only
☐ 2.7 **Investments** tab → shows customer name + SecureWealth ID + fund + decision
☐ 2.7b **Audit Defence** panel → "No tampering detected" when clean; tamper +
       self-heal entries appear after running `attack_sim.py`
☐ 2.9 **Red Team tab** — 10 scenario cards, header reads "10 scenarios · run
       one at a time · results are audited"
☐ 2.10 Click one Run button → **all other Run buttons disable** until it finishes
☐ 2.11 **Mass Forgery — 3 of 4 Copies** → timeline shows "Head-count would have
       failed" then "Cryptographic authority applied" → forgery reversed
☐ 2.12 Timelines are readable: red pulsing dot on the attack step, green on
       each defence, verdict banner + elapsed ms
☐ 2.13 Resize the window narrow → cards reflow, tables scroll, nothing clips

☐ 2.8 **LIVE TEST:** keep the dashboard open, fire a ₹95,000 investment from
       Terminal/app → within 5 seconds a red toast appears and the alert lands
       in the feed. *(This is the live-attack demo moment.)*

---

## Phase 3 — Mobile App End-to-End

☐ 3.1 **Login** with `SW10000001` / `123456` — the field says "SecureWealth ID", not phone
☐ 3.2 App **lands on the Wealth Dashboard**, not Home (task 1.3)
☐ 3.3 Tab order is **Home → Wealth → Security → Phishing → Profile** (task 1.1)
☐ 3.4 The word "Send"/"Send Money" appears **nowhere**; it's "Invest" (task 1.2)
☐ 3.5 Wealth screen shows Net Worth, accounts, deposits, loans, AI recommendations
☐ 3.6 Tap an ⓘ tooltip (Net Worth / Risk Score) → glossary popup opens (task 1.4)

**Investment — ALLOW path**
☐ 3.7 Wealth → Invest → only **Savings** accounts appear as source
☐ 3.8 Fund list shows 6 mutual-fund categories with risk badges — **no stocks**
☐ 3.9 Invest ₹4,000 in Bluechip Equity Fund SIP → "All Clear" → Continue → receipt
☐ 3.10 Balance on Wealth screen decreased by ₹4,000 (pull to refresh)

**Investment — CHALLENGE path**
☐ 3.11 Invest ₹95,000 → "Verification Needed", copy says money hasn't moved
☐ 3.12 Tap **Verify My Identity** → Challenge screen with step progress
☐ 3.13 Enter a WRONG value → error with attempts remaining, no crash
☐ 3.14 Enter correct MPIN `123456`, then the OTP shown in the demo-SMS card
☐ 3.15 Success → receipt; balance now reduced by ₹95,000
☐ 3.16 The OTP card displays **"Never share this OTP with anyone."**

**Phishing (task 6)**
☐ 3.17 Phishing tab → consent card appears (not yet scanning)
☐ 3.18 Tap **Allow & Scan My Messages** → scanning starts **automatically**
☐ 3.19 Fake-KYC, lottery, and parcel SMS → **Suspicious**; bank alert & "Mom" → **Safe**
☐ 3.20 Tap a suspicious message → plain-language explanation appears
☐ 3.21 The genuine OTP message shows the "Never share this OTP" warning
☐ 3.22 "Turn off automatic scanning" returns to the consent card

**Multilingual (task 1.5)**
☐ 3.23 Profile → tap **हिन्दी** → tabs, Invest screen, decision text switch to Hindi
☐ 3.24 Tap **ਪੰਜਾਬੀ** → switches to Punjabi
☐ 3.25 Force-close and reopen the app → language persists
☐ 3.26 Switch back to English

---

## Phase 4 — Failure & Safety Tests (do these; judges probe here)

☐ 4.1 **Insufficient balance:** invest more than the account holds → clean
      "Not enough balance" message, no crash, no partial debit
☐ 4.2 **Backend down:** stop uvicorn, try to invest → friendly "cannot reach
      server" message, app stays usable (no white screen)
☐ 4.3 **Wrong admin key:** change the key in the dashboard → 401, clear alert
☐ 4.4 **Challenge lockout:** trigger a CHALLENGE, fail verification 3 times →
      investment cancelled, status FAILED, balance untouched
☐ 4.5 **Audit not blocking:** confirm every investment in Phase 1/3 produced an
      audit record — counts should match exactly
☐ 4.6 **Session expiry:** wait past token expiry (or clear it) → app returns to
      login rather than erroring

---

## Phase 5 — Full Demo Rehearsal (run twice, timed)

```bash
# Fresh state before each rehearsal:
cd backend && python scripts/seed_demo.py --reset-audit
```

1. Login `SW10000001` / `123456`
2. Wealth Dashboard → Net Worth → AI recommendation
3. Invest ₹4,000 → **ALLOW** (silent, no friction) ← "security doesn't disturb genuine users"
4. Invest ₹95,000 → **CHALLENGE** → verify → success ← "adaptive security"
5. Switch to Admin Dashboard → live alert already there → Audit Log → **Verify chain now** → ✔ CHAIN INTACT ← **the USP moment**
6. Phishing tab → auto-scan → suspicious SMS explained ← "protection beyond transactions"
7. Profile → हिन्दी → app switches language ← "inclusive banking"

☐ Runs end-to-end without a single error
☐ Completes within your presentation time slot
☐ Each teammate knows which screen is theirs

---

# Phase 6 — Mobile App Verification (M8)

Everything above proves the backend is correct. This phase proves the **app**
is correct, which is a different question: the backend can return 200 with a
renamed field and the app will render a blank card while every backend test
still passes. That has happened twice in this project, so it is now asserted.

## 6.1 Automated: app contract test

```bash
cd backend && bash scripts/frontend_test.sh
```

Walks all **34 endpoints the app actually calls**, in the order the app calls
them, and asserts each response contains the fields the screens read:

| Section | Screen | What it proves |
|---|---|---|
| 1–2 | Register → Auth | A new customer can open an account and sign in with the issued SecureWealth ID |
| 3 | deviceSession | The device registers, so trust scoring is not running blind |
| 4 | Profile | Session carries `customer_id`; device list has `trust_status` |
| 5 | Consent gate | Aggregation returns **403** before consent — this is what makes ConsentScreen appear |
| 6 | Wealth | Net worth, cash flow, linked accounts, and every recommendation-card field |
| 7 | Dashboard | Dashboard summary + activity feed |
| 8 | Invest | `triggered_signals` is a real list — the "what we checked" panel shows engine data |
| 9 | Challenge | Start, method options, explanation, wrong-answer rejection, cancel |
| 10 | Phishing | Manual scan, inbox bulk scan, threat explanation |
| 11 | Profile actions | Device-trust explanation, consent revoke, logout |

It creates its own throwaway customer, so it is safe to run repeatedly and
does **not** need `seed_demo.py` first.

## 6.2 Automated: frontend guards

```bash
cd frontend
npx tsc --noEmit           # types
node scripts/i18n_check.js # 205 keys × EN/HI/PA, no gaps, no untranslated
node scripts/a11y_check.js # every icon-only control labelled + reachable
```

`i18n_check` fails on missing keys, dead keys, and values left in English.
It has already caught three apostrophes that silently truncated TypeScript
string literals — `tsc` compiled them without complaint.

## 6.3 Manual checklist (device or simulator)

Run with the backend on `--host 0.0.0.0` and Ollama running.

**Identity**
- ☐ Register → SecureWealth ID shown on the card, Continue disabled until "I have saved my ID" is ticked
- ☐ Sign in with that ID; the phone number is **not** accepted as a login
- ☐ Profile shows the ID, and this handset appears under Your devices marked **THIS DEVICE**

**Wealth**
- ☐ First open shows a **skeleton**, not a spinner, and the layout does not jump when data lands
- ☐ Net worth hero shows the assets-vs-liabilities bar with a sensible caption
- ☐ Financial health card shows a grade and four component bars
- ☐ A recommendation shows amount **and** tenure; "Why this?" fills with generated text
- ☐ "Start this" pre-fills the Invest screen with that amount

**Consent**
- ☐ Profile → turn consent off → Wealth tab shows the consent screen, not an error
- ☐ Grant consent → data returns immediately without a manual refresh

**Investing**
- ☐ ₹3,000–5,000 → ALLOW, no friction
- ☐ ₹90,000+ → CHALLENGE; the checking screen counts seconds and passes 8s copy if slow
- ☐ "What we checked" lists signals consistent with the verdict (never contradicting it)
- ☐ Challenge → "Verify another way" → switching to MPIN warns that an extra step is added
- ☐ Biometric is listed but **disabled**, with the attestation reason shown
- ☐ "I didn't start this" → investment stops → appears in activity as **You stopped this investment**

**Security activity**
- ☐ Grouped under Today / Yesterday
- ☐ Every healthy row shows a green padlock, not an amber warning
- ☐ No hashes or signatures anywhere in the customer app

**Phishing**
- ☐ Header reflects the real scan result (protected / N found / protection off)
- ☐ Tapping a flagged message opens the sheet with numbered actions
- ☐ Stop the backend, scan a message → an honest error, **never** a fabricated verdict

**Language**
- ☐ Profile → हिन्दी → Wealth, Dashboard, Safety, Activity, Profile, Challenge all switch
- ☐ Profile → ਪੰਜਾਬੀ → same
- ☐ Force-quit and reopen → the chosen language persists

**Robustness**
- ☐ Turn off wifi mid-session → clear "cannot reach the server" messages, no white screen
- ☐ No screen shows placeholder data (no "iPhone 14 Pro, Delhi", no fixed "65%")

## 6.4 Demo personas

```bash
cd backend && python scripts/seed_personas.py --reset-audit
```

Five customers, all MPIN **123456**, each landing in a different branch of the
wealth engine and carrying a different security baseline. Use whichever the
question calls for instead of trying to tell every story through one login.

| Login | Who | Wealth advice they get | Security demo |
|---|---|---|---|
| SW10000001 | Swayam Kohli | **Growth SIP** — 5.2 months runway, low debt, real surplus | ₹4,000 ALLOW · ₹95,000 CHALLENGE |
| SW10000002 | Mahak Singh | **Build emergency fund** — holds ₹74k against a ₹2.08L target | ₹40,000 already CHALLENGEs — her baseline is ₹1–2k |
| SW10000003 | Archit Sahay | **Pay down the 15.8% loan** — 58% of income goes to EMIs | New device, so extra verification |
| SW10000004 | Ayush Kyumar | **Deploy idle cash + reinvest a maturing FD** — ₹12.5L sitting idle, ₹5L FD due in 45 days | ₹90,000 is normal for him and still ALLOWs |
| SW10000005 | Vishwas Kesarwani | **Advice suppressed** — ₹62k income against ₹61k spending, so it says fix expenses first | Night-time investor; daytime is his anomaly |

The last one is worth showing deliberately: the engine declines to recommend a
product to someone who cannot afford one. That is a harder thing for a bank to
demo than a recommendation, and it is the honest answer.

☐ Log in as each and confirm the advice differs
☐ Show Mahak and Ayush side by side — same engine, opposite conclusions

---

## 6.5 Timed demo rehearsal

Run **twice**, timed, with a stopwatch. Before each run:

```bash
cd backend && python scripts/seed_demo.py --reset-audit
# leave the server running so the LLM stays warm — a cold model adds ~30s
```

| # | Beat | Says |
|---|---|---|
| 1 | Sign in with SecureWealth ID | Bank-grade identity, not a phone number |
| 2 | Wealth tab: net worth, health grade, recommendation | Wealth **first** |
| 3 | Invest ₹4,000 → ALLOW, no friction | Security does not punish genuine customers |
| 4 | Invest ₹95,000 → CHALLENGE with live timer | Adaptive, and the money never moved |
| 5 | "Verify another way" → alternative 2FA | Choice without lowering assurance |
| 6 | Admin dashboard → Verify chain → CHAIN INTACT | **The USP moment** |
| 7 | Red Team tab → run a tamper scenario → DEFENDED | It survives attack, live |
| 8 | Phishing tab → flagged SMS → what to do now | Protection beyond transactions |
| 9 | Profile → हिन्दी | Inclusive banking |

- ☐ End-to-end with zero errors, twice
- ☐ Inside the time slot with a minute spare
- ☐ Each teammate knows which beat is theirs
- ☐ Ollama warmed before you walk on stage

---

## Known Limitations (be ready to answer)

| Item | Status | Honest answer for judges |
|---|---|---|
| Zero-Day autoencoder | **Active** | PyTorch autoencoder, one-class trained on 136,500 legitimate transactions — it never saw a fraud example, so it detects novelty rather than known patterns. Thresholds are the p95/p99 of legitimate reconstruction error, not hand-picked. Verify with `GET /api/v1/health/ai` and `python scripts/zero_day_check.py`. If torch or the artifacts are missing it falls back to a numpy statistical detector, so the layer is never simply absent. |
| Real SMS reading | Simulated inbox | iOS forbids SMS inbox access; Android needs a signed build with READ_SMS. Disclosed in-app on the Phishing tab. Consent, scanning, verdicts and explanations all run through the **real** engine — only the message list is a stand-in. |
| OTP delivery | `demo_otp` in response | No SMS gateway in the demo; swap in a provider at one call site. |
| Trusted devices | Working | The app registers the handset on login and Profile shows each device's trust status in plain language. Explicit primary/secondary designation is not built. |
| Challenge sessions | In-memory | Fine for demo; use Redis in production. |
| Biometric verification | Listed, disabled | A fingerprint match happens on the handset, so the server receives only a boolean it cannot verify. Accepting it would be theatre. Needs Android Keystore / iOS Secure Enclave attestation. Shown in the method picker with that reason. |
| Scam reporting | Local to the session | "Report this as a scam" records the customer's judgement in-app; a production build would forward it to the bank's fraud desk. |
| Push notifications | Not built | Would need `expo-notifications`; deliberately not added late in the build to avoid destabilising the Expo Go demo. |
