# SecureWealth Twin

**Intelligent Wealth Growth with Built-in Fraud Protection**  
*Wealth First. Security Always.*

[![Punjab & Sind Bank Hackathon 2026 Finalist](https://img.shields.io/badge/PSB%20Hackathon%202026-Finalist-006837.svg)](https://punjabandsindbank.co.in)
[![Domain](https://img.shields.io/badge/Domain-AI%20%C3%97%20Cybersecurity-purple.svg)](#the-security-growth-paradox)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20PostgreSQL-blue.svg)](https://fastapi.tiangolo.com/)
[![Mobile](https://img.shields.io/badge/Mobile-React%20Native%20%7C%20Expo-000000.svg)](https://expo.dev)
[![AI/ML](https://img.shields.io/badge/AI%2FML-PyTorch%20%7C%20XGBoost%20%7C%20Ollama-orange.svg)](https://pytorch.org/)
[![Audit & Crypto](https://img.shields.io/badge/Cybersecurity-Ed25519%20%7C%20SHA--256%20Chain-green.svg)](https://ed25519.cr.yp.to/)
[![Languages](https://img.shields.io/badge/Languages-English%20%7C%20हिन्दी%20%7C%20ਪੰਜਾਬੀ-gold.svg)](#multilingual-plain-language-explainability)
[![License: All Rights Reserved](https://img.shields.io/badge/License-All%20Rights%20Reserved-red.svg)](LICENSE)

SecureWealth Twin is a unified **AI × Cybersecurity** banking platform engineered for the **Punjab & Sind Bank (PSB) Hackathon 2026 Finals**. It operates as the customer’s virtual financial twin — bridging personalized, consent-driven wealth guidance with an active, behavioral **Cyber-Protection Layer** and an **immutable, self-healing Master-Replica audit engine** that protects assets before any money moves.

---

## Core Engineering Team & Leadership

The end-to-end architecture, technical implementation, cybersecurity pipeline, mobile experience, and AI models of SecureWealth Twin were **mostly done and driven by the following core members**:

| Member | Role | Core Engineering Ownership |
|---|---|---|
| **[Swayam Kohli](https://github.com/SwayamKohli)** | **Team Lead — AI & Cybersecurity Systems Architect** | Led overall system design, cybersecurity defense integration, and cross-layer technical orchestration; engineered the entire mobile application from scratch (14 production screens, trilingual i18n system across 260 keys, focus-based navigation, resilient timeout recovery); integrated the 5-stage behavioral cyber-protection pipeline into the live transaction lifecycle; diagnosed and resolved complex cash-flow and data pipeline calculation defects; authored end-to-end automated verification suites and red-team attack simulators. |
| **[Mahak Singh](https://github.com/Mahak0205)** | **Backend & Distributed Systems Engineer** | Implemented the Master-Replica distributed audit database architecture and consensus-based replication framework; built core database ORM models and repository abstractions; authored foundational security and audit API schemas, migrations, and backend service orchestration. |
| **[Ayush](https://github.com/Kaizoku-Ayush)** | **AI / Machine Learning Lead** | Researched, trained, and evaluated the machine learning fraud detection models with behavioral feature engineering and SHAP attribution; developed the ethical wealth intelligence engine (budgeting rules, emergency reserve models, debt-to-income checks, and fraud gating); engineered the unified financial profiling layer. |
| **[Archit Sahay](https://github.com/arcfr)** | **AI Explainability & Local LLM Lead** | Designed and authored the 7 plain-language explainability engines converting complex security and wealth decisions into human-readable text; integrated offline local LLM inference with deterministic fallback templates; created multilingual prompt systems and the SMS phishing intelligence module. |

---

## The Problem Statement & The Security-Growth Paradox

Modern Public Sector Banks face a critical dual mandate: empowering customers to grow their wealth through digital advisory while actively safeguarding those assets against sophisticated cyber threats.

SecureWealth Twin was built to solve the **four core challenges** outlined in the PSB problem statement:

1. **The Security-Growth Paradox:** Traditional security measures (hard blocks, repetitive SMS OTPs) cause friction that alienates wealth management users. Conversely, frictionless experiences expose users to social engineering, coerced transfers, and impulsive scams.  
   *$\rightarrow$ SecureWealth Twin resolves this with an **adaptive, risk-weighted step-up challenge matrix**: routine transactions remain frictionless (`ALLOW`), while suspicious spikes trigger contextual verification (`CHALLENGE`).*
2. **Fragmented Financial Visibility:** Customers hold scattered assets across multiple institutions, blinding advisory engines.  
   *$\rightarrow$ Solved via **consent-gated Account Aggregator integration** providing a unified view of net worth, cash flow, liquidity ratios, and liabilities.*
3. **Sophisticated Behavioral Fraud Vectors:** Modern attacks are rarely just brute force; fraudsters use behavioral coercion (e.g. phone-coached fund transfers, nocturnal drain attempts, rapid velocity bursts).  
   *$\rightarrow$ Solved via an **in-line 5-stage cyber-pipeline** combining behavioral telemetry, XGBoost classification, and PyTorch autoencoder novelty detection.*
4. **The "Black Box" Explainability Gap:** Regulators and customers distrust opaque AI.  
   *$\rightarrow$ Solved via **7 locally hosted explainability engines** translating decisions into transparent, plain-language justifications in English, Hindi, and Punjabi with anti-hallucination guardrails.*

---

## Architecture Overview

```
                         ┌──────────────────────────┐
    Mobile App (Expo)    │   Admin Dashboard (Web)  │
    Wealth-first UX      │   Audit • Red Team Suite │
         │               └───────────┬──────────────┘
         │  JWT                      │  X-Admin-Key
         └───────────┬───────────────┘
                     ▼
              FastAPI Backend (90 route handlers)
                     │
   ┌─────────────────┼────────────────────────────────┐
   │                 │                                │
Wealth Engine   Security Pipeline               Audit Engine
(Profile ->     (Behavior -> Fraud ML ->       (Master + 3 Replicas
 Wealth Advice)  Zero-Day -> Risk -> Decision)  Hash Chain + Ed25519)
                     │                                │
                     └──────► ALLOW / WARN /          │
                              CHALLENGE / BLOCK       │
                                     │                │
                              One Immutable, Self-Healing Audit Record
```

**Architectural Principle:** The frontend never orchestrates security or AI calls directly. A single call executes the five-stage cyber-pipeline server-side, signs and writes the audit record across all replicas, and returns the verdict.

---

## Core Differentiator: Byzantine-Resilient Master-Replica Audit Trail

Traditional banking audit trails are designed against external attacks or data loss (e.g. keeping backups). **They fail against the realistic threat: a privileged insider** (a malicious DBA or compromised admin) who issues a direct SQL update to cover up fraud:

```sql
UPDATE audit_logs SET final_decision = 'ALLOW', risk_score = 1 WHERE transaction_id = '...';
```

In typical master-slave replication, the corrupted master simply overwrites the slaves, permanently erasing the evidence. SecureWealth Twin flips this power dynamic:

```
                    ┌─────────────────────────┐
                    │ Transaction Decision    │
                    └───────────┬─────────────┘
                                │ SHA-256 Hash Chaining + Ed25519 Digital Signing
                                ▼
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
   Master Table             Replica 1              Replica 2              Replica 3
   (`audit_logs`)     (`audit_replica_1`)    (`audit_replica_2`)    (`audit_replica_3`)
         │                      │                      │                      │
         └──────────────────────┼──────────────────────┼──────────────────────┘
                                ▼
                     `ReplicaVerifier`
                 (Equal Voters + Crypto Authority)
                                │
               Tamper Detected in Master or Replicas?
                                ▼
                     `RecoveryService`
                 (Autonomous Self-Healing)
                                │
          Replicas Vote Out & OVERWRITE the Corrupted Master!
```

### Key Pillars of the Audit Engine

1. **4-Way Lockstep Replication:** Every transaction decision writes synchronously to the primary master table and three distinct physical replica tables.
2. **Cryptographic Chaining:** Each record stores a cryptographic hash linking it to its predecessor (`previous_hash`). Modifying any historical record invalidates every downstream link in the chain.
3. **Inversion of Authority:** The verifier does not assume the Master is correct. All 4 copies are treated as equal voters. If an insider modifies the Master, the 3 untouched replicas out-vote it 3-to-1, flagging the Master as corrupted.
4. **Cryptographic Authority Trumps Head-Count ("Test D"):** If an attacker modifies 3 of the 4 copies to the same forged value, naive majority voting fails. SecureWealth Twin signs every record with an asymmetric **Ed25519 private key** stored outside the database. Forged copies fail cryptographic verification regardless of how many exist; **a single signature-valid copy outranks any number of agreeing forgeries.**
5. **Autonomous Self-Healing:** The recovery service automatically replaces the corrupted Master or Replica row using the verified pristine copy.
6. **Tamper Auditing:** The detection and the repair are appended as new, digitally signed events into the audit chain, ensuring the audit trail survives its own fix.

---

## 5-Stage Real-Time Cyber-Protection Pipeline

Every investment passes through an ordered chain of independent evaluators before any money moves:

1. **Behavior Engine:** Evaluates velocity bursts, amount deviations against personal 30-day baselines, and nocturnal transaction flags (11 PM – 5 AM IST).
2. **Fraud ML Engine:** An XGBoost gradient-boosted classifier evaluated on 22 engineered behavioural features, producing fraud probabilities with SHAP attribution.
3. **Zero-Day Novelty Detector:** An 8 KB PyTorch autoencoder trained on normal user embedding distributions to detect unseen attack vectors via reconstruction loss.
4. **Risk Engine:** Fuses ML scores, behavioural flags, hardware trust (120-day fingerprint, jailbreak/root checks), and SIM indicators into a composite 0–100 risk score.
5. **Decision Engine:** Enforces deterministic decision bands:
   - **`ALLOW` (Score < 35):** Silent approval for routine investments.
   - **`WARN` (Score 35–54):** In-app cautionary prompt.
   - **`CHALLENGE` (Score 55–79):** Contextual step-up verification.
   - **`BLOCK` (Score ≥ 80):** Immediate cancellation; zero funds debited.

### Adaptive Challenge Matrix

| Trigger | Challenge Plan |
|---|---|
| Unknown / Unregistered Device | Security Question $\rightarrow$ OTP |
| Large Amount Deviation | MPIN $\rightarrow$ OTP |
| High Velocity / Distress Signal | OTP Re-confirmation |
| Nocturnal / Unusual Timing | Acknowledge $\rightarrow$ MPIN |

*Three failed attempts cancel the transaction. If the customer reports fraud ("This wasn't me"), the system records a `CUSTOMER_REPORTED_FRAUD` audit event and freezes the session.*

---

## Ethical Wealth Intelligence

Built strictly around customer financial well-being rather than product sales commissions:
- **No Speculative Assets:** Whitelist strictly limited to vetted Mutual Fund categories (Liquid, Debt, Index, Large Cap, Balanced). Absolutely no stock tips, intraday trading, or guaranteed return claims.
- **Empirical Financial Frameworks:** Enforces Virginia Tech 4-month emergency liquidity minimums, the 50/30/20 budgeting rule, and RBI Debt-to-Income (DTI) ceilings.
- **Fraud-Gated Suppression:** If real-time fraud probability exceeds **0.70**, all wealth and investment recommendations are **fully suppressed** to protect compromised accounts.

---

## Multilingual Plain-Language Explainability

Customers are never left with opaque error codes. Seven dedicated explanation engines translate raw model outputs into plain, actionable language:
- **Engines:** Wealth Recommendations, Fraud Alerts, Decision Justifications, Challenge Demands, Unknown Risk Explanations, Device Trust Status, and Phishing Analysis.
- **Runtime:** Locally hosted Llama 3 via Ollama with deterministic template fallbacks so the app never fails if the model is unreachable.
- **Full Trilingual Parity:** Available across **English**, **हिन्दी (Hindi)**, and **ਪੰਜਾਬੀ (Punjabi)** with verified 260-key parity.
- **Safety Guardrail:** The language model sits strictly outside the security-critical path and cannot alter transaction outcomes; an anti-contradiction guardrail automatically rejects explanations that disagree with the underlying engine verdict.

---

## System Structure

```
securewealth-twin/
├── backend/
│   ├── ai/                    # XGBoost fraud engine, PyTorch zero-day detector, LLM explainers
│   ├── aggregation/           # Consent-based Account Aggregator service & net worth calculators
│   ├── api/                   # 90 FastAPI route endpoints (auth, accounts, wealth, audit, security)
│   ├── audit/                 # Hash chaining, Ed25519 signing, replica consensus & self-healing
│   ├── core/                  # Configuration, security dependencies, custom exceptions, logging
│   ├── database/              # PostgreSQL connection & repository patterns
│   ├── keys/                  # Ed25519 keypair for cryptographic audit signing
│   ├── models/                # SQLAlchemy ORM models (AuditLog, AuditReplica, Transaction, User)
│   ├── schemas/               # Pydantic v2 validation contracts
│   ├── scripts/               # Attack simulator, smoke tests, seeding, key generation
│   ├── security/              # Risk engine, behavior rules, challenge engine, decision engine
│   └── services/              # Pipeline orchestration, transaction management, red team engine
├── frontend/                  # React Native / Expo client (14 screens, trilingual i18n, accessible)
├── admin-dashboard/           # Standalone Web Console (Punjab & Sind Bank palette, Red Team suite)
└── demo/                      # Architecture blueprints, video script, reference deck
```

---

## Quickstart Setup

### 1. Backend Service

```bash
cd backend
python -m venv venv && source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Apply database migrations & seed demo dataset
alembic upgrade head
python scripts/seed_demo.py --reset-audit

# Launch FastAPI server
uvicorn main:app --reload
```
API Documentation will be live at `http://127.0.0.1:8000/docs`.

**Demo Credentials:**
- SecureWealth ID: `SW10000001`
- MPIN: `123456`
*(Seed includes ₹3,70,000 in savings, ₹3,00,000 FD, home loan, 120-day trusted device, behavioral profile, and 10 baseline SIP records).*

### 2. Admin Dashboard (Web)

```bash
cd admin-dashboard
python -m http.server 3001
```
Open `http://localhost:3001` in your browser.  
Default Admin Key: `securewealth-admin-2026`.

### 3. Mobile App (Expo / React Native)

```bash
cd frontend
npm install

# Configure API host in src/api/config.ts to your local server
npx expo start
```

---

## Verification & Adversarial Testing

SecureWealth Twin was tested against automated contract suites and 10 live red-team attack scenarios:

```bash
cd backend

# Run the complete backend integration journey
bash scripts/smoke_test.sh

# Run the multi-phase audit tamper & self-healing verification suite (34/34 tests)
python scripts/audit_phase_test.py

# Execute a live insider attack on the database
python scripts/attack_sim.py --target master

# Run the Admin Dashboard & Red Team test harness
bash scripts/dashboard_test.sh
```

Frontend verification:
```bash
node frontend/scripts/i18n_check.js     # 260 keys verified across EN, HI, PA
node frontend/scripts/a11y_check.js     # 100% accessible icon-only controls
```

---

## License & Intellectual Property

**Copyright © 2026 Swayam Kohli. All rights reserved.**

This project was developed for the Punjab & Sind Bank (PSB) Hackathon 2026. This repository is published strictly for evaluation, recruiter review, and technical demonstration purposes. **No permission is granted to copy, reproduce, modify, distribute, sublicense, or use this codebase or its architecture for any commercial or non-commercial purposes without express written permission.**
