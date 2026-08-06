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
    # ── Wealth recommendation explanations ───────────────────────────────
    #
    # These were English-only at every layer until now: no language field on
    # the request, no handling in the endpoint, and no entries here. Switching
    # the app to Hindi or Punjabi translated the whole interface EXCEPT the one
    # paragraph explaining why a product was being suggested — which is the
    # paragraph a customer most needs in their own language.
    #
    # Keyed on recommendation_id from wealth_engine. Ids that carry a dynamic
    # suffix (ffd_reinvest_<deposit_id>) are matched on their prefix.
    "wealth": {
        "emergency_fund_implicit": {
            "en": "Before any investment, we suggest keeping about four months of your expenses in an easily accessible deposit. It is not the highest return, but it is the money that keeps a bad month from becoming a loan.",
            "hi": "किसी भी निवेश से पहले, हम सुझाव देते हैं कि आप अपने लगभग चार महीने के खर्च के बराबर रकम आसानी से निकाली जा सकने वाली जमा में रखें। इस पर सबसे ज़्यादा रिटर्न नहीं मिलता, लेकिन यही पैसा एक मुश्किल महीने को कर्ज़ बनने से रोकता है।",
            "pa": "ਕਿਸੇ ਵੀ ਨਿਵੇਸ਼ ਤੋਂ ਪਹਿਲਾਂ, ਅਸੀਂ ਸੁਝਾਅ ਦਿੰਦੇ ਹਾਂ ਕਿ ਤੁਸੀਂ ਆਪਣੇ ਲਗਭਗ ਚਾਰ ਮਹੀਨਿਆਂ ਦੇ ਖਰਚ ਬਰਾਬਰ ਰਕਮ ਸੌਖੀ ਤਰ੍ਹਾਂ ਕੱਢੀ ਜਾ ਸਕਣ ਵਾਲੀ ਜਮ੍ਹਾਂ ਵਿੱਚ ਰੱਖੋ। ਇਸ 'ਤੇ ਸਭ ਤੋਂ ਵੱਧ ਰਿਟਰਨ ਨਹੀਂ ਮਿਲਦਾ, ਪਰ ਇਹੀ ਪੈਸਾ ਇੱਕ ਔਖੇ ਮਹੀਨੇ ਨੂੰ ਕਰਜ਼ਾ ਬਣਨ ਤੋਂ ਰੋਕਦਾ ਹੈ।",
        },
        "emergency_fund_goal": {
            "en": "This moves you closer to the emergency fund goal you set. Completing it first makes every later investment safer, because you will not need to break it in a difficult month.",
            "hi": "यह आपको उस आपातकालीन फंड लक्ष्य के करीब ले जाता है जो आपने तय किया था। इसे पहले पूरा करने से आगे का हर निवेश ज़्यादा सुरक्षित हो जाता है, क्योंकि मुश्किल महीने में आपको उसे तोड़ना नहीं पड़ेगा।",
            "pa": "ਇਹ ਤੁਹਾਨੂੰ ਉਸ ਐਮਰਜੈਂਸੀ ਫੰਡ ਟੀਚੇ ਦੇ ਨੇੜੇ ਲੈ ਜਾਂਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਤੈਅ ਕੀਤਾ ਸੀ। ਇਸਨੂੰ ਪਹਿਲਾਂ ਪੂਰਾ ਕਰਨ ਨਾਲ ਅੱਗੇ ਦਾ ਹਰ ਨਿਵੇਸ਼ ਵੱਧ ਸੁਰੱਖਿਅਤ ਹੋ ਜਾਂਦਾ ਹੈ, ਕਿਉਂਕਿ ਔਖੇ ਮਹੀਨੇ ਵਿੱਚ ਤੁਹਾਨੂੰ ਉਸਨੂੰ ਤੋੜਨਾ ਨਹੀਂ ਪਵੇਗਾ।",
        },
        "debt_reduction_stressed": {
            "en": "More than half of your income is going to loan instalments. Paying down the costliest loan first is a guaranteed saving — no fund can promise a return higher than the interest you stop paying.",
            "hi": "आपकी आय का आधे से ज़्यादा हिस्सा कर्ज़ की किस्तों में जा रहा है। सबसे महँगे कर्ज़ को पहले चुकाना एक निश्चित बचत है — कोई भी फंड उस ब्याज से ज़्यादा रिटर्न का वादा नहीं कर सकता जो आप देना बंद कर देते हैं।",
            "pa": "ਤੁਹਾਡੀ ਆਮਦਨ ਦਾ ਅੱਧੇ ਤੋਂ ਵੱਧ ਹਿੱਸਾ ਕਰਜ਼ੇ ਦੀਆਂ ਕਿਸ਼ਤਾਂ ਵਿੱਚ ਜਾ ਰਿਹਾ ਹੈ। ਸਭ ਤੋਂ ਮਹਿੰਗੇ ਕਰਜ਼ੇ ਨੂੰ ਪਹਿਲਾਂ ਚੁਕਾਉਣਾ ਇੱਕ ਪੱਕੀ ਬੱਚਤ ਹੈ — ਕੋਈ ਵੀ ਫੰਡ ਉਸ ਵਿਆਜ ਤੋਂ ਵੱਧ ਰਿਟਰਨ ਦਾ ਵਾਅਦਾ ਨਹੀਂ ਕਰ ਸਕਦਾ ਜੋ ਤੁਸੀਂ ਦੇਣਾ ਬੰਦ ਕਰ ਦਿੰਦੇ ਹੋ।",
        },
        "debt_optimisation": {
            "en": "Putting a little extra against your highest-interest loan each month shortens it considerably. The interest you save is larger than what an equivalent deposit would earn.",
            "hi": "हर महीने अपने सबसे ऊँचे ब्याज वाले कर्ज़ पर थोड़ी अतिरिक्त रकम डालने से वह काफ़ी जल्दी खत्म होता है। आप जितना ब्याज बचाते हैं, वह उतनी ही जमा से मिलने वाली कमाई से ज़्यादा है।",
            "pa": "ਹਰ ਮਹੀਨੇ ਆਪਣੇ ਸਭ ਤੋਂ ਵੱਧ ਵਿਆਜ ਵਾਲੇ ਕਰਜ਼ੇ 'ਤੇ ਥੋੜ੍ਹੀ ਵਾਧੂ ਰਕਮ ਪਾਉਣ ਨਾਲ ਉਹ ਕਾਫ਼ੀ ਜਲਦੀ ਖਤਮ ਹੁੰਦਾ ਹੈ। ਤੁਸੀਂ ਜਿੰਨਾ ਵਿਆਜ ਬਚਾਉਂਦੇ ਹੋ, ਉਹ ਉਸੇ ਰਕਮ ਦੀ ਜਮ੍ਹਾਂ ਤੋਂ ਮਿਲਣ ਵਾਲੀ ਕਮਾਈ ਤੋਂ ਵੱਧ ਹੈ।",
        },
        "idle_balance_fd": {
            "en": "A large amount is sitting in your savings account earning very little. Moving the portion you do not need soon into a fixed deposit earns more without putting it at market risk.",
            "hi": "आपके बचत खाते में बड़ी रकम पड़ी है जिस पर बहुत कम कमाई हो रही है। जो हिस्सा आपको जल्दी नहीं चाहिए, उसे सावधि जमा में ले जाने से बिना बाज़ार जोखिम के ज़्यादा कमाई होती है।",
            "pa": "ਤੁਹਾਡੇ ਬੱਚਤ ਖਾਤੇ ਵਿੱਚ ਵੱਡੀ ਰਕਮ ਪਈ ਹੈ ਜਿਸ 'ਤੇ ਬਹੁਤ ਘੱਟ ਕਮਾਈ ਹੋ ਰਹੀ ਹੈ। ਜਿਹੜਾ ਹਿੱਸਾ ਤੁਹਾਨੂੰ ਜਲਦੀ ਨਹੀਂ ਚਾਹੀਦਾ, ਉਸਨੂੰ ਮਿਆਦੀ ਜਮ੍ਹਾਂ ਵਿੱਚ ਲੈ ਜਾਣ ਨਾਲ ਬਿਨਾਂ ਬਾਜ਼ਾਰ ਜੋਖਮ ਦੇ ਵੱਧ ਕਮਾਈ ਹੁੰਦੀ ਹੈ।",
        },
        "ffd_reinvest": {
            "en": "One of your fixed deposits matures soon. If you do nothing it may sit idle at a low rate, so we are flagging it while you still have time to decide.",
            "hi": "आपकी एक सावधि जमा जल्द ही परिपक्व हो रही है। अगर आप कुछ नहीं करते तो वह कम दर पर बेकार पड़ी रह सकती है, इसलिए हम इसे तब बता रहे हैं जब आपके पास तय करने का समय है।",
            "pa": "ਤੁਹਾਡੀ ਇੱਕ ਮਿਆਦੀ ਜਮ੍ਹਾਂ ਜਲਦੀ ਹੀ ਪੂਰੀ ਹੋ ਰਹੀ ਹੈ। ਜੇ ਤੁਸੀਂ ਕੁਝ ਨਹੀਂ ਕਰਦੇ ਤਾਂ ਉਹ ਘੱਟ ਦਰ 'ਤੇ ਵਿਹਲੀ ਪਈ ਰਹਿ ਸਕਦੀ ਹੈ, ਇਸ ਲਈ ਅਸੀਂ ਇਹ ਉਦੋਂ ਦੱਸ ਰਹੇ ਹਾਂ ਜਦੋਂ ਤੁਹਾਡੇ ਕੋਲ ਫ਼ੈਸਲਾ ਕਰਨ ਦਾ ਸਮਾਂ ਹੈ।",
        },
        "conservative_start": {
            "en": "A liquid deposit is a safe base to plan from. You can withdraw it at any time, so it is a sensible first step before committing to anything longer.",
            "hi": "तरल जमा योजना बनाने के लिए एक सुरक्षित आधार है। आप इसे कभी भी निकाल सकते हैं, इसलिए किसी लंबी अवधि की चीज़ में पैसा लगाने से पहले यह एक समझदारी भरा पहला कदम है।",
            "pa": "ਤਰਲ ਜਮ੍ਹਾਂ ਯੋਜਨਾ ਬਣਾਉਣ ਲਈ ਇੱਕ ਸੁਰੱਖਿਅਤ ਆਧਾਰ ਹੈ। ਤੁਸੀਂ ਇਸਨੂੰ ਕਦੇ ਵੀ ਕੱਢ ਸਕਦੇ ਹੋ, ਇਸ ਲਈ ਕਿਸੇ ਲੰਬੀ ਮਿਆਦ ਵਾਲੀ ਚੀਜ਼ ਵਿੱਚ ਪੈਸਾ ਲਾਉਣ ਤੋਂ ਪਹਿਲਾਂ ਇਹ ਇੱਕ ਸਮਝਦਾਰੀ ਵਾਲਾ ਪਹਿਲਾ ਕਦਮ ਹੈ।",
        },
        "expense_optimization": {
            "en": "Your income and your spending are almost the same, so there is very little left to invest. We are not suggesting a product here — reducing expenses first will do more for you than anything we could sell.",
            "hi": "आपकी आय और आपका खर्च लगभग बराबर हैं, इसलिए निवेश के लिए बहुत कम बचता है। हम यहाँ कोई उत्पाद नहीं सुझा रहे — पहले खर्च कम करना आपके लिए उससे ज़्यादा फ़ायदेमंद होगा जो हम बेच सकते हैं।",
            "pa": "ਤੁਹਾਡੀ ਆਮਦਨ ਅਤੇ ਤੁਹਾਡਾ ਖਰਚ ਲਗਭਗ ਬਰਾਬਰ ਹਨ, ਇਸ ਲਈ ਨਿਵੇਸ਼ ਲਈ ਬਹੁਤ ਘੱਟ ਬਚਦਾ ਹੈ। ਅਸੀਂ ਇੱਥੇ ਕੋਈ ਉਤਪਾਦ ਨਹੀਂ ਸੁਝਾ ਰਹੇ — ਪਹਿਲਾਂ ਖਰਚ ਘਟਾਉਣਾ ਤੁਹਾਡੇ ਲਈ ਉਸ ਤੋਂ ਵੱਧ ਫ਼ਾਇਦੇਮੰਦ ਹੋਵੇਗਾ ਜੋ ਅਸੀਂ ਵੇਚ ਸਕਦੇ ਹਾਂ।",
        },
    },
    # ── Device trust explanations (Profile screen) ────────────────────────
    "device_trust": {
        "TRUSTED": {
            "en": "We recognise this device. You have signed in from it before, so we do not need to ask you extra questions during normal activity.",
            "hi": "हम इस डिवाइस को पहचानते हैं। आप पहले भी इससे साइन इन कर चुके हैं, इसलिए सामान्य गतिविधि के दौरान हमें आपसे अतिरिक्त सवाल पूछने की ज़रूरत नहीं है।",
            "pa": "ਅਸੀਂ ਇਸ ਡਿਵਾਈਸ ਨੂੰ ਪਛਾਣਦੇ ਹਾਂ। ਤੁਸੀਂ ਪਹਿਲਾਂ ਵੀ ਇਸ ਤੋਂ ਸਾਈਨ ਇਨ ਕਰ ਚੁੱਕੇ ਹੋ, ਇਸ ਲਈ ਆਮ ਗਤੀਵਿਧੀ ਦੌਰਾਨ ਸਾਨੂੰ ਤੁਹਾਡੇ ਤੋਂ ਵਾਧੂ ਸਵਾਲ ਪੁੱਛਣ ਦੀ ਲੋੜ ਨਹੀਂ ਹੈ।",
        },
        "NEW": {
            "en": "This device is new to us. That is not a problem, but we will ask for extra verification on larger transactions until we have seen it a few more times.",
            "hi": "यह डिवाइस हमारे लिए नया है। यह कोई समस्या नहीं है, लेकिन जब तक हम इसे कुछ और बार न देख लें, बड़ी राशि के लेन-देन पर हम अतिरिक्त सत्यापन माँगेंगे।",
            "pa": "ਇਹ ਡਿਵਾਈਸ ਸਾਡੇ ਲਈ ਨਵਾਂ ਹੈ। ਇਹ ਕੋਈ ਸਮੱਸਿਆ ਨਹੀਂ ਹੈ, ਪਰ ਜਦੋਂ ਤੱਕ ਅਸੀਂ ਇਸਨੂੰ ਕੁਝ ਹੋਰ ਵਾਰ ਨਾ ਵੇਖ ਲਈਏ, ਵੱਡੀ ਰਕਮ ਦੇ ਲੈਣ-ਦੇਣ 'ਤੇ ਅਸੀਂ ਵਾਧੂ ਤਸਦੀਕ ਮੰਗਾਂਗੇ।",
        },
        "UNTRUSTED": {
            "en": "We do not yet trust this device. Every sensitive action from it will need verification. If you did not add this device, remove it and change your MPIN.",
            "hi": "हम अभी इस डिवाइस पर भरोसा नहीं करते। इससे किए गए हर संवेदनशील काम के लिए सत्यापन ज़रूरी होगा। अगर आपने यह डिवाइस नहीं जोड़ा है, तो इसे हटाएँ और अपना MPIN बदलें।",
            "pa": "ਅਸੀਂ ਹਾਲੇ ਇਸ ਡਿਵਾਈਸ 'ਤੇ ਭਰੋਸਾ ਨਹੀਂ ਕਰਦੇ। ਇਸ ਤੋਂ ਕੀਤੇ ਹਰ ਸੰਵੇਦਨਸ਼ੀਲ ਕੰਮ ਲਈ ਤਸਦੀਕ ਜ਼ਰੂਰੀ ਹੋਵੇਗੀ। ਜੇ ਤੁਸੀਂ ਇਹ ਡਿਵਾਈਸ ਨਹੀਂ ਜੋੜਿਆ, ਤਾਂ ਇਸਨੂੰ ਹਟਾਓ ਅਤੇ ਆਪਣਾ MPIN ਬਦਲੋ।",
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
