"""
Banking Phishing Rule Engine
=============================
Layer 1 of the phishing detection pipeline.

Output:
    phishing_score  : float 0.0–1.0
    fired_signals   : list of signal names
    detected_keywords: dict of signal → matched keywords/patterns
    risk_level      : str  HIGH / MEDIUM / LOW / SAFE
"""

import re
import math
from dataclasses import dataclass, field
import unicodedata
from typing import Optional



SIGNALS: dict[str, dict] = {

    # ── PSYCHOLOGICAL LAYER ───────────────────────────────────────────────────

    "account_suspension_threat": {
        "group": "psychological",
        "weight": 0.60,
        "keywords": [
            "suspended", "suspension", "blocked", "deactivated",
            "terminated", "frozen", "disabled", "de-activated",
            "inactivated", "deactivate", "block your account","freezed"
        ],
        "phrases": [
            "account will be suspended", "account has been suspended",
            "account will be blocked", "account has been blocked",
            "account will be closed", "account will be frozen",
            "account will be deactivated", "permanently blocked",
            "temporarily suspended", "account will be terminated",
            "account will be disabled", "services will be suspended",
            "account will be freezeded", "services will be freezed",
            "account suspended due", "your account is at risk",
        ],
        "patterns": [
            re.compile(r'account\s+(will\s+be|has\s+been|is\s+being)\s+(suspend|block|close|freez|terminat|disabl)', re.I),
        ],
    },

    "unusual_activity_claim": {
        "group": "psychological",
        "weight": 0.30,
        "keywords": [
            "unusual", "suspicious", "unauthorized", "unauthorised",
            "unrecognised", "unrecognized", "anomaly", "irregular",
            "flagged", "anomalous", "suspicious login", "suspect",
        ],
        "phrases": [
            "suspicious activity", "unusual activity detected",
            "unauthorized access", "unrecognised login",
            "your account has been flagged", "irregular transaction",
            "suspicious transaction detected", "unusual login attempt",
            "anomalous activity", "suspicious behaviour detected",
            "we detected unusual", "suspicious sign-in",
        ],
        "patterns": [
            re.compile(r'(unusual|suspicious|unauthorized|unauthorised|anomal)\s+(activity|access|login|transaction|sign.?in)', re.I),
        ],
    },

    "access_restriction_threat": {
        "group": "psychological",
        "weight": 0.25,
        "keywords": [
            "restricted", "locked", "inaccessible", "revoked",
            "barred", "access denied", "login disabled",
            "net banking locked", "internet banking restricted",
        ],
        "phrases": [
            "access restricted", "access has been limited",
            "access will be revoked", "login has been locked",
            "services have been suspended", "net banking restricted",
            "internet banking access blocked", "access to your account restricted",
            "unable to access your account", "your access has been",
        ],
        "patterns": [
            re.compile(r'(access|login|net.?banking)\s+(restricted|locked|revoked|blocked|disabled)', re.I),
        ],
    },

    "time_deadline_pressure": {
        "group": "psychological",
        "weight": 0.40,
        "keywords": [
            "immediately", "urgent", "urgently", "instantly",
            "expires", "expiring", "deadline", "last chance",
            "hurry", "asap", "right now", "do not delay",
            "without delay", "at once", "no later than",
            # Indian English urgency variants
            "do the needful", "at the earliest", "kindly revert",
            "please action", "kindly action", "kindly expedite",
            "without further delay", "as a matter of urgency",
            "on priority", "on an urgent basis", "at your earliest",
            "lose no time", "right away", "straight away",
            "without wasting time", "do not wait", "don't wait",
            "be quick", "hurry up", "act fast",
        ],
        "phrases": [
            "act immediately", "respond within 24 hours",
            "expires today", "valid for limited time",
            "must be done today", "failure to respond",
            "within the next 24 hours", "within 2 hours",
            "within 48 hours", "last chance to verify",
            "time is running out", "do not ignore this",
            "respond before", "before it expires",
            "limited time remaining", "act within",
            "do the needful immediately", "kindly do the needful",
            "please action this immediately", "action required urgently",
            "kindly revert at the earliest", "services will cease",
            "your services will be stopped",
        ],
        "patterns": [
            re.compile(r'within\s+\d+\s+(hour|minute|day)', re.I),
            re.compile(r'(expire|expir)\s*(s|d|ing)?\s*(today|tomorrow|soon|shortly)', re.I),
            re.compile(r'(respond|verify|update|confirm)\s+(immediately|now|urgently|instantly)', re.I),
            re.compile(r'(do|complete|finish)\s+(the\s+)?needful', re.I),
            re.compile(r'at\s+(the\s+)?earliest', re.I),
            re.compile(r'(services?|account)\s+will\s+(cease|stop|end|terminate)', re.I),
        ],
    },

    "last_warning_claim": {
        "group": "psychological",
        "weight": 0.50,
        "keywords": [
            "last warning", "final notice", "final warning",
            "last reminder", "last opportunity", "final reminder",
            "last and final", "final alert", "last alert",
            "this is your last", "final intimation",
        ],
        "phrases": [
            "this is your last warning", "final notice",
            "last and final reminder", "last opportunity to verify",
            "final warning before", "last chance before",
            "this is a final notice", "final intimation before",
        ],
        "patterns": [
            re.compile(r'(last|final)\s+(warning|notice|reminder|alert|chance|opportunity|intimation)', re.I),
        ],
    },

    "immediate_action_demand": {
        "group": "psychological",
        "weight": 0.40,
        "keywords": [
            "click now", "verify now", "update now", "confirm now",
            "act now", "call now", "respond now", "login now",
            "click here to verify", "click to confirm",
            "tap here", "tap to verify", "tap to confirm",
        ],
        "phrases": [
            "click here to verify", "verify your account now",
            "update immediately", "confirm your details now",
            "take action now", "click to confirm identity",
            "tap to verify now", "login immediately to verify",
            "visit the link immediately", "open the link now",
        ],
        "patterns": [
            re.compile(r'(click|tap|visit|open)\s+(here|now|link|below)\s+(to\s+)?(verify|confirm|update|login|secure)', re.I),
            re.compile(r'(verify|confirm|update|secure)\s+(your\s+)?(account|details|identity)\s+now', re.I),
        ],
    },

    "guilt_induction": {
        "group": "psychological",
        "weight": 0.25,
        "keywords": [
            "your fault", "you caused", "due to your",
            "initiated from your", "from your device",
            "your activity", "complaint filed against",
            "reported against your", "registered against",
            "complaint against your upi", "case registered",
        ],
        "phrases": [
            "suspicious activity from your device",
            "transaction initiated from your account",
            "complaint has been filed against your",
            "your account was used for",
            "fraud reported against your upi",
            "case registered against your account",
            "criminal complaint against your pan",
            "fir filed against your number",
        ],
        "patterns": [
            re.compile(r'(complaint|case|fir|report)\s+(filed|registered|lodged)\s+against\s+your', re.I),
            re.compile(r'(activity|transaction|access)\s+(from|initiated\s+from|detected\s+from)\s+your\s+(device|account|number)', re.I),
        ],
    },

    # ── AUTHORITY LAYER ───────────────────────────────────────────────────────

    "bank_impersonation": {
        "group": "authority",
        "weight": 0.15,  # low alone — must combine with other signals
        "keywords": [
            "sbi alert", "sbi bank", "sbi customer",
            "hdfc alert", "hdfc bank alert", "hdfc security",
            "icici alert", "icici bank alert", "icici security",
            "axis bank alert", "kotak bank alert", "pnb alert",
            "bob alert", "canara bank alert", "yes bank alert",
            "idbi bank alert", "indusind alert", "union bank alert",
            "bank of baroda alert", "bank of india alert",
        ],
        "phrases": [
            "sbi customer care", "hdfc bank security team",
            "icici bank security", "your bank has detected",
            "bank of india notification", "from sbi",
            "from hdfc bank", "from icici bank",
            "this is sbi", "this is hdfc",
        ],
        "patterns": [
            re.compile(r'(sbi|hdfc|icici|axis|kotak|pnb|bob|canara|idbi|indusind)\s*(bank)?\s*(alert|security|notification|warning|notice)', re.I),
        ],
    },
  

    "rbi_impersonation": {
        "group": "authority",
        "weight": 0.35,
        "keywords": [
            "rbi", "reserve bank of india", "reserve bank",
            "rbi notification", "rbi alert", "rbi circular",
            "rbi guidelines", "rbi mandate", "rbi directive",
            "rbi notice", "rbi order", "rbi instruction",
        ],
        "phrases": [
            "as per rbi guidelines", "rbi has instructed",
            "rbi notification for your account", "reserve bank of india alert",
            "rbi has mandated", "rbi circular notification",
            "rbi has directed all banks", "as per rbi mandate",
            "rbi compliance required", "rbi has issued notice",
        ],
        "patterns": [
            re.compile(r'rbi\s+(has|alert|notice|circular|guideline|mandate|directive|notification|instruction)', re.I),
            re.compile(r'reserve\s+bank\s+of\s+india\s+(alert|notice|circular|notification)', re.I),
        ],
    },

    "government_body_impersonation": {
        "group": "authority",
        "weight": 0.35,
        "keywords": [
            "income tax department", "it department",
            "cybercrime department", "cyber cell",
            "enforcement directorate", "government of india", 
            "ministry of finance",
        ],
        "phrases": [
            "income tax department notice", "cybercrime department alert",
            "enforcement directorate has flagged", "government has flagged your account",
            "as per pmla act", "ministry of finance directive",
            "central government notice", "fiu has flagged",
            "sebi has flagged your account", "cbi has registered",
        ],
        "patterns": [
            re.compile(r'\b(ed|sebi|cbi|nia)\s+notice\b', re.I),
            re.compile(r'\b(pmla|fiu-ind)\b', re.I),
            re.compile(r'(income\s+tax|cybercrime|enforcement\s+directorate|cyber\s+cell)\s+(department|notice|alert|warning)', re.I),
            re.compile(r'(government|govt|ministry|central\s+govt)\s+(of\s+india)?\s*(notice|alert|directive|order)', re.I),
        ],
    },

    "pan_request": {
        "group": "credential",
        "weight": 0.35,
        "keywords": [
            "pan card", "pan number", "pan details",
            "permanent account number", "pan verification",
            "share pan", "provide pan", "enter pan",
            "submit pan", "pan linked",
        ],
        "phrases": [
            "share your pan number", "provide pan card details",
            "pan verification required", "enter your pan to proceed",
            "submit pan card", "link your pan", "pan card details needed",
            "link pan to account",
        ],
        "patterns": [
            re.compile(r'[A-Z]{5}[0-9]{4}[A-Z]{1}'),
            re.compile(r'(share|provide|enter|submit|link)\s+(your\s+)?pan', re.I),
            re.compile(r'pan\s+(number|card|details|verification|required|linked)', re.I),
            re.compile(r'pan\s+(is\s+)?(not\s+)?(linked|updated|verified)', re.I),
        ],
    },
    "payment_network_impersonation": {
        "group": "authority",
        "weight": 0.30,
        "keywords": [
            "npci", "upi alert", "visa security",
            "mastercard alert", "rupay alert", "bhim upi",
            "neft system", "imps system", "npci notification",
            "visa notification", "mastercard security",
        ],
        "phrases": [
            "npci has flagged", "upi system alert",
            "visa security notification", "rupay card alert",
            "bhim upi notification", "npci compliance",
            "upi network alert", "payment network security",
            "npci has blocked", "rupay security notice",
        ],
        "patterns": [
            re.compile(r'(npci|visa|mastercard|rupay|bhim)\s*(upi)?\s*(alert|notification|security|notice|warning|flagged)', re.I),
        ],
    },

    "kyc_expiry_claim": {
        "group": "authority",
        "weight": 0.25,
        "keywords": [
            "kyc expired", "kyc expiry", "kyc pending",
            "kyc update", "kyc verification", "kyc incomplete",
            "kyc not done", "kyc required", "re-kyc",
            "ekyc", "kyc status", "kyc lapsed",
            "kyc due", "kyc overdue",
        ],
        "phrases": [
            "your kyc has expired", "kyc update required",
            "complete your kyc immediately", "account will be blocked due to kyc",
            "kyc pending since", "re-kyc mandatory",
            "kyc verification incomplete", "kyc not updated",
            "kyc expiry notice", "kyc lapsed for your account",
            "update kyc to avoid", "kyc due for your account",
        ],
        "patterns": [
            re.compile(r'kyc\s+(expired|pending|incomplete|required|update|verification|lapsed|due)', re.I),
            re.compile(r'(complete|update|verify|submit)\s+(your\s+)?kyc', re.I),
        ],
    },

    "rbi_guideline_invoke": {
        "group": "authority",
        "weight": 0.30,
        "keywords": [
            "as per rbi", "rbi circular", "rbi mandate",
            "rbi regulation", "rbi compliance", "rbi norms",
            "as per guidelines", "regulatory requirement",
            "compliance required", "mandatory as per",
            "statutory requirement", "regulatory compliance",
            "banking regulation", "as per notification",
        ],
        "phrases": [
            "as per rbi circular", "mandatory as per rbi guidelines",
            "regulatory compliance required", "as per government directive",
            "as per banking regulations", "as per rbi notification",
            "statutory compliance notice", "as per rbi norms",
            "mandatory regulatory requirement", "as per banking act",
        ],
        "patterns": [
            re.compile(r'as\s+per\s+(rbi|government|banking|regulatory|statutory)\s+(circular|guideline|notification|mandate|regulation|directive|norms)', re.I),
            re.compile(r'(mandatory|compulsory|statutory)\s+(as\s+per|under|compliance|requirement)', re.I),
        ],
    },

    "document_verification_request": {
        "group": "authority",
        "weight": 0.30,
        "keywords": [
            "submit documents", "upload documents",
            "send documents", "provide documents",
            "document verification", "id proof required",
            "address proof", "verification documents",
            "upload id", "submit proof", "send proof",
        ],
        "phrases": [
            "submit your documents", "upload your id proof",
            "send a copy of your aadhaar", "document verification pending",
            "provide proof of address", "upload verification documents",
            "send id proof immediately", "submit address proof",
            "identity verification pending", "document submission required",
        ],
        "patterns": [
            re.compile(r'(submit|upload|send|provide)\s+(your\s+)?(documents?|id\s+proof|address\s+proof|verification)', re.I),
        ],
    },

    # ── CREDENTIAL LAYER ──────────────────────────────────────────────────────

    "otp_request": {
        "group": "credential",
        "weight": 0.50,
        "keywords": [
            "share otp", "enter otp", "provide otp",
            "give otp", "send otp", "confirm otp",
            "disclose otp", "otp required", "submit otp",
            "otp verification", "enter the otp", "type otp",
        ],
        "phrases": [
            "share your otp", "enter the otp",
            "provide otp to verify", "give otp to our agent",
            "submit otp to confirm", "otp is required",
            "enter otp to proceed", "confirm with otp",
            "share one time password", "provide one time password",
        ],
        "patterns": [
            re.compile(r'(share|enter|provide|give|send|confirm|submit|disclose|type)\s+(your\s+)?otp', re.I),
            re.compile(r'otp\s+(is|required|needed|mandatory)\s*(to|for)?', re.I),
            re.compile(r'\b\d{4,8}\b.*otp|otp.*\b\d{4,8}\b', re.I),
        ],
    },

    "pin_request": {
        "group": "credential",
        "weight": 0.60,
        "keywords": [
            "share pin", "enter pin", "confirm pin",
            "provide pin", "give pin", "atm pin",
            "debit card pin", "credit card pin",
            "your pin", "submit pin", "disclose pin",
        ],
        "phrases": [
            "share your atm pin", "confirm your debit card pin",
            "enter your pin to verify", "provide pin to our executive",
            "give your pin number", "submit your pin",
            "enter pin to proceed", "confirm with your pin",
        ],
        "patterns": [
            re.compile(r'(share|enter|provide|give|confirm|submit|disclose)\s+(your\s+)?(atm\s+)?pin', re.I),
        ],
    },

    "card_details_request": {
        "group": "credential",
        "weight": 0.60,
        "keywords": [
            "card number", "cvv", "expiry date", "card details",
            "16 digit", "card verification", "debit card number",
            "credit card number", "card information",
            "card data", "card credentials", "card expiry",
        ],
        "phrases": [
            "share your card number", "enter your cvv",
            "provide card details", "16 digit card number",
            "card expiry date", "enter card information",
            "provide your card credentials", "submit card details",
            "enter debit card number", "provide credit card number",
        ],
        "patterns": [
            re.compile(r'\b\d{16}\b'),
            re.compile(r'\bcvv\b', re.I),
            re.compile(r'card\s+(number|details|expiry|verification|information|data|credentials)', re.I),
            re.compile(r'(share|enter|provide|submit)\s+(your\s+)?(debit|credit)?\s*card', re.I),
        ],
    },

    "password_request": {
        "group": "credential",
        "weight": 0.60,
        "keywords": [
            "net banking password", "login password",
            "internet banking password", "ipin", "mpin",
            "share password", "provide password",
            "enter password", "banking password",
            "your password", "confirm password",
        ],
        "phrases": [
            "share your password", "provide your net banking password",
            "enter your mpin", "confirm your ipin",
            "reset your password via this link",
            "your net banking password", "enter internet banking password",
            "login with your password", "confirm with your mpin",
        ],
        "patterns": [
            re.compile(r'(share|provide|enter|confirm|submit)\s+(your\s+)?(net\s+banking\s+|internet\s+banking\s+|login\s+)?password', re.I),
            re.compile(r'\b(ipin|mpin)\b', re.I),
        ],
    },

    "aadhaar_request": {
        "group": "credential",
        "weight": 0.40,
        "keywords": [
            "aadhaar number", "aadhar number", "aadhaar card",
            "uidai", "share aadhaar", "provide aadhaar",
            "enter aadhaar", "aadhaar verification",
            "12 digit aadhaar", "masked aadhaar",
        ],
        "phrases": [
            "share your aadhaar number", "provide your 12 digit aadhaar",
            "aadhaar verification required", "enter aadhaar to verify identity",
            "submit aadhaar number", "aadhaar card details required",
            "link aadhaar to your account", "aadhaar otp verification",
        ],
        "patterns": [
            re.compile(r'\b\d{12}\b'),
            re.compile(r'(share|provide|enter|submit|confirm)\s+(your\s+)?(12\s+digit\s+)?aadhaar', re.I),
            re.compile(r'aadhaar\s+(number|card|verification|details|required)', re.I),
        ],
    },

    "pan_request": {
        "group": "credential",
        "weight": 0.35,
        "keywords": [
            "pan card", "pan number", "pan details",
            "permanent account number", "pan verification",
            "share pan", "provide pan", "enter pan",
            "submit pan", "pan linked",
        ],
        "phrases": [
            "share your pan number", "provide pan card details",
            "pan verification required", "enter your pan to proceed",
            "submit pan card", "link your pan", "pan card details needed",
            "pan not linked", "link pan to account",
        ],
        "patterns": [
            re.compile(r'[A-Z]{5}[0-9]{4}[A-Z]{1}'),
            re.compile(r'(share|provide|enter|submit|link)\s+(your\s+)?pan', re.I),
            re.compile(r'pan\s+(number|card|details|verification|required|linked)', re.I),
        ],
    },

    # ── GREED LAYER ───────────────────────────────────────────────────────────

    "lottery_win_claim": {
        "group": "greed",
        "weight": 0.30,
        "keywords": [
            "you have won", "winner", "winning", "lottery",
            "prize", "lucky winner", "selected winner",
            "cash prize", "congratulations you", "prize money",
            "bumper prize", "jackpot winner",
        ],
        "phrases": [
            "you have won", "lucky winner selected",
            "cash prize of rs", "lottery prize pending",
            "you are the winner", "congratulations you have won",
            "prize money waiting", "claim your prize",
            "you have been selected as winner",
        ],
        "patterns": [
            re.compile(r'(you\s+have\s+won|you\s+are\s+(a\s+)?winner|lucky\s+winner)', re.I),
            re.compile(r'(prize|lottery|jackpot)\s+(of\s+)?(rs\.?|inr|₹)?\s*[\d,]+', re.I),
        ],
    },

    "cashback_lure": {
        "group": "greed",
        "weight": 0.30,
        "keywords": [
            "cashback", "cash back", "bonus credited",
            "surprise credit", "special credit", "amount credited",
            "money credited", "refund credited", "exclusive cashback",
            "instant cashback", "guaranteed cashback",
        ],
        "phrases": [
            "cashback of rs", "special cashback for you",
            "your cashback is ready", "claim your cashback",
            "bonus amount credited", "surprise cashback",
            "instant cashback credited", "exclusive cashback offer",
            "cashback waiting to be claimed",
        ],
        "patterns": [
            re.compile(r'cashback\s+(of\s+)?(rs\.?|inr|₹)?\s*[\d,]+', re.I),
            re.compile(r'(rs\.?|inr|₹)\s*[\d,]+\s+cashback', re.I),
        ],
    },

    "reward_expiry_pressure": {
        "group": "greed",
        "weight": 0.20,
        "keywords": [
            "reward points", "points expiring", "rewards expiring",
            "loyalty points", "bonus points", "points lapse",
            "redeem now", "points will expire", "points expiry",
            "reward expiry", "rewards lapse",
        ],
        "phrases": [
            "your reward points are expiring", "redeem before they expire",
            "points will lapse on", "claim your rewards now",
            "rewards expiring today", "loyalty points expiring",
            "bonus points about to expire", "redeem before expiry",
            "your points will expire", "reward points lapsing",
        ],
        "patterns": [
            re.compile(r'(reward|loyalty|bonus)\s+points?\s+(expir|laps)', re.I),
            re.compile(r'points?\s+(will\s+)?(expir|laps)', re.I),
        ],
    },

    "lucky_draw_claim": {
        "group": "greed",
        "weight": 0.25,
        "keywords": [
            "lucky draw", "bumper prize", "special draw",
            "festive draw", "annual draw", "grand prize",
            "mega prize", "jackpot", "selected for prize",
            "draw winner", "prize draw",
        ],
        "phrases": [
            "lucky draw winner", "bumper prize of rs",
            "selected in our lucky draw", "grand prize winner",
            "festive lucky draw", "annual lucky draw",
            "mega prize winner", "you won our lucky draw",
            "selected for bumper prize",
        ],
        "patterns": [
            re.compile(r'lucky\s+draw\s+(winner|prize|selected)', re.I),
            re.compile(r'(bumper|grand|mega|special)\s+prize', re.I),
        ],
    },

    # ── TRANSACTION LAYER ─────────────────────────────────────────────────────

    "failed_transaction_claim": {
        "group": "transaction",
        "weight": 0.15,
        "keywords": [
            "transaction failed", "payment failed", "transfer failed",
            "neft failed", "imps failed", "upi failed",
            "transaction unsuccessful", "payment unsuccessful",
            "transfer unsuccessful", "transaction declined",
            "payment declined",
        ],
        "phrases": [
            "your transaction has failed", "payment could not be processed",
            "neft transfer failed", "upi payment failed",
            "transaction was unsuccessful", "imps transfer failed",
            "your payment has failed", "transfer declined",
            "transaction could not be completed",
        ],
        "patterns": [
            re.compile(r'(transaction|payment|transfer|neft|imps|upi)\s+(has\s+)?(failed|unsuccessful|declined|rejected)', re.I),
        ],
    },
  "payment_request": {
    "group": "transaction",
    "weight": 0.50,
    "keywords": [
        "pay", "payment", "send money", "transfer money",
        "deposit", "make payment", "proceed payment",
        "registration fee", "processing fee", "service charge",
        "verification fee", "activation fee", "joining fee",
        "security deposit", "advance payment", "token amount",
        "booking amount", "application fee",
        "pay now", "send now", "transfer now","send","verification"
    ],
    "phrases": [
        "pay rs", "send","send rs", "transfer rs",
        "pay inr", "send inr", "transfer inr",
        "payment required to proceed",
        "complete payment to continue",
        "pay to activate your account",
        "pay to verify your account",
        "pay to unlock your account",
        "payment needed for verification",
        "complete your verficitaion"
        "payment required for processing",
        "transfer amount to confirm",
        "send amount to receive",
        "registration fee required",
        "pay registration fee",
        "application fee required",
        "pay to get job",
        "pay for interview process"
    ],
    "patterns": [
        re.compile(r'(pay|send|transfer|deposit)\s+(rs\.?|inr|₹)?\s*[\d,]+', re.I),
        re.compile(r'(fee|charge|amount)\s+(of\s+)?(rs\.?|inr|₹)?\s*[\d,]+', re.I),
        re.compile(r'(payment|amount)\s+(required|needed|necessary)\s+(to|for)', re.I),
        re.compile(r'(to\s+(proceed|continue|complete|process)).*(pay|transfer|send)', re.I),
    ]
},

    "pending_approval_request": {
        "group": "transaction",
        "weight": 0.25,
        "keywords": [
            "pending approval", "awaiting approval",
            "approval required", "pending confirmation",
            "confirm to proceed", "approve transaction",
            "pending your action", "action required",
            "pending authorization",
        ],
        "phrases": [
            "transaction pending your approval", "click to approve",
            "awaiting your confirmation", "pending action required",
            "approve this transaction", "authorization pending",
            "transaction requires your approval", "confirm to complete transaction",
            "pending your authorization",
        ],
        "patterns": [
            re.compile(r'(transaction|payment|transfer)\s+(pending|awaiting)\s+(your\s+)?(approval|confirmation|authorization)', re.I),
            re.compile(r'(approve|confirm|authorize)\s+(this\s+)?(transaction|payment|transfer)', re.I),
        ],
    },

    "unauthorized_transaction_claim": {
        "group": "transaction",
        "weight": 0.20,
        "keywords": [
            "unauthorized transaction", "unauthorised transaction",
            "fraudulent transaction", "fraud transaction",
            "unknown transaction", "unrecognised transaction",
            "not initiated by you", "not done by you",
            "unexpected debit", "unknown debit",
        ],
        "phrases": [
            "unauthorized transaction detected", "fraudulent transaction on your account",
            "transaction not initiated by you", "unknown debit on your account",
            "if not done by you", "if not initiated by you",
            "unauthorised debit detected", "unknown transaction on your account",
            "fraud transaction detected", "unexpected transaction detected",
        ],
        "patterns": [
            re.compile(r'(unauthorized|unauthorised|fraudulent|unknown|unrecognised)\s+(transaction|debit|transfer|payment)', re.I),
            re.compile(r'(not\s+initiated|not\s+done|not\s+made)\s+by\s+you', re.I),
        ],
    },

    "emi_bounce_threat": {
        "group": "transaction",
        "weight": 0.30,
        "keywords": [
            "emi bounced", "emi failed", "emi due",
            "emi overdue", "loan emi", "bounce charge",
            "emi not paid", "missed emi", "emi default",
            "emi pending", "emi payment failed",
        ],
        "phrases": [
            "your emi has bounced", "emi payment failed",
            "loan emi overdue", "bounce charges applied",
            "emi default notice", "missed emi payment",
            "emi not received", "emi bounce charge levied",
            "your emi is pending",
        ],
        "patterns": [
            re.compile(r'emi\s+(bounced|failed|overdue|pending|default|not\s+paid|missed)', re.I),
            re.compile(r'(loan|emi)\s+(bounce|default|overdue)', re.I),
        ],
    },

    # ── TECHNICAL LAYER ───────────────────────────────────────────────────────

    "shortened_url": {
        "group": "technical",
        "weight": 0.30,
        "keywords": [],
        "phrases": [],
        "patterns": [
            re.compile(r'bit\.ly', re.I),
            re.compile(r'tinyurl\.com', re.I),
            re.compile(r'goo\.gl', re.I),
            re.compile(r't\.co/', re.I),
            re.compile(r'ow\.ly', re.I),
            re.compile(r'rb\.gy', re.I),
            re.compile(r'cutt\.ly', re.I),
            re.compile(r'tiny\.cc', re.I),
            re.compile(r'short\.url', re.I),
            re.compile(r'is\.gd', re.I),
            re.compile(r'clck\.ru', re.I),
            re.compile(r'shorturl\.at', re.I),
        ],
    },

    "http_link": {
        "group": "technical",
        "weight": 0.20,
        "keywords": [],
        "phrases": [],
        "patterns": [
            re.compile(r'http://(?!https)', re.I),
        ],
    },

    "ip_address_url": {
        "group": "technical",
        "weight": 0.40,
        "keywords": [],
        "phrases": [],
        "patterns": [
            re.compile(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
        ],
    },

    "domain_squatting": {
        "group": "technical",
        "weight": 0.35,
        "keywords": [],
        "phrases": [],
        "patterns": [
            re.compile(r'sbi[\-\.][a-z0-9]+\.(com|in|net|org)', re.I),
            re.compile(r'hdfc[\-\.][a-z0-9]+\.(com|in|net|org)', re.I),
            re.compile(r'icici[\-\.][a-z0-9]+\.(com|in|net|org)', re.I),
            re.compile(r'rbi[\-\.][a-z0-9]+\.(com|in|net|org)', re.I),
            re.compile(r'axis[\-\.][a-z0-9]+\.(com|in|net|org)', re.I),
            re.compile(r'kotak[\-\.][a-z0-9]+\.(com|in|net|org)', re.I),
            re.compile(r'\.(tk|ml|ga|cf|gq|xyz|top|club|work|site|online)\b', re.I),
            re.compile(r'(secure|login|verify|update|alert|bank)[\-\.](sbi|hdfc|icici|rbi|axis)', re.I),
        ],
    },

    "fake_app_download": {
        "group": "technical",
        "weight": 0.30,
        "keywords": [
            "download app", "install app", "download now",
            "click to download", "get the app", "install now",
            "new version available", "update your app",
            "download our app", "install our app",
            "apk", "banking apk", "mobile apk" 
        ],
        "phrases": [
            "download our updated app", "install the new banking app",
            "click to download", "get the latest version",
            "new version of our app", "download from this link",
            "install banking app", "update your banking app now",
        ],
        "patterns": [
            re.compile(r'(download|install)\s+(our|the|new|updated)?\s*(banking|sbi|hdfc|icici)?\s*app', re.I),
            re.compile(r'(download|install)\s+.*\s+(now|immediately|here)', re.I),
        ],
    },

    "apk_sideload_request": {
        "group": "technical",
        "weight": 0.45,
        "keywords": [
            "apk file", "download apk", "install apk",
            "enable unknown sources", "allow installation",
            "sideload", "outside play store", "direct download",
        ],
        "phrases": [
            "download this apk", "install the apk file",
            "enable unknown sources to install",
            "allow apps from unknown sources",
            "download directly from this link",
            "install outside play store",
        ],
        "patterns": [
            re.compile(r'\.apk\b', re.I),
            re.compile(r'(download|install)\s+apk', re.I),
            re.compile(r'unknown\s+sources', re.I),
            re.compile(r'drive\.google\.com.*apk', re.I),
        ],
    },

    "sms_sender_id_spoofing": {
        "group": "technical",
        "weight": 0.35,
        "keywords": [],
        "phrases": [],
        "patterns": [
            re.compile(r'\bSB[1I]INB\b'),
            re.compile(r'\bHDFCB[NM]K\b'),
            re.compile(r'\b[Il1]CICI\b'),
            re.compile(r'\bAX[lI1]SBK\b'),
        ],
    },
    "link_click_request": {
    "group": "technical",
    "weight": 0.25,
    "keywords": [
        "click here", "click the link", "open link",
        "visit link", "tap here", "tap to open",
        "open this link", "click below"
    ],
    "phrases": [
        "click here to verify",
        "click the link below",
        "tap here to continue",
        "open the link to proceed",
        "visit the link to confirm",
        "click to update your account"
    ],
    "patterns": [
        re.compile(r'(click|tap|visit|open).*(link|here|below)', re.I),
    ]
},
"link_with_context_risk": {
    "group": "technical",
    "weight": 0.20,
    "keywords": [
        "important update", "account update",
        "verify your account", "secure your account"
    ],
    "phrases": [
        "important update regarding your account",
        "verify your account using the link",
        "secure your account now",
        "update your details via link"
    ],
    "patterns": [
        re.compile(r'(http|https).*', re.I),
    ]
},

    "callback_number_fraud": {
        "group": "technical",
        "weight": 0.25,
        "keywords": [
            "call now", "call us immediately", "call back",
            "call our agent", "call this number", "helpline number",
            "customer care number", "call our helpline",
            "call immediately", "contact our agent",
        ],
        "phrases": [
            "call our helpline immediately", "contact us at this number",
            "call back on this number", "our agent will call you",
            "call our customer care", "call us for assistance",
            "call immediately to resolve",
        ],
        "patterns": [
            re.compile(r'\b[6-9]\d{9}\b'),
            re.compile(r'call\s+(us|now|back|immediately)\s+(at|on)?\s*[6-9]\d{9}', re.I),
        ],
    },

    # ── BEHAVIOURAL LAYER (context-based) ────────────────────────────────────

    "off_hours_transaction": {
        "group": "behavioural",
        "weight": 0.10,
        "keywords": [],
        "phrases": [],
        "patterns": [],
        "context_key": "transaction_hour",
    },

    "round_amount": {
        "group": "behavioural",
        "weight": 0.10,
        "keywords": [],
        "phrases": [],
        "patterns": [
            re.compile(r'(?:rs\.?|inr|₹)\s*([\d,]+)', re.I),
        ],
        "context_key": "amount",
    },

    "new_recipient": {
        "group": "behavioural",
        "weight": 0.08,
        "keywords": [],
        "phrases": [],
        "patterns": [],
        "context_key": "is_new_recipient",
    },

    "unusual_amount": {
        "group": "behavioural",
        "weight": 0.12,
        "keywords": [],
        "phrases": [],
        "patterns": [],
        "context_key": "amount_vs_average",
    },

    "transaction_velocity": {
        "group": "behavioural",
        "weight": 0.15,
        "keywords": [],
        "phrases": [],
        "patterns": [],
        "context_key": "recent_transaction_count",
    },

    # ── UPI & DIGITAL PAYMENT LAYER ───────────────────────────────────────────

    "upi_collect_request": {
        "group": "upi_digital",
        "weight": 0.35,
        "keywords": [
            "collect request", "upi collect", "accept request",
            "approve request", "upi request received",
            "money request", "payment request received",
            "collect money request", "incoming request",
        ],
        "phrases": [
            "accept this upi collect request", "approve the payment request",
            "upi collect request pending", "money request from unknown",
            "incoming collect request", "approve to receive money",
            "upi request pending approval",
        ],
        "patterns": [
            re.compile(r'(accept|approve)\s+(this\s+)?(upi\s+)?(collect|payment|money)\s+request', re.I),
            re.compile(r'upi\s+(collect|request)\s+(pending|received|incoming)', re.I),
        ],
    },

    "qr_code_scam": {
        "group": "upi_digital",
        "weight": 0.35,
        "keywords": [
            "scan qr", "scan this code", "qr code",
            "scan to receive", "scan to claim",
            "scan to get money", "scan to collect",
            "scan the qr", "qr scan",
        ],
        "phrases": [
            "scan this qr code to receive", "scan to claim your refund",
            "scan qr to get cashback", "scan to collect prize",
            "scan qr code to receive money", "scan to get refund",
            "scan to receive payment", "scan and receive",
        ],
        "patterns": [
            re.compile(r'scan\s+(this\s+)?(qr|code)\s+(to\s+)?(receive|collect|claim|get)', re.I),
            re.compile(r'qr\s+code\s+(to\s+)?(receive|collect|claim)', re.I),
        ],
    },

    "screen_share_request": {
        "group": "upi_digital",
        "weight": 0.50,
        "keywords": [
            "anydesk", "teamviewer", "quicksupport",
            "screen share", "remote access", "screen mirror",
            "share your screen", "install anydesk",
            "remote support", "desktop sharing",
            "airdroid", "mobizen", "remote desktop",
        ],
        "phrases": [
            "install anydesk on your phone", "share your screen with our agent",
            "download teamviewer quicksupport", "allow remote access",
            "screen sharing required", "install remote support app",
            "share screen with executive", "remote access required",
            "install anydesk for assistance",
        ],
        "patterns": [
            re.compile(r'(anydesk|teamviewer|quicksupport|airdroid|mobizen)', re.I),
            re.compile(r'(screen\s+shar|remote\s+access|remote\s+support|desktop\s+shar)', re.I),
        ],
    },

    # ── SOCIAL ENGINEERING LAYER ──────────────────────────────────────────────

    "mass_compliance_claim": {
        "group": "social_engineering",
        "weight": 0.25,
        "keywords": [
            "all customers", "every customer", "most customers",
            "customers have already", "others have verified",
            "join thousands", "millions of customers",
            "all account holders", "all users",
        ],
        "phrases": [
            "millions of customers have updated", "all sbi customers must verify",
            "join thousands who have completed", "every account holder must",
            "all customers are required", "other customers have already",
            "most users have updated", "all users are required to",
        ],
        "patterns": [
            re.compile(r'(all|every|most)\s+(customers?|users?|account\s+holders?)\s+(must|are\s+required|have)', re.I),
            re.compile(r'(millions|thousands)\s+of\s+(customers?|users?)\s+have', re.I),
        ],
    },

    "reciprocity_manipulation": {
        "group": "social_engineering",
        "weight": 0.20,
        "keywords": [
            "we have protected", "we secured",
            "we prevented", "we saved your account",
            "as a goodwill", "goodwill gesture",
            "we have credited", "complimentary",
            "we blocked the fraud", "we stopped",
        ],
        "phrases": [
            "we have protected your account from fraud",
            "as a goodwill gesture we credited",
            "we saved your account from being blocked",
            "complimentary amount added to your account",
            "we have secured your account",
            "we stopped a fraudulent transaction",
        ],
        "patterns": [
            re.compile(r'we\s+have\s+(protected|secured|saved|prevented|blocked|stopped)', re.I),
            re.compile(r'(goodwill|complimentary)\s+(gesture|amount|credit|reward)', re.I),
        ],
    },

    "personalisation_exploit": {
        "group": "social_engineering",
        "weight": 0.10,
        "keywords": [
            "dear customer", "dear valued customer",
            "account ending", "last transaction on",
            "customer since", "premium customer",
        ],
        "phrases": [],
        "patterns": [
            re.compile(r'dear\s+[a-z]{2,}(?!\s+(customer|sir|madam))', re.I),
            re.compile(r'account\s+(ending|no\.?)\s*\d{4}', re.I),
            re.compile(r'customer\s+since\s+\d{4}', re.I),
            re.compile(r'last\s+transaction\s+(on|was)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d)', re.I),
        ],
    },

    "confusion_overload": {
        "group": "social_engineering",
        "weight": 0.20,
        "keywords": [
            "as per section", "circular no", 
            "notification no", "pmla act", "fema act",
            "it act", "under section", "compliance notice",
            "regulatory directive", "statutory notice", "docket number",
        ],
        "phrases": [
            "as per section 12b", "rbi circular no",
            "under pmla act 2002", "as per it act section",
            "statutory compliance required", "regulatory directive no",
            "as per fema guidelines", "under banking regulation act",
            "reference number for your case",
        ],
        "patterns": [
            re.compile(r'(circular|notification|ref|reference|docket)\s*(no\.?|number)\s*[\w\-/]+', re.I),
            re.compile(r'(section|clause)\s+\d+(\([a-z]\))?', re.I),
            re.compile(r'(pmla|fema|it\s+act|banking\s+regulation\s+act)\s*(,\s*\d{4})?', re.I),
        ],
    },

    # ── REFUND & OVERPAYMENT LAYER ────────────────────────────────────────────

    "refund_lure": {
        "group": "refund_overpayment",
        "weight": 0.25,
        "keywords": [
            "refund pending", "refund ready", "refund waiting",
            "tax refund", "itr refund", "tds refund",
            "bill refund", "overpayment refund",
            "refund will be credited", "claim refund",
            "refund of rs", "electricity refund",
        ],
        "phrases": [
            "your refund is pending", "income tax refund waiting",
            "itr refund ready to claim", "electricity bill refund",
            "tds refund pending in your account", "refund of rs is ready",
            "claim your tax refund", "your refund has been approved",
        ],
        "patterns": [
            re.compile(r'refund\s+(of\s+)?(rs\.?|inr|₹)?\s*[\d,]+', re.I),
            re.compile(r'(itr|tds|tax|income\s+tax)\s+refund\s+(pending|ready|waiting|approved)', re.I),
        ],
    },
    "reverse_payment_trap": {
    "group": "refund_overpayment",
    "weight": 0.40,
    "keywords": [
        "pay to receive", "send to receive", "transfer to receive",
        "pay to get refund", "send to claim refund",
        "transfer to get cashback", "pay to unlock reward"
    ],
    "phrases": [
        "send money to receive refund",
        "pay to claim your refund",
        "transfer amount to receive cashback",
        "send payment to get reward",
        "pay first to receive amount",
        "transfer to unlock cashback",
        "send amount to claim prize",
        "refund processed"
    ],
    "patterns": [
        re.compile(r'(receive|get|claim).*(pay|send|transfer)', re.I),
        re.compile(r'(pay|send|transfer).*(receive|get|refund|cashback|reward)', re.I),
    ]
},

    "overpayment_scam": {
        "group": "refund_overpayment",
        "weight": 0.35,
        "keywords": [
            "accidentally credited", "extra amount",
            "mistakenly sent", "wrong transfer",
            "please return", "send back", "transfer back",
            "return the amount", "excess amount credited",
            "mistakenly transferred", "kindly return",
        ],
        "phrases": [
            "we accidentally credited extra",
            "please return the excess amount",
            "mistakenly transferred to your account",
            "kindly send back rs", "wrong amount credited please return",
            "excess amount please return", "please transfer back",
            "accidentally sent extra amount",
        ],
        "patterns": [
            re.compile(r'(accidentally|mistakenly|wrongly)\s+(credited|transferred|sent)', re.I),
            re.compile(r'(please|kindly)\s+(return|send\s+back|transfer\s+back)\s+(rs\.?|inr|₹|the\s+amount)', re.I),
        ],
    },

    # ── THREAT ESCALATION LAYER ───────────────────────────────────────────────

    "legal_action_threat": {
        "group": "threat_escalation",
        "weight": 0.30,
        "keywords": [
            "legal action", "police complaint",
            "court notice", "legal notice", "arrest",
            "warrant", "lawsuit", "legal proceedings",
            "criminal complaint", "non-bailable", "nabard notice",
        ],
        "phrases": [
            "fir will be filed", "legal action will be taken",
            "police complaint registered", "court notice issued",
            "cybercrime department has flagged",
            "criminal proceedings initiated", "arrest warrant issued",
            "non-bailable warrant", "legal notice served",
        ],
        "patterns": [
            re.compile(r'\bfir\b', re.I),
            re.compile(r'(legal\s+action|police\s+complaint|criminal\s+complaint)\s+(will\s+be\s+)?(filed|registered|lodged|issued|initiated)', re.I),
            re.compile(r'(arrest|warrant|court\s+notice|legal\s+notice)\s+(issued|served|pending)', re.I),
        ],
    },

    "cibil_score_threat": {
        "group": "threat_escalation",
        "weight": 0.25,
        "keywords": [
            "cibil", "cibil score", "credit score",
            "credit report", "cibil defaulter",
            "blacklisted", "credit rating", "cibil damage",
            "cibil negative", "credit bureau",
        ],
        "phrases": [
            "your cibil score will be affected",
            "reported to cibil as defaulter",
            "credit score will drop", "loan default will affect cibil",
            "blacklisted in cibil", "negative cibil report",
            "cibil score will be damaged", "reported to credit bureau",
        ],
        "patterns": [
            re.compile(r'(cibil|credit)\s+(score|report|rating)\s+(will\s+be\s+)?(affected|damaged|dropped|reported)', re.I),
            re.compile(r'(reported|blacklisted|defaulter)\s+(in|to|at)\s+cibil', re.I),
        ],
    },

    "telecom_impersonation": {
        "group": "threat_escalation",
        "weight": 0.35,
        "keywords": [
            "trai", "sim blocked", "sim will be blocked",
            "mobile number blocked", "number deactivated",
            "telecom regulatory", "dot notice",
            "sim disconnection", "sim card blocked",
            "number will be disconnected", "sim suspension",
        ],
        "phrases": [
            "trai will block your sim", "your mobile number will be deactivated",
            "sim disconnection notice", "as per trai directive",
            "dot has flagged your number", "your sim will be blocked",
            "mobile number will be suspended", "number will be disconnected",
            "trai compliance required",
        ],
        "patterns": [
            re.compile(r'(trai|dot)\s+(will|has|directive|notice|compliance)', re.I),
            re.compile(r'(sim|mobile\s+number|number)\s+(will\s+be\s+)?(blocked|deactivated|disconnected|suspended)', re.I),
        ],
    },

    # ── SEASONAL LAYER ────────────────────────────────────────────────────────

    "tax_season_exploit": {
        "group": "seasonal",
        "weight": 0.25,
        "keywords": [
            "itr", "income tax return", "tax refund",
            "tds refund", "form 26as", "tax notice",
            "it department notice", "pan linked",
            "advance tax", "tax filing", "tax demand",
            "tax arrear", "it notice",
        ],
        "phrases": [
            "itr refund of rs pending", "income tax department notice",
            "your pan has been flagged", "tds refund ready to claim",
            "advance tax demand notice", "file your itr",
            "income tax notice issued", "form 26as discrepancy",
            "tax refund pending your action",
        ],
        "patterns": [
            re.compile(r'itr\s+(refund|pending|notice|filing)', re.I),
            re.compile(r'(income\s+tax|tds|advance\s+tax)\s+(refund|notice|demand|return)', re.I),
            re.compile(r'form\s+26as', re.I),
        ],
    },

    "emergency_fabrication": {
        "group": "seasonal",
        "weight": 0.30,
        "keywords": [
            "emergency", "urgent help", "immediate help",
            "family emergency", "accident", "hospital",
            "stranded", "stuck", "need money urgently",
            "emergency transfer", "critical situation",
            "life emergency", "medical emergency",
        ],
        "phrases": [
            "family member met with accident",
            "emergency funds needed", "stranded and need immediate help",
            "hospital emergency transfer", "urgent help needed right now",
            "medical emergency fund", "critical situation need help",
            "family emergency transfer needed",
        ],
        "patterns": [
            re.compile(r'(family|medical|life)\s+emergency', re.I),
            re.compile(r'(stranded|stuck|accident|hospital)\s+.*(transfer|send|help|funds)', re.I),
        ],
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# NEGATIVE SIGNALS
# These REDUCE the phishing score — markers of legitimate bank messages
# ──────────────────────────────────────────────────────────────────────────────

NEGATIVE_SIGNALS = [
    "never share your otp",
    "do not share otp",
    "bank never asks for otp",
    "do not share otp with anyone",
    "never share otp with anyone",
    "never share your pin",
    "do not share pin",
    "bank never asks for pin",
    "never share your password",
    "do not share password",
    "bank never asks for password",
    "never share your card details",
    "do not share card details",
    "this is an automated message",
    "no action needed",
    "ignore if already done",
    "if not you please ignore",
    "for help visit your branch",
    "visit nearest branch",
    "call our official number 1800",
    "call 1800",
    "delivered by",
    "for disputes call",
    "not a promotional message",
    "as per your request",
    "you initiated this",
    "debited from your account",
"credited to your account",
"transaction successful",
"payment successful",
"transfer successful",
"transaction complete",
"payment complete",
"utr no",
"utr number",
"ref no",
"reference number",
"txn id",
"transaction id",
"available balance",
"avl bal",
"current balance",
"closing balance",
"bank will never ask",
"we will never ask",
"never ask for your otp",
"never ask for your pin",
"never ask for your password",
"never call asking for",
"beware of fraud",
"stay alert against fraud",
"protect yourself from fraud",
"report fraud",
"do not respond to",
"do not click on",
"do not share with anyone",
"keep your credentials safe",
"your security is important",
"report suspicious activity",
"cybercrime.gov.in",
"report to us immediately",
"as requested by you",
"based on your request",
"you have initiated",
"initiated by you",
"requested by you",
"as per your instruction",
"following your request",
"in response to your query",
"your request has been processed",
"your request is being processed",
"pursuant to your request",
"visit your nearest branch",
"visit any branch",
"visit home branch",
"contact your branch",
"visit our website",
"official website",
"official app",
"imobile",
"yono app",
"hdfc app",
"icici ibank",
"net banking portal",
"if not done by you",
"if not initiated by you",
"if this was not you",
"if you did not initiate",
"if you have not requested",
"contact us immediately",
"call us immediately",
"block your card",
"hotlist your card",
"call helpline",
"inform us immediately",
"visit branch for kyc",
"kyc at branch",
"submit kyc at branch",
"kyc update at branch",
"visit nearest branch with",
"carry original documents",
"bring aadhaar to branch",
"with original id proof",
"for your information",
"for your records",
"this is to inform you",
"please note",
"kindly note",
"please be informed",
"this is a service message",
"this is a system generated",
"auto generated message",
"do not reply to this",
"this is an auto generated sms",
"do not reply",
]

NEGATIVE_REDUCTION = 0.3  # reduce score by this amount per negative signal found


# ──────────────────────────────────────────────────────────────────────────────
# SIGNAL WEIGHTS BY GROUP
# Used to apply group-level dampening if needed
# ──────────────────────────────────────────────────────────────────────────────

GROUP_WEIGHTS = {
    "psychological":      1.0,
    "authority":          1.0,
    "credential":         1.2,  # boost — credential ask is highest risk
    "greed":              0.9,
    "transaction":        0.8,  # dampened — legit banks also send transaction alerts
    "technical":          1.1,
    "behavioural":        1.0,
    "upi_digital":        1.2,  # boost — UPI scams are high risk
    "social_engineering": 0.9,
    "refund_overpayment": 1.0,
    "threat_escalation":  1.1,
    "seasonal":           0.9,
}


# ──────────────────────────────────────────────────────────────────────────────
# RESULT DATACLASS
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ScanResult:
    phishing_score: float
    risk_level: str
    fired_signals: list[str]
    detected_keywords: dict[str, list[str]]
    signal_groups_fired: list[str]
    negative_signals_found: list[str]
    signal_count: int
    top_signal: str | None


# ──────────────────────────────────────────────────────────────────────────────
# PREPROCESSING
# ──────────────────────────────────────────────────────────────────────────────

def preprocess(text: str) -> str:
    """Normalize text for matching."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


# ──────────────────────────────────────────────────────────────────────────────
# CONTEXT-BASED BEHAVIOURAL SIGNAL EVALUATION
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_behavioural_signals(context: dict) -> dict[str, float]:
    """
    Evaluate behavioural signals from transaction context.

    Args:
        context: dict with optional keys:
            transaction_hour      : int 0-23
            amount                : float
            is_new_recipient      : bool
            amount_vs_average     : float (ratio, e.g. 3.5 = 3.5x average)
            recent_transaction_count : int (in last hour)

    Returns:
        dict of signal_name → score contribution
    """
    scores = {}

    hour = context.get("transaction_hour")
    if hour is not None:
        if hour < 7 or hour > 22:
            scores["off_hours_transaction"] = SIGNALS["off_hours_transaction"]["weight"]

    amount = context.get("amount")
    if amount is not None:
        if amount >= 5000 and amount % 1000 == 0:
            scores["round_amount"] = SIGNALS["round_amount"]["weight"]

    if context.get("is_new_recipient"):
        scores["new_recipient"] = SIGNALS["new_recipient"]["weight"]

    ratio = context.get("amount_vs_average")
    if ratio is not None and ratio > 3.0:
        scores["unusual_amount"] = SIGNALS["unusual_amount"]["weight"]

    tx_count = context.get("recent_transaction_count")
    if tx_count is not None and tx_count > 3:
        scores["transaction_velocity"] = SIGNALS["transaction_velocity"]["weight"]

    return scores
# ── Normalization constants ───────────────────────────────────────────────────

ZERO_WIDTH = r'[\u200b\u200c\u200d\u200e\u200f\uFEFF\u00ad]'

# Cyrillic + Greek + other Unicode confusables → ASCII equivalents
# NFKC alone does NOT resolve these — explicit map is required
CONFUSABLES_MAP = str.maketrans({
    # Cyrillic lookalikes
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c',
    'у': 'y', 'х': 'x', 'і': 'i', 'ј': 'j', 'ѕ': 's',
    'ԁ': 'd', 'ո': 'n', 'ս': 'u', 'ƅ': 'b', 'ⅼ': 'l',
    # Greek lookalikes
    'ο': 'o', 'α': 'a', 'ε': 'e', 'ι': 'i', 'ν': 'v',
    'κ': 'k', 'ρ': 'p', 'τ': 't', 'χ': 'x', 'υ': 'u',
    # Latin extended lookalikes
    'ɑ': 'a', 'ɡ': 'g', 'ƙ': 'k', 'ʂ': 's', 'ẃ': 'w',
    # Fullwidth ASCII
    'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e',
    'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j',
    'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o',
    'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't',
    'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y',
    'ｚ': 'z',
})

LEET_MAP = str.maketrans({
    '0': 'o', '1': 'i', '2': 'z', '3': 'e',
    '4': 'a', '5': 's', '7': 't',
    '@': 'a', '$': 's', '!': 'i',
})

def normalize_advanced(text: str) -> str:
    # Step 1 — NFKC unicode normalization (handles some composed chars)
    text = unicodedata.normalize("NFKC", text)

    # Step 2 — explicit confusables map (Cyrillic/Greek survive NFKC)
    text = text.translate(CONFUSABLES_MAP)

    # Step 3 — lowercase after confusables (order matters)
    text = text.lower()

    # Step 4 — strip zero-width and invisible characters
    text = re.sub(ZERO_WIDTH, '', text)

    # Step 5 — defang URL obfuscation
    text = text.replace("hxxps", "https").replace("hxxp", "http")
    text = text.replace("[.]", ".").replace("(.)", ".")

    # Step 6 — collapse all whitespace variants early
    text = re.sub(r'\s+', ' ', text)

    # Step 7 — leet speak substitution
    text = text.translate(LEET_MAP)

    # Step 8 — collapse spaced-out letters (a c c o u n t → account)
    # matches sequences of single chars separated by spaces
    def collapse_spaced(m):
        return m.group(0).replace(' ', '')
    text = re.sub(r'\b(\w\s){2,}\w\b', collapse_spaced, text)

    # Step 9 — collapse repeated characters (blooocked → blocked)
    text = re.sub(r'(.)\1{2,}', r'\1', text)

    # Step 10 — remove remaining punctuation noise (keep : / . -)
    text = re.sub(r'[^\w\s:/.-]', ' ', text)

    # Step 11 — final whitespace cleanup
    text = re.sub(r'\s+', ' ', text).strip()

    return text
# ──────────────────────────────────────────────────────────────────────────────
# CORE SCANNER
# ──────────────────────────────────────────────────────────────────────────────
def scan_message(
    message: str,
    context: Optional[dict] = None,
) -> ScanResult:

    if context is None:
        context = {}

    text_clean = normalize_advanced(preprocess(message))

    fired_signals = set()
    detected_keywords: dict[str, list[str]] = {}
    raw_scores: dict[str, float] = {}
    
    # Basic word count for density analysis later
    word_count = max(len(text_clean.split()), 1)

    # ─────────────────────────────────────────────
    # TEXT SIGNAL EVALUATION (Unchanged logic)
    # ─────────────────────────────────────────────
    for signal_name, signal_def in SIGNALS.items():

        # skip behavioural-only signals
        if signal_def.get("context_key") and not signal_def.get("keywords") and not signal_def.get("patterns"):
            continue

        hits = []
        
        # NEGATIVE PHRASES (signal-level cancellation)
        neg_phrases = signal_def.get("negative_phrases", [])
        if any(neg in text_clean for neg in neg_phrases):
            continue

        # keywords
        for kw in signal_def.get("keywords", []):
            if kw.lower() in text_clean:
                hits.append(kw)

        # phrases
        for phrase in signal_def.get("phrases", []):
            if phrase.lower() in text_clean:
                hits.append(phrase)

        # regex
        for pattern in signal_def.get("patterns", []):
            match = pattern.search(text_clean)
            if match:
                hits.append(match.group(0))

        if hits:
            base_weight = signal_def["weight"]
            group = signal_def["group"]
            group_multiplier = GROUP_WEIGHTS.get(group, 1.0)

            # Keep the asymptotic hit multiplier
            hit_multiplier = 1 - math.exp(-0.7 * len(hits))

            score_contribution = base_weight * group_multiplier * hit_multiplier

            fired_signals.add(signal_name)
            detected_keywords[signal_name] = list(set(hits))
            raw_scores[signal_name] = score_contribution

    # ─────────────────────────────────────────────
    # BEHAVIOURAL SIGNALS (Unchanged logic)
    # ─────────────────────────────────────────────
    behavioural_scores = evaluate_behavioural_signals(context)

    for signal_name, score in behavioural_scores.items():
        fired_signals.add(signal_name)
        detected_keywords[signal_name] = ["context"]
        raw_scores[signal_name] = score

    # ─────────────────────────────────────────────
    # ADVANCED SCORE AGGREGATION (NEW LOGIC)
    # ─────────────────────────────────────────────
    raw_total = sum(raw_scores.values()) if raw_scores else 0.0
    
    # 1. Evaluate Signal Groups
    signal_groups_fired = list({
        SIGNALS[s]["group"]
        for s in fired_signals
        if s in SIGNALS
    })

    if raw_total > 0:
        # A. Smooth Diversity Bonus
        # Instead of rigid steps (1.1, 1.2), use a logarithmic curve. 
        # 1 group = 1.0x | 2 groups = ~1.17x | 4 groups = ~1.40x
        diversity_multiplier = 1.0 + (math.log1p(len(signal_groups_fired)) * 0.25)
        adjusted_score = raw_total * diversity_multiplier

        # B. Text Density Dampener
        # Phishing is usually brief. If a document is very long (>50 words) but has very few hits, 
        # it's likely a legitimate document triggering false positives.
        total_hit_count = sum(len(hits) for hits in detected_keywords.values() if hits != ["context"])
        hits_per_word = total_hit_count / word_count
        
        if word_count > 50 and hits_per_word < 0.03: # Less than 3% of the text is trigger words
            adjusted_score *= 0.80 # Dampen score by 20%

        # C. Exponential Bounding (The Magic Formula)
        # Instead of min(1.0, total), which flatlines, we use an asymptotic curve: 1 - e^(-k * x)
        # This naturally bounds the score between 0.0 and 0.999 without ever hard-clipping.
        base_phishing_score = 1.0 - math.exp(-1.4 * adjusted_score)

        # D. Smart Negative Dampening
        negative_found = [neg for neg in NEGATIVE_SIGNALS if neg in text_clean]
        if negative_found:
            # If the score is overwhelmingly high (>0.85), IGNORE negative signals.
            # Attackers append "Bank will never ask for OTP" to bypass scanners. We don't let them.
            if base_phishing_score < 0.85:
                # Use a proportional reduction rather than flat subtraction.
                # Reduce the score by 15% per negative signal found, capped at a 40% reduction.
                reduction_factor = min(len(negative_found) * 0.15, 0.40)
                base_phishing_score = base_phishing_score * (1.0 - reduction_factor)
    else:
        base_phishing_score = 0.0
        negative_found = []

    # ─────────────────────────────────────────────
    # FINAL SCORE & CATEGORIZATION
    # ─────────────────────────────────────────────
    phishing_score = round(base_phishing_score, 4)

    if phishing_score >= 0.70:
        risk_level = "HIGH"
    elif phishing_score >= 0.40:
        risk_level = "MEDIUM"
    elif phishing_score >= 0.20:
        risk_level = "LOW"
    else:
        risk_level = "SAFE"

    # Identify true maximum contributor
    top_signal = (
        max(raw_scores.items(), key=lambda x: x[1])[0]
        if raw_scores else None
    )

    return ScanResult(
        phishing_score=phishing_score,
        risk_level=risk_level,
        fired_signals=list(fired_signals),
        detected_keywords=detected_keywords,
        signal_groups_fired=signal_groups_fired,
        negative_signals_found=negative_found,
        signal_count=len(fired_signals),
        top_signal=top_signal,
    )
