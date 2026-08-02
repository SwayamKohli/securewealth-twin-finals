# Mobile App — Audit & Implementation Plan

Analysis of the existing Expo/React Native app, followed by the plan.

> **STATUS: M1–M8 delivered.** Everything below is implemented except the two
> items listed as deliberately deferred (push notifications, task 17). The
> "what exists today" section is preserved as the *original* audit — it is the
> before picture, not the current state.
>
> | Batch | Tasks | Status |
> |---|---|---|
> | M1 Identity & device trust | 1–3 | Done |
> | M2 Consent & aggregation | 4–5 | Done |
> | M3 Challenge + method choice | 6–8 | Done |
> | M4 Wealth recommendations | 9–11 | Done |
> | M5 Security activity | 12–14 | Done |
> | M6 Phishing | 15–16 | Done · 17 (push) deferred |
> | M7 Polish | 18–23 | Done |
> | M8 Verification | 24–25 | Automated done · manual rehearsal is yours to run |
>
> **API usage went from 15 of 57 methods to 34.** The three gaps called out in
> the audit below — no device registration, no consent UI, unused explainability
> engines — are all closed.
>
> Verified by: `smoke_test.sh` 58/58 · `frontend_test.sh` 36/36 ·
> `explainer_test.sh` 11/11 (7 engines on the local LLM) ·
> `audit_phase_test.py` 36/36 · `dashboard_test.sh` 35/35 ·
> `i18n_check.js` 205 keys × 3 languages · `a11y_check.js` clean · `tsc` clean.

---

## Part 1 — What exists today

### Screens (12 files, ~8,100 lines)

| Screen | Lines | Backend calls | State |
|---|---|---|---|
| DashboardScreen | 1103 | `getDashboard` | Home tab |
| WealthOverviewScreen | 890 | `getAccounts`, `getDeposits`, `getLoans`, `getNetWorth`, `getCashflow`, `getWealthRecommendations` | Landing tab — best-integrated screen |
| AuditDashboardScreen | 788 | *(mock JSON)* | **DEAD** — unrouted, deprecated |
| SecurityReviewScreen | 777 | `initiateTransaction` | Decision screen |
| PhishingScannerScreen | 679 | `scanPhishing` | Phishing tab |
| TransactionInitiateScreen | 668 | `getAccounts` | Invest screen |
| AuthScreen | 451 | `login` | **Login only — no registration** |
| SmsInboxScan (component) | 440 | `bulkScanPhishing`, `explainPhishing` | Auto-scan |
| ChallengeScreen | 360 | `startChallenge`, `verifyChallenge` | Step-up verification |
| TransactionResultScreen | 324 | — | Receipt |
| MySecurityActivityScreen | 321 | `getMySecurityActivity` | Security tab |
| SafetyHubScreen | 263 | — | Security tab landing |
| Profile | ~50 (inline) | — | **Placeholder only** |

### The headline finding: 42 of 57 API methods are never called

The app uses **15**. Unused, grouped by why it matters:

**🔴 Breaks a security claim**
- `registerDevice`, `getDevices`, `getCurrentDevice` — **the app never registers a device.**
  The risk engine scores device trust on every investment, but with no device ever
  registered it falls back to `NEW_DEVICE` / "no registered device". Trusted-device
  scoring, the two-device requirement (task 4.4) and device-based challenges are all
  running blind. This is the most important gap in the app.

**🟠 Feature built on the backend, invisible in the app**
- `register` — no registration screen exists at all
- Consent endpoints — the consent gate is enforced by the API but the app never asks
  for consent, so a fresh user would hit 403s with no way to resolve them
- `linkAccount`, `syncAggregation`, `getAggregationStatus` — Account Aggregation has no UI
- `explainDecision`, `explainWealth`, `explainRisk` — Explainability APIs unused;
  SecurityReview shows a **local JSON copy** of signal text instead of the live engine
- `getTransactions` — no investment history screen
- `getSession`, `getCurrentUser`, `updateUser`, `logout` — Profile is a placeholder;
  logout clears the token locally without calling the API

**⚪ Genuinely not needed** — `createAccount/Deposit/Loan/Card`, `delete*`, `evaluateFraud`,
`evaluateRisk`, `makeDecision` (correctly removed — backend orchestrates now).

### Other issues found

1. **i18n covers 5 of 12 screens.** Dashboard, Wealth, Phishing, Safety Hub,
   Result and Activity are still English-only, so switching to हिन्दी leaves most
   of the app untranslated.
2. **`AuditDashboardScreen` + `HashChainVisual`** — 1,000 lines of dead weight
   showing hashes to customers.
3. **Two mock JSON files remain as UI copy** (`risk_signals.json`,
   `phishing_signals.json`) — acceptable, but SecurityReview should prefer the
   live explainability API and fall back to them.
4. **Challenge screen offers no choice of method** — if the user can't get the
   OTP, the flow dead-ends after 3 attempts.
5. **No error boundary** — one render error white-screens the whole app.

---

## Part 2 — Decisions taken

| Question | Decision |
|---|---|
| Registration | **Keep self-signup**, build a polished screen that surfaces the issued SecureWealth ID |
| Challenge "override" | **Choose an alternative 2FA method** — verification stays mandatory, the user picks *how* |
| Phishing input | **Consent-gated demo inbox + paste**, honestly documented |
| Audit screens | **Comment out** AuditDashboardScreen + HashChainVisual; keep plain-English activity |

---

## Part 3 — Implementation plan

Ordered so each batch is independently demoable and nothing blocks the next.

### M1 · Identity & Device Trust *(highest value — closes the security gap)*

1. **Registration screen** — name, phone, email, DOB, 6-digit MPIN with
   confirmation and live validation. On success: a success screen presenting the
   **SecureWealth ID prominently** ("This is your login ID — save it"), copy-to-
   clipboard, then straight into login.
2. **Device registration on first login** — call `registerDevice` with a stable
   device name/type, persist the device ID, and send it on subsequent sessions.
   *This makes device-trust scoring real instead of a fallback.*
3. **Profile screen (real)** — `getSession` + `getCurrentUser`: name, masked
   SecureWealth ID, registered devices with trust status, language switcher,
   consent toggle, proper `logout` API call.

**Affects:** `AuthScreen`, new `RegisterScreen`, new `ProfileScreen`, `navigation`, `apiService`
**Test:** register → ID shown → login → device appears in Profile → investment risk reflects a trusted device

---

### M2 · Consent & Account Aggregation *(makes a task-list feature visible)*

4. **Consent gate on first launch** — if `GET /aggregation/consent` is false, show
   a clean consent screen (what we access, why, revocable) before the Wealth tab
   loads. Handle 403 gracefully everywhere instead of showing an error.
5. **Linked banks card** on Wealth — `getAggregationStatus` + `linkAccount` +
   `syncAggregation`, with a "Last synced" timestamp and pull-to-sync.

**Affects:** new `ConsentScreen`, `WealthOverviewScreen`, `navigation`
**Test:** revoke consent in Profile → app prompts for consent → grant → data returns

---

### M3 · Challenge Flow with Method Choice *(your specific ask)*

6. **Method picker** — when a challenge starts, show the available verification
   methods as cards (OTP to registered mobile · MPIN · Security question ·
   Biometric where available). Default to the backend's recommendation, but let the
   user switch: *"Can't access your OTP right now? Verify another way."*
7. **Backend support** — `POST /security/challenge/{txn}/method` to switch the
   active step, plus a `/cancel` endpoint so "This wasn't me" drops the investment
   and records it as a reported fraud attempt.
8. **Better challenge UI** — animated step progress, countdown on OTP expiry,
   resend, attempts-left meter, and a persistent "your money hasn't moved" banner.

**Affects:** `ChallengeScreen`, `challenge_service.py`, `challenge_api.py`
**Test:** trigger challenge → switch method → verify → success; and → "not me" → cancelled + recorded

---

### M4 · Wealth Recommendations *(depth on the "Wealth First" half)*

9. **Rebuild the recommendations section** — currently a flat list. Make each
   recommendation a proper card: goal, suggested amount, tenure, expected benefit,
   confidence bar, and an expandable **"Why this?"** powered by the live
   `explainWealth` endpoint in the selected language.
10. **Net Worth visual** — assets vs liabilities bar, trend, and the
    financial-health grade with its component breakdown.
11. **Invest directly from a recommendation** — "Start this SIP" pre-fills the
    Invest screen. Closes the loop between advice and action.

**Affects:** `WealthOverviewScreen`, `TransactionInitiateScreen`

---

### M5 · Security Activity & Explainability *(customer-friendly, no jargon)*

12. **Comment out** `AuditDashboardScreen` and `HashChainVisual` with a note
    pointing to the admin web app.
13. **My Security Activity polish** — timeline grouped by day, decision icons,
    amount + fund, and a subtle "tamper-protected" badge with a one-line plain
    explanation. No hashes.
14. **Live explainability in SecurityReview** — call `explainDecision` for the
    plain-language reason (multilingual), falling back to the local JSON copy if
    the API is unreachable.

**Affects:** `MySecurityActivityScreen`, `SecurityReviewScreen`, `navigation`

---

### M6 · Phishing Protection *(honest, and better-looking)*

15. **Restructure the Phishing tab** — protection status header, auto-scan results,
    manual check below, and a "How this works on a real device" disclosure.
16. **Threat detail sheet** — tap a suspicious message for the live explanation,
    what to do next, and a "Report" action.
17. *(Optional)* **Local push notification** when a scam is detected — genuinely
    real alerting, cheap to add, demos well.

**Affects:** `PhishingScannerScreen`, `SmsInboxScan`

---

### M7 · Polish Pass *(the "premium" ask)*

18. **Finish i18n** — the 7 untranslated screens.
19. **Skeleton loaders** instead of spinners; consistent empty states.
20. **Micro-interactions** — press feedback, screen transitions, number count-ups
    on balances, success animation on completed investment.
21. **Error boundary + offline banner** — never white-screen; show "You're offline"
    and retry.
22. **Tooltip coverage sweep** — every technical term across all screens.
23. **Accessibility** — labels, hit targets ≥44px, contrast check.

---

### M8 · Verification

24. **`frontend_test.sh`** — asserts every endpoint the app calls, in the order the
    app calls it (register → login → device → consent → wealth → invest →
    challenge → activity → phishing).
25. **Manual checklist** in `TESTING.md`, and a timed demo-journey rehearsal.

---

## Sequencing

```
M1 Identity + Device Trust   ← start here (closes the real security gap)
M2 Consent & Aggregation
M3 Challenge + method choice ← your specific ask
M4 Wealth recommendations
M5 Security activity         ← includes commenting out audit screens
M6 Phishing
M7 Polish
M8 Verification
```

M1–M3 are the ones that change what the app *does*. M4–M6 deepen existing
screens. M7 is presentation. M8 proves it.

---

## Two things worth flagging

**Device registration is not cosmetic.** Every investment is currently scored
against a device the backend has never seen. Fixing this in M1 will change risk
scores — expect ALLOW decisions to get *cleaner* (a trusted 120-day device
lowers risk) and unknown-device challenges to start firing correctly. Worth
re-running `smoke_test.sh` after M1.

**Scope check.** M1–M3 + M5 are essential. M4 and M6 are depth. M7 is polish.
If time runs short, M7 items 20–23 are the safest to cut — say the word and
I'll re-order.
