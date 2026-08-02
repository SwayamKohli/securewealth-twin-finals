"""
ai/engines/i18n_catalog.py — Multilingual explanation templates (tasks 3.5/5.5)
===============================================================================
Customer-facing narrative templates in English, Hindi, and Punjabi for the
Explainability Layer. Template-based (not LLM) so the demo is deterministic
and works offline.

Usage:
    from ai.engines.i18n_catalog import narrative
    narrative("decision", "CHALLENGE", "hi", amount="₹95,000")
"""

from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "hi", "pa")

_CATALOG: dict[str, dict[str, dict[str, str]]] = {
    # ── Fraud decision explanations (5.2 — explain WHY, not HOW) ─────────
    "decision": {
        "ALLOW": {
            "en": "This investment matched your usual activity, so it went through smoothly with no extra steps.",
            "hi": "यह निवेश आपकी सामान्य गतिविधि से मेल खाता है, इसलिए यह बिना किसी अतिरिक्त कदम के पूरा हो गया।",
            "pa": "ਇਹ ਨਿਵੇਸ਼ ਤੁਹਾਡੀ ਆਮ ਗਤੀਵਿਧੀ ਨਾਲ ਮੇਲ ਖਾਂਦਾ ਹੈ, ਇਸ ਲਈ ਇਹ ਬਿਨਾਂ ਕਿਸੇ ਵਾਧੂ ਕਦਮ ਦੇ ਪੂਰਾ ਹੋ ਗਿਆ।",
        },
        "WARN": {
            "en": "A few things about this investment looked slightly unusual for you, so we flagged it for your attention. Your money is safe.",
            "hi": "इस निवेश में कुछ बातें आपके लिए थोड़ी असामान्य लगीं, इसलिए हमने इसे आपके ध्यान के लिए चिह्नित किया। आपका पैसा सुरक्षित है।",
            "pa": "ਇਸ ਨਿਵੇਸ਼ ਵਿੱਚ ਕੁਝ ਗੱਲਾਂ ਤੁਹਾਡੇ ਲਈ ਥੋੜ੍ਹੀਆਂ ਅਸਾਧਾਰਨ ਲੱਗੀਆਂ, ਇਸ ਲਈ ਅਸੀਂ ਇਸਨੂੰ ਤੁਹਾਡੇ ਧਿਆਨ ਲਈ ਨਿਸ਼ਾਨਬੱਧ ਕੀਤਾ। ਤੁਹਾਡਾ ਪੈਸਾ ਸੁਰੱਖਿਅਤ ਹੈ।",
        },
        "CHALLENGE": {
            "en": "This investment did not match your usual pattern, so we paused it and asked you to confirm your identity. This protects you if someone else tries to use your account.",
            "hi": "यह निवेश आपके सामान्य पैटर्न से मेल नहीं खाता, इसलिए हमने इसे रोककर आपसे पहचान की पुष्टि करने को कहा। यह आपकी सुरक्षा के लिए है, यदि कोई और आपका खाता इस्तेमाल करने की कोशिश करे।",
            "pa": "ਇਹ ਨਿਵੇਸ਼ ਤੁਹਾਡੇ ਆਮ ਪੈਟਰਨ ਨਾਲ ਮੇਲ ਨਹੀਂ ਖਾਂਦਾ, ਇਸ ਲਈ ਅਸੀਂ ਇਸਨੂੰ ਰੋਕ ਕੇ ਤੁਹਾਡੀ ਪਛਾਣ ਦੀ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਕਿਹਾ। ਇਹ ਤੁਹਾਡੀ ਸੁਰੱਖਿਆ ਲਈ ਹੈ, ਜੇ ਕੋਈ ਹੋਰ ਤੁਹਾਡਾ ਖਾਤਾ ਵਰਤਣ ਦੀ ਕੋਸ਼ਿਸ਼ ਕਰੇ।",
        },
        "BLOCK": {
            "en": "This investment showed strong signs of fraud, so we stopped it completely. No money has left your account. If this was really you, please contact support.",
            "hi": "इस निवेश में धोखाधड़ी के प्रबल संकेत मिले, इसलिए हमने इसे पूरी तरह रोक दिया। आपके खाते से कोई पैसा नहीं गया है। यदि यह वास्तव में आप थे, तो कृपया सहायता से संपर्क करें।",
            "pa": "ਇਸ ਨਿਵੇਸ਼ ਵਿੱਚ ਧੋਖਾਧੜੀ ਦੇ ਮਜ਼ਬੂਤ ਸੰਕੇਤ ਮਿਲੇ, ਇਸ ਲਈ ਅਸੀਂ ਇਸਨੂੰ ਪੂਰੀ ਤਰ੍ਹਾਂ ਰੋਕ ਦਿੱਤਾ। ਤੁਹਾਡੇ ਖਾਤੇ ਵਿੱਚੋਂ ਕੋਈ ਪੈਸਾ ਨਹੀਂ ਗਿਆ। ਜੇ ਇਹ ਸੱਚਮੁੱਚ ਤੁਸੀਂ ਸੀ, ਤਾਂ ਕਿਰਪਾ ਕਰਕੇ ਸਹਾਇਤਾ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
        },
    },
    # ── Challenge explanations (5.4 — why the challenge appeared) ────────
    "challenge": {
        "DEVICE_CONFIRMATION": {
            "en": "We did not recognise the device you are using, so we asked a quick security question to make sure it is really you.",
            "hi": "हमने आपके उपकरण को नहीं पहचाना, इसलिए यह सुनिश्चित करने के लिए कि यह वास्तव में आप हैं, हमने एक छोटा सुरक्षा प्रश्न पूछा।",
            "pa": "ਅਸੀਂ ਤੁਹਾਡੇ ਡਿਵਾਈਸ ਨੂੰ ਨਹੀਂ ਪਛਾਣਿਆ, ਇਸ ਲਈ ਇਹ ਯਕੀਨੀ ਬਣਾਉਣ ਲਈ ਕਿ ਇਹ ਸੱਚਮੁੱਚ ਤੁਸੀਂ ਹੋ, ਅਸੀਂ ਇੱਕ ਛੋਟਾ ਸੁਰੱਖਿਆ ਸਵਾਲ ਪੁੱਛਿਆ।",
        },
        "OTP_RECONFIRMATION": {
            "en": "The way the OTP was entered looked rushed or unusual, so we asked for it once more to be safe.",
            "hi": "OTP दर्ज करने का तरीका जल्दबाज़ी भरा या असामान्य लगा, इसलिए सुरक्षा के लिए हमने इसे एक बार फिर मांगा।",
            "pa": "OTP ਦਰਜ ਕਰਨ ਦਾ ਤਰੀਕਾ ਜਲਦਬਾਜ਼ੀ ਵਾਲਾ ਜਾਂ ਅਸਾਧਾਰਨ ਲੱਗਿਆ, ਇਸ ਲਈ ਸੁਰੱਖਿਆ ਲਈ ਅਸੀਂ ਇਸਨੂੰ ਇੱਕ ਵਾਰ ਫਿਰ ਮੰਗਿਆ।",
        },
        "TRANSACTION_CONFIRMATION": {
            "en": "This amount is much larger than your usual investments, so we asked you to confirm it before completing.",
            "hi": "यह राशि आपके सामान्य निवेश से काफी बड़ी है, इसलिए पूरा करने से पहले हमने आपसे पुष्टि करने को कहा।",
            "pa": "ਇਹ ਰਕਮ ਤੁਹਾਡੇ ਆਮ ਨਿਵੇਸ਼ ਨਾਲੋਂ ਕਾਫ਼ੀ ਵੱਡੀ ਹੈ, ਇਸ ਲਈ ਪੂਰਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਅਸੀਂ ਤੁਹਾਨੂੰ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਕਿਹਾ।",
        },
        "RISK_WARNING_ACCEPTANCE": {
            "en": "This investment happened at an unusual time or pattern for you, so we asked you to review it once before continuing.",
            "hi": "यह निवेश आपके लिए असामान्य समय या पैटर्न पर हुआ, इसलिए आगे बढ़ने से पहले हमने आपसे एक बार समीक्षा करने को कहा।",
            "pa": "ਇਹ ਨਿਵੇਸ਼ ਤੁਹਾਡੇ ਲਈ ਅਸਾਧਾਰਨ ਸਮੇਂ ਜਾਂ ਪੈਟਰਨ 'ਤੇ ਹੋਇਆ, ਇਸ ਲਈ ਅੱਗੇ ਵਧਣ ਤੋਂ ਪਹਿਲਾਂ ਅਸੀਂ ਤੁਹਾਨੂੰ ਇੱਕ ਵਾਰ ਸਮੀਖਿਆ ਕਰਨ ਲਈ ਕਿਹਾ।",
        },
    },
    # ── Phishing explanations (5.3) ──────────────────────────────────────
    "phishing": {
        "SUSPICIOUS_LINK": {
            "en": "This message contains a link that does not belong to your bank. Clicking it could take you to a fake website designed to steal your details.",
            "hi": "इस संदेश में एक लिंक है जो आपके बैंक का नहीं है। इस पर क्लिक करने से आप एक नकली वेबसाइट पर जा सकते हैं जो आपकी जानकारी चुराने के लिए बनाई गई है।",
            "pa": "ਇਸ ਸੁਨੇਹੇ ਵਿੱਚ ਇੱਕ ਲਿੰਕ ਹੈ ਜੋ ਤੁਹਾਡੇ ਬੈਂਕ ਦਾ ਨਹੀਂ ਹੈ। ਇਸ 'ਤੇ ਕਲਿੱਕ ਕਰਨ ਨਾਲ ਤੁਸੀਂ ਇੱਕ ਨਕਲੀ ਵੈੱਬਸਾਈਟ 'ਤੇ ਜਾ ਸਕਦੇ ਹੋ ਜੋ ਤੁਹਾਡੀ ਜਾਣਕਾਰੀ ਚੋਰੀ ਕਰਨ ਲਈ ਬਣਾਈ ਗਈ ਹੈ।",
        },
        "UNKNOWN_SENDER": {
            "en": "This message came from a number or sender your bank does not use. Real banks send messages from registered IDs only.",
            "hi": "यह संदेश ऐसे नंबर या भेजने वाले से आया है जिसका उपयोग आपका बैंक नहीं करता। असली बैंक केवल पंजीकृत आईडी से संदेश भेजते हैं।",
            "pa": "ਇਹ ਸੁਨੇਹਾ ਅਜਿਹੇ ਨੰਬਰ ਜਾਂ ਭੇਜਣ ਵਾਲੇ ਤੋਂ ਆਇਆ ਹੈ ਜੋ ਤੁਹਾਡਾ ਬੈਂਕ ਨਹੀਂ ਵਰਤਦਾ। ਅਸਲੀ ਬੈਂਕ ਸਿਰਫ਼ ਰਜਿਸਟਰਡ ID ਤੋਂ ਸੁਨੇਹੇ ਭੇਜਦੇ ਹਨ।",
        },
        "FAKE_DOMAIN": {
            "en": "The website address in this message imitates a real bank but is not genuine. Scammers often change one or two letters to fool you.",
            "hi": "इस संदेश में दिया गया वेबसाइट पता असली बैंक की नकल करता है लेकिन असली नहीं है। ठग अक्सर एक-दो अक्षर बदलकर आपको धोखा देते हैं।",
            "pa": "ਇਸ ਸੁਨੇਹੇ ਵਿੱਚ ਦਿੱਤਾ ਵੈੱਬਸਾਈਟ ਪਤਾ ਅਸਲੀ ਬੈਂਕ ਦੀ ਨਕਲ ਕਰਦਾ ਹੈ ਪਰ ਅਸਲੀ ਨਹੀਂ ਹੈ। ਠੱਗ ਅਕਸਰ ਇੱਕ-ਦੋ ਅੱਖਰ ਬਦਲ ਕੇ ਤੁਹਾਨੂੰ ਧੋਖਾ ਦਿੰਦੇ ਹਨ।",
        },
        "URGENT_LANGUAGE": {
            "en": "This message tries to rush or scare you (like 'account will be blocked today'). Scammers create urgency so you act without thinking.",
            "hi": "यह संदेश आपको जल्दबाज़ी या डराने की कोशिश करता है (जैसे 'खाता आज ब्लॉक हो जाएगा')। ठग जल्दबाज़ी पैदा करते हैं ताकि आप बिना सोचे कदम उठाएँ।",
            "pa": "ਇਹ ਸੁਨੇਹਾ ਤੁਹਾਨੂੰ ਜਲਦਬਾਜ਼ੀ ਜਾਂ ਡਰਾਉਣ ਦੀ ਕੋਸ਼ਿਸ਼ ਕਰਦਾ ਹੈ (ਜਿਵੇਂ 'ਖਾਤਾ ਅੱਜ ਬਲਾਕ ਹੋ ਜਾਵੇਗਾ')। ਠੱਗ ਜਲਦਬਾਜ਼ੀ ਪੈਦਾ ਕਰਦੇ ਹਨ ਤਾਂ ਜੋ ਤੁਸੀਂ ਬਿਨਾਂ ਸੋਚੇ ਕਦਮ ਚੁੱਕੋ।",
        },
        "OTP_SCAM": {
            "en": "This message asks for your OTP or PIN. Your bank will NEVER ask for these — anyone who does is trying to steal from you.",
            "hi": "यह संदेश आपका OTP या PIN मांगता है। आपका बैंक कभी भी ये नहीं मांगेगा — जो भी मांगे, वह आपसे चोरी करने की कोशिश कर रहा है।",
            "pa": "ਇਹ ਸੁਨੇਹਾ ਤੁਹਾਡਾ OTP ਜਾਂ PIN ਮੰਗਦਾ ਹੈ। ਤੁਹਾਡਾ ਬੈਂਕ ਕਦੇ ਵੀ ਇਹ ਨਹੀਂ ਮੰਗੇਗਾ — ਜੋ ਵੀ ਮੰਗੇ, ਉਹ ਤੁਹਾਡੇ ਤੋਂ ਚੋਰੀ ਕਰਨ ਦੀ ਕੋਸ਼ਿਸ਼ ਕਰ ਰਿਹਾ ਹੈ।",
        },
        "SAFE": {
            "en": "We did not find any warning signs in this message. Still, never share your OTP, PIN, or password with anyone.",
            "hi": "हमें इस संदेश में कोई चेतावनी संकेत नहीं मिला। फिर भी, अपना OTP, PIN या पासवर्ड कभी किसी के साथ साझा न करें।",
            "pa": "ਸਾਨੂੰ ਇਸ ਸੁਨੇਹੇ ਵਿੱਚ ਕੋਈ ਚੇਤਾਵਨੀ ਸੰਕੇਤ ਨਹੀਂ ਮਿਲਿਆ। ਫਿਰ ਵੀ, ਆਪਣਾ OTP, PIN ਜਾਂ ਪਾਸਵਰਡ ਕਦੇ ਕਿਸੇ ਨਾਲ ਸਾਂਝਾ ਨਾ ਕਰੋ।",
        },
    },
}


def narrative(kind: str, key: str, language: str = "en") -> str | None:
    """Return the localised narrative, or None if not in the catalog."""
    lang = language if language in SUPPORTED_LANGUAGES else "en"
    entry = _CATALOG.get(kind, {}).get(key)
    if entry is None:
        return None
    return entry.get(lang) or entry.get("en")
