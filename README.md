# SecureWealth Twin

**Wealth First. Security Always.**

An AI-powered wealth-first banking platform that combines consent-based account
aggregation, intelligent wealth guidance, and adaptive fraud protection — with
an immutable, self-healing audit trail as its core differentiator.

---

## Architecture

```
                        ┌──────────────────────────┐
   Mobile App (Expo)    │   Admin Dashboard (Web)  │
   Wealth-first UX      │   Audit • Live Fraud     │
        │               └───────────┬──────────────┘
        │  JWT                      │  X-Admin-Key
        └───────────┬───────────────┘
                    ▼
             FastAPI Backend
                    │
  ┌─────────────────┼──────────────────────┐
  │                 │                      │
Wealth AI     Security Pipeline      Audit Engine
(profile →    (Behavior → Fraud ML   (hash chain +
 wealth       → Zero-Day → Risk      RSA signature
 engine)      → Decision)             + 3 replicas)
                    │                      │
                    └──────► ALLOW / WARN / CHALLENGE / BLOCK
                                           │
                                    one immutable
                                    audit record
```

**Key principle:** the frontend never calls AI modules directly. One call to
`POST /api/v1/transactions/initiate` runs the entire security pipeline server
side, writes the audit record, and returns the decision.

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head                                  # applies all migrations
python scripts/seed_demo.py --reset-audit             # demo world + clean audit chain

uvicorn main:app --reload                             # http://127.0.0.1:8000/docs
```

**Demo credentials** — SecureWealth ID `SW10000001` / MPIN `123456`

The seed creates: 2 Savings accounts (₹2,50,000 + ₹1,20,000), FD ₹3,00,000,
RD ₹60,000, home loan ₹12,00,000, a trusted 120-day-old device, a behavioural
profile, and ~10 SIP investments over the last 30 days (the fraud engine's
baseline). `--reset-audit` wipes any broken audit chain from earlier runs.

### 2. Mobile App

```bash
cd frontend
npm install
# set your machine's LAN IP in src/api/config.ts (API_BASE_URL)
npx expo start
```

### 3. Admin Dashboard (standalone web app)

```bash
cd admin-dashboard
python -m http.server 3001      # then open http://localhost:3001
```
Default admin key: `securewealth-admin-2026` (change via `ADMIN_API_KEY` in `.env`).

---

## Authentication

Login uses a bank-grade **SecureWealth ID** (CIF-style, e.g. `SW10000001`),
issued once at registration. Phone-number login has been removed. The accepted
identifier type is configurable:

```env
LOGIN_METHODS=CUSTOMER_ID        # default; supports CUSTOMER_ID, PHONE
```

---

## Feature Map

| Feature | Where |
|---|---|
| Consent-based aggregation | `GET/POST/DELETE /api/v1/aggregation/consent` — data endpoints 403 until consent |
| Unified wealth dashboard + Net Worth | Wealth tab · `wealth_position` in wealth API responses |
| Wealth AI (MF-only, expense-aware, fraud-gated) | `ai/engines/wealth_engine.py` |
| Investment-only workflow | Savings → Mutual Fund; `fund_name` / `fund_category`, MF whitelist |
| Real-time fraud detection | `services/security/security_pipeline.py` |
| Adaptive security | ALLOW / WARN / CHALLENGE / BLOCK |
| Challenge flow | `POST /api/v1/security/challenge/{txn}/start` and `/verify` |
| Immutable audit | one record per investment; hash chain + RSA signature + 3 replicas |
| Admin APIs | `/api/v1/admin/stats · /audit · /alerts · /investments` |
| SMS phishing auto-scan | Phishing tab — consent → auto scan → explained alerts |
| Multilingual | English / हिन्दी / ਪੰਜਾਬੀ — Profile tab switcher + `language` on explainability APIs |

### Adaptive challenge plans

| Trigger | Steps required |
|---|---|
| Unknown device | Security question → OTP |
| Large amount spike | MPIN → OTP |
| OTP-distress signal | OTP re-confirmation |
| Unusual time / pattern | Acknowledge → MPIN |

OTP is never shown unless the risk actually calls for it. Three failed attempts
cancels the investment. Held investments debit nothing until verification passes.

---

## Demo Journey

1. **Login** — `SW10000001` / `123456` → lands directly on the Wealth Dashboard.
2. **Wealth** — Net Worth, assets vs liabilities, AI recommendations (mutual
   fund categories only, never stocks).
3. **Invest ₹4,000** in Bluechip Equity Fund SIP → **ALLOW**, silent approval.
4. **Invest ₹95,000** → **CHALLENGE** → verification steps → investment completes.
5. **Admin Dashboard** — the alert appears within 5 seconds; open the Audit Log
   to show the hash-chained record, then click **Verify chain now** →
   ✔ CHAIN INTACT.
6. **Phishing tab** — grant consent → messages scan automatically → the fake-KYC
   and lottery SMS flag as Suspicious with plain-language reasons; the genuine
   OTP message shows "Never share this OTP with anyone."
7. **Profile → हिन्दी / ਪੰਜਾਬੀ** — the app switches language live.

---

## Safety Properties

- **Fail-safe, not fail-open** — a security pipeline error yields CHALLENGE, never a silent ALLOW.
- **Graceful AI degradation** — missing ML artifacts log a warning and fall back to rule-based signals; the app never hard-fails.
- **Audit never blocks the customer** — audit write failures are logged, the investment still completes.
- **No stock recommendations** — an approved-product whitelist is enforced before every wealth response.
