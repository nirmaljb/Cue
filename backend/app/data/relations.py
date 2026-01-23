"""Static dictionary for relation translations.

Maps English relation keys to translations in supported languages.
If a relation is not found, fallback to English.
"""

# Supported languages
SUPPORTED_LANGUAGES = ["en", "hi", "ta", "bn", "te"]

# Language metadata
LANGUAGE_INFO = {
    "en": {"name": "English", "native": "English", "flag": "🇬🇧", "code": "en-IN"},
    "hi": {"name": "Hindi", "native": "हिंदी", "flag": "🇮🇳", "code": "hi-IN"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "flag": "🇮🇳", "code": "ta-IN"},
    "bn": {"name": "Bengali", "native": "বাংলা", "flag": "🇮🇳", "code": "bn-IN"},
    "te": {"name": "Telugu", "native": "తెలుగు", "flag": "🇮🇳", "code": "te-IN"},
}

# Relation translations dictionary
# Key: lowercase English relation
# Value: dict with translations for each language
RELATIONS = {
    # Family - Male
    "son": {
        "en": "Son",
        "hi": "बेटा",
        "ta": "மகன்",
        "bn": "ছেলে",
        "te": "కొడుకు",
    },
    "father": {
        "en": "Father",
        "hi": "पिता",
        "ta": "தந்தை",
        "bn": "বাবা",
        "te": "నాన్న",
    },
    "grandfather": {
        "en": "Grandfather",
        "hi": "दादा",
        "ta": "தாத்தா",
        "bn": "দাদু",
        "te": "తాత",
    },
    "grandson": {
        "en": "Grandson",
        "hi": "पोता",
        "ta": "பேரன்",
        "bn": "নাতি",
        "te": "మనవడు",
    },
    "brother": {
        "en": "Brother",
        "hi": "भाई",
        "ta": "சகோதரன்",
        "bn": "ভাই",
        "te": "సోదరుడు",
    },
    "uncle": {
        "en": "Uncle",
        "hi": "चाचा",
        "ta": "மாமா",
        "bn": "কাকা",
        "te": "మామ",
    },
    "nephew": {
        "en": "Nephew",
        "hi": "भतीजा",
        "ta": "மருமகன்",
        "bn": "ভাইপো",
        "te": "మేనల్లుడు",
    },
    "husband": {
        "en": "Husband",
        "hi": "पति",
        "ta": "கணவர்",
        "bn": "স্বামী",
        "te": "భర్త",
    },
    
    # Family - Female
    "daughter": {
        "en": "Daughter",
        "hi": "बेटी",
        "ta": "மகள்",
        "bn": "মেয়ে",
        "te": "కూతురు",
    },
    "mother": {
        "en": "Mother",
        "hi": "माँ",
        "ta": "அம்மா",
        "bn": "মা",
        "te": "అమ్మ",
    },
    "grandmother": {
        "en": "Grandmother",
        "hi": "दादी",
        "ta": "பாட்டி",
        "bn": "দিদা",
        "te": "నానమ్మ",
    },
    "granddaughter": {
        "en": "Granddaughter",
        "hi": "पोती",
        "ta": "பேத்தி",
        "bn": "নাতনি",
        "te": "మనవరాలు",
    },
    "sister": {
        "en": "Sister",
        "hi": "बहन",
        "ta": "சகோதரி",
        "bn": "বোন",
        "te": "సోదరి",
    },
    "aunt": {
        "en": "Aunt",
        "hi": "चाची",
        "ta": "அத்தை",
        "bn": "কাকি",
        "te": "అత్త",
    },
    "niece": {
        "en": "Niece",
        "hi": "भतीजी",
        "ta": "மருமகள்",
        "bn": "ভাইঝি",
        "te": "మేనకోడలు",
    },
    "wife": {
        "en": "Wife",
        "hi": "पत्नी",
        "ta": "மனைவி",
        "bn": "স্ত্রী",
        "te": "భార్య",
    },
    
    # Extended Family
    "cousin": {
        "en": "Cousin",
        "hi": "चचेरा भाई",
        "ta": "உறவினர்",
        "bn": "জ্ঞাতি",
        "te": "బంధువు",
    },
    "in-law": {
        "en": "In-law",
        "hi": "ससुराल वाले",
        "ta": "மாமியார்",
        "bn": "শ্বশুরবাড়ির",
        "te": "అత్తమామలు",
    },
    "son-in-law": {
        "en": "Son-in-law",
        "hi": "दामाद",
        "ta": "மருமகன்",
        "bn": "জামাই",
        "te": "అల్లుడు",
    },
    "daughter-in-law": {
        "en": "Daughter-in-law",
        "hi": "बहू",
        "ta": "மருமகள்",
        "bn": "বৌমা",
        "te": "కోడలు",
    },
    
    # Non-Family
    "friend": {
        "en": "Friend",
        "hi": "मित्र",
        "ta": "நண்பர்",
        "bn": "বন্ধু",
        "te": "స్నేహితుడు",
    },
    "close friend": {
        "en": "Close Friend",
        "hi": "करीबी दोस्त",
        "ta": "நெருங்கிய நண்பர்",
        "bn": "ঘনিষ্ঠ বন্ধু",
        "te": "సన్నిహిత మిత్రుడు",
    },
    "neighbor": {
        "en": "Neighbor",
        "hi": "पड़ोसी",
        "ta": "பக்கத்து வீட்டுக்காரர்",
        "bn": "প্রতিবেশী",
        "te": "పొరుగువాడు",
    },
    "doctor": {
        "en": "Doctor",
        "hi": "डॉक्टर",
        "ta": "மருத்துவர்",
        "bn": "ডাক্তার",
        "te": "డాక్టర్",
    },
    "nurse": {
        "en": "Nurse",
        "hi": "नर्स",
        "ta": "செவிலியர்",
        "bn": "নার্স",
        "te": "నర్సు",
    },
    "caregiver": {
        "en": "Caregiver",
        "hi": "देखभालकर्ता",
        "ta": "பராமரிப்பாளர்",
        "bn": "যত্নশীল",
        "te": "సంరక్షకుడు",
    },
    "helper": {
        "en": "Helper",
        "hi": "सहायक",
        "ta": "உதவியாளர்",
        "bn": "সাহায্যকারী",
        "te": "సహాయకుడు",
    },
}


def get_relation(relation: str, lang: str = "en") -> str:
    """Get translated relation for a given language.
    
    Args:
        relation: English relation (case-insensitive)
        lang: Target language code (en, hi, ta, bn, te)
    
    Returns:
        Translated relation or original English if not found
    """
    # Normalize key
    key = relation.lower().strip()
    
    # Check if relation exists in dictionary
    if key in RELATIONS:
        translations = RELATIONS[key]
        # Return translation for language, fallback to English
        return translations.get(lang, translations.get("en", relation))
    
    # Relation not in dictionary - return original
    return relation


def get_language_info(lang: str) -> dict:
    """Get language metadata.
    
    Args:
        lang: Language code (en, hi, ta, bn, te)
    
    Returns:
        Language info dict with name, native, flag, code
    """
    return LANGUAGE_INFO.get(lang, LANGUAGE_INFO["en"])
