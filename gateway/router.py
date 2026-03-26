"""
gateway/router.py – Keyword-based intent classifier for BharatBot.

Routes user messages to the correct domain agent (AgriBot, HealthBot, or
LawBot) based on keyword matching across 7 Indian regional languages and
English.  No external API calls are made — this is a pure Python module.
"""

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword dictionaries – at least 10 keywords per domain per language
# ---------------------------------------------------------------------------

# Each domain maps language code -> list of keywords (lowercase)
_AGRI_KEYWORDS: dict[str, list[str]] = {
    "hi": [
        "फसल", "खेती", "किसान", "मिट्टी", "सिंचाई", "कीट", "उर्वरक",
        "मंडी", "बीज", "कृषि", "खाद", "पौधा", "रोग", "मौसम", "फल",
        "सब्जी", "धान", "गेहूं", "मक्का", "ट्रैक्टर", "बाढ़", "सूखा",
    ],
    "ta": [
        "விவசாயம்", "பயிர்", "விதை", "உரம்", "நீர்ப்பாசனம்", "பூச்சி",
        "மண்", "வானிலை", "மண்டி", "கடலை", "நெல்", "கோதுமை", "மக்காசோளம்",
        "தோட்டம்", "விவசாயி", "அறுவடை", "களை", "பூச்சிக்கொல்லி",
    ],
    "te": [
        "వ్యవసాయం", "పంట", "విత్తనాలు", "ఎరువు", "నీటిపారుదల", "పురుగు",
        "మట్టి", "వాతావరణం", "మండీ", "వరి", "గోధుమ", "మొక్కజొన్న",
        "రైతు", "కీటకనాశిని", "పంట వ్యాధి", "తోట", "అడవి",
    ],
    "kn": [
        "ಕೃಷಿ", "ಬೆಳೆ", "ಬಿತ್ತನೆ", "ಗೊಬ್ಬರ", "ನೀರಾವರಿ", "ಕೀಟ",
        "ಮಣ್ಣು", "ಹವಾಮಾನ", "ಮಂಡಿ", "ಭತ್ತ", "ಗೋಧಿ", "ರೈತ",
        "ಕೀಟನಾಶಕ", "ರೋಗ", "ತೋಟ", "ಮಳೆ", "ಬರ",
    ],
    "mr": [
        "शेती", "पीक", "बियाणे", "खत", "सिंचन", "कीड", "माती",
        "हवामान", "मंडी", "तांदूळ", "गहू", "मका", "शेतकरी",
        "कीटकनाशक", "रोग", "बाग", "दुष्काळ",
    ],
    "bn": [
        "কৃষি", "ফসল", "বীজ", "সার", "সেচ", "কীট", "মাটি",
        "আবহাওয়া", "মান্ডি", "ধান", "গম", "ভুট্টা", "কৃষক",
        "কীটনাশক", "রোগ", "বাগান", "খরা",
    ],
    "gu": [
        "ખેતી", "પાક", "બીજ", "ખાતર", "સિંચાઈ", "જીવાત", "માટી",
        "હવામાન", "મંડી", "ડાંગર", "ઘઉં", "મકાઈ", "ખેડૂત",
        "જંતુનાશક", "રોગ", "બગીચો", "દુષ્કાળ",
    ],
    "en": [
        "crop", "farm", "farmer", "agriculture", "soil", "irrigation",
        "fertilizer", "pesticide", "seed", "mandi", "weather", "harvest",
        "pest", "disease", "rice", "wheat", "maize", "sowing", "yield",
        "kisan", "agri", "paddy", "horticulture", "organic",
    ],
}

_HEALTH_KEYWORDS: dict[str, list[str]] = {
    "hi": [
        "बुखार", "दर्द", "खांसी", "डॉक्टर", "अस्पताल", "दवाई", "बीमार",
        "दवा", "नुस्खा", "स्वास्थ्य", "पेट", "सिरदर्द", "उल्टी", "दस्त",
        "रक्त", "ब्लड", "मलेरिया", "डेंगू", "वायरस", "टीका",
    ],
    "ta": [
        "காய்ச்சல்", "வலி", "இருமல்", "மருத்துவர்", "மருத்துவமனை",
        "மருந்து", "நோய்", "சுகாதாரம்", "வயிறு", "தலைவலி", "வாந்தி",
        "வயிற்றுப்போக்கு", "இரத்தம்", "மலேரியா", "டெங்கு", "தடுப்பூசி",
    ],
    "te": [
        "జ్వరం", "నొప్పి", "దగ్గు", "డాక్టర్", "ఆసుపత్రి", "మందు",
        "అనారోగ్యం", "ఆరోగ్యం", "కడుపు", "తలనొప్పి", "వాంతి", "విరేచనాలు",
        "రక్తం", "మలేరియా", "డెంగ్యూ", "టీకా",
    ],
    "kn": [
        "ಜ್ವರ", "ನೋವು", "ಕೆಮ್ಮು", "ವೈದ್ಯ", "ಆಸ್ಪತ್ರೆ", "ಔಷಧ",
        "ಖಾಯಿಲೆ", "ಆರೋಗ್ಯ", "ಹೊಟ್ಟೆ", "ತಲೆನೋವು", "ವಾಂತಿ", "ಭೇದಿ",
        "ರಕ್ತ", "ಮಲೇರಿಯಾ", "ಡೆಂಗಿ", "ಲಸಿಕೆ",
    ],
    "mr": [
        "ताप", "दुखणे", "खोकला", "डॉक्टर", "रुग्णालय", "औषध",
        "आजारी", "आरोग्य", "पोट", "डोकेदुखी", "उलटी", "जुलाब",
        "रक्त", "मलेरिया", "डेंगू", "लस",
    ],
    "bn": [
        "জ্বর", "ব্যথা", "কাশি", "ডাক্তার", "হাসপাতাল", "ওষুধ",
        "অসুস্থ", "স্বাস্থ্য", "পেট", "মাথাব্যথা", "বমি", "ডায়রিয়া",
        "রক্ত", "ম্যালেরিয়া", "ডেঙ্গু", "টিকা",
    ],
    "gu": [
        "તાવ", "દુખાવો", "ઉધરસ", "ડૉક્ટર", "હૉસ્પિટલ", "દવા",
        "બીમાર", "આરોગ્ય", "પેટ", "માથાનો દુઃખાવો", "ઉલ્ટી", "ઝાડા",
        "લોહી", "મેલેરિયા", "ડેન્ગ્યૂ", "રસી",
    ],
    "en": [
        "fever", "pain", "cough", "doctor", "hospital", "medicine",
        "sick", "health", "stomach", "headache", "vomit", "diarrhea",
        "blood", "malaria", "dengue", "vaccine", "symptom", "treatment",
        "clinic", "pharmacy", "infection", "disease", "ayush", "nhp",
    ],
}

_LAW_KEYWORDS: dict[str, list[str]] = {
    "hi": [
        "कानून", "एफआईआर", "न्यायालय", "पुलिस", "वकील", "अधिकार",
        "आरटीआई", "जमानत", "मुकदमा", "गिरफ्तारी", "अनुबंध", "धारा",
        "आईपीसी", "रसीद", "उपभोक्ता", "शिकायत", "न्याय",
    ],
    "ta": [
        "சட்டம்", "எஃப்.ஐ.ஆர்", "நீதிமன்றம்", "போலீஸ்", "வழக்கறிஞர்",
        "உரிமை", "ஆர்.டி.ஐ", "பிணை", "வழக்கு", "கைது", "ஒப்பந்தம்",
        "பிரிவு", "ஐபிசி", "நுகர்வோர்", "புகார்", "நீதி",
    ],
    "te": [
        "చట్టం", "ఎఫ్ఐఆర్", "న్యాయస్థానం", "పోలీస్", "న్యాయవాది",
        "హక్కులు", "ఆర్టీఐ", "బెయిల్", "కేసు", "అరెస్ట్", "ఒప్పందం",
        "సెక్షన్", "ఐపీసీ", "వినియోగదారుడు", "ఫిర్యాదు", "న్యాయం",
    ],
    "kn": [
        "ಕಾನೂನು", "ಎಫ್ಐಆರ್", "ನ್ಯಾಯಾಲಯ", "ಪೊಲೀಸ್", "ವಕೀಲ",
        "ಹಕ್ಕು", "ಆರ್ಟಿಐ", "ಜಾಮೀನು", "ಪ್ರಕರಣ", "ಬಂಧನ", "ಒಪ್ಪಂದ",
        "ಸೆಕ್ಷನ್", "ಐಪಿಸಿ", "ಗ್ರಾಹಕ", "ದೂರು", "ನ್ಯಾಯ",
    ],
    "mr": [
        "कायदा", "एफआयआर", "न्यायालय", "पोलीस", "वकील", "हक्क",
        "आरटीआय", "जामीन", "खटला", "अटक", "करार", "कलम",
        "आयपीसी", "ग्राहक", "तक्रार", "न्याय",
    ],
    "bn": [
        "আইন", "এফআইআর", "আদালত", "পুলিশ", "আইনজীবী", "অধিকার",
        "আরটিআই", "জামিন", "মামলা", "গ্রেপ্তার", "চুক্তি", "ধারা",
        "আইপিসি", "ভোক্তা", "অভিযোগ", "ন্যায়",
    ],
    "gu": [
        "કાયદો", "એફઆઈઆર", "ન્યાયાલય", "પોલીસ", "વકીલ", "અધિકાર",
        "આરટીઆઈ", "જામીન", "કેસ", "ધરપકડ", "કરાર", "કલમ",
        "આઈપીસી", "ગ્રાહક", "ફરિયાદ", "ન્યાય",
    ],
    "en": [
        "law", "fir", "court", "police", "lawyer", "rights", "rti",
        "bail", "case", "arrest", "contract", "section", "ipc", "crpc",
        "consumer", "complaint", "justice", "legal", "advocate", "judge",
        "tribunal", "lok adalat", "affidavit", "petition", "appeal",
    ],
}


def _normalize(text: str) -> str:
    """Normalize text for keyword matching by lowercasing.

    Args:
        text: Raw input string.

    Returns:
        Lowercased string.
    """
    return text.lower()


def _count_keyword_hits(text: str, keyword_list: list[str]) -> int:
    """Count how many keywords from the list appear in the text.

    Args:
        text: Normalized input text.
        keyword_list: List of keyword strings to match against.

    Returns:
        Integer count of keyword matches found.
    """
    count = 0
    for kw in keyword_list:
        if kw in text:
            count += 1
    return count


def classify_intent(text: str, lang: str = "hi") -> str:
    """Classify user intent and return the appropriate agent name.

    Uses keyword matching across all 7 supported languages and English to
    determine which domain agent should handle the user's message.
    Returns the agent with the highest keyword score.

    Args:
        text: The user's input message (in any supported language).
        lang: Detected ISO 639-1 language code (e.g. "hi", "ta").

    Returns:
        One of "agribot", "healthbot", or "lawbot".
        Defaults to "agribot" if no keywords match.
    """
    normalized = _normalize(text)

    agri_score = 0
    health_score = 0
    law_score = 0

    # Check keywords for all languages (text may contain mixed-language words)
    for language in _AGRI_KEYWORDS:
        agri_score += _count_keyword_hits(normalized, _AGRI_KEYWORDS[language])
        health_score += _count_keyword_hits(normalized, _HEALTH_KEYWORDS[language])
        law_score += _count_keyword_hits(normalized, _LAW_KEYWORDS[language])

    logger.info(
        "Intent scores — AgriBot: %d | HealthBot: %d | LawBot: %d (lang=%s)",
        agri_score, health_score, law_score, lang,
    )

    if agri_score == 0 and health_score == 0 and law_score == 0:
        logger.info("No keyword match found; defaulting to 'agribot'.")
        return "agribot"

    max_score = max(agri_score, health_score, law_score)
    if max_score == agri_score:
        return "agribot"
    elif max_score == health_score:
        return "healthbot"
    else:
        return "lawbot"
