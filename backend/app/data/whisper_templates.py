"""Whisper audio templates for multi-language support.

Fixed templates with placeholders for name, relation, and routine.
Uses respectful language forms (आप/நீங்கள்/আপনি/మీరు).
"""

# Audio whisper templates per language
# {name} - Person's name (kept as-is, no translation)
# {relation} - Translated relation from dictionary
# {routine} - Translated routine text
WHISPER_TEMPLATES = {
    "en": {
        "full": (
            "This is {name}. They are your {relation}. "
            "You usually feel comfortable around them. "
            "{routine} "
            "You can take your time."
        ),
        "short": (
            "This is {name}. They are your {relation}. "
            "You're safe here."
        ),
    },
    "hi": {
        "full": (
            "यह {name} हैं। वे आपके {relation} हैं। "
            "आप इनके साथ आमतौर पर सहज महसूस करते हैं। "
            "{routine} "
            "आप आराम से समय ले सकते हैं।"
        ),
        "short": (
            "यह {name} हैं। वे आपके {relation} हैं। "
            "आप सुरक्षित हैं।"
        ),
    },
    "ta": {
        "full": (
            "இவர் {name}. இவர் உங்கள் {relation}. "
            "நீங்கள் இவருடன் பொதுவாக நிம்மதியாக உணர்கிறீர்கள். "
            "{routine} "
            "நீங்கள் நேரம் எடுத்துக் கொள்ளலாம்."
        ),
        "short": (
            "இவர் {name}. இவர் உங்கள் {relation}. "
            "நீங்கள் பாதுகாப்பாக இருக்கிறீர்கள்."
        ),
    },
    "bn": {
        "full": (
            "ইনি {name}। তিনি আপনার {relation}। "
            "আপনি সাধারণত তাঁর সঙ্গে স্বস্তি অনুভব করেন। "
            "{routine} "
            "আপনি তাঁর সাথে সময় কাটাতে পারেন।"
        ),
        "short": (
            "ইনি {name}। তিনি আপনার {relation}। "
            "আপনি নিরাপদ আছেন।"
        ),
    },
    "te": {
        "full": (
            "ఇది {name}. వారు మీ {relation}. "
            "మీరు సాధారణంగా వారితో సౌకర్యంగా అనిపిస్తారు. "
            "{routine} "
            "మీరు నెమ్మదిగా సమయం తీసుకోవచ్చు."
        ),
        "short": (
            "ఇది {name}. వారు మీ {relation}. "
            "మీరు సురక్షితంగా ఉన్నారు."
        ),
    },
}

# Routine prefix templates (for translating the routine sentence)
# These wrap the translated routine content
ROUTINE_PREFIXES = {
    "en": "You both enjoy {routine}.",
    "hi": "आप दोनों को {routine} करना पसंद है।",
    "ta": "நீங்கள் இருவரும் {routine} செய்வதை விரும்புகிறீர்கள்.",
    "bn": "আপনারা দু'জনেই {routine} করতে পছন্দ করেন।",
    "te": "మీరు ఇద్దరూ {routine} చేయడం ఇష్టపడతారు.",
}


def get_whisper_template(lang: str, has_routine: bool = True) -> str:
    """Get whisper template for a language.
    
    Args:
        lang: Language code (en, hi, ta, bn, te)
        has_routine: Whether to use full template (with routine) or short
    
    Returns:
        Template string with placeholders
    """
    templates = WHISPER_TEMPLATES.get(lang, WHISPER_TEMPLATES["en"])
    return templates["full"] if has_routine else templates["short"]


def format_whisper(
    name: str,
    relation: str,
    routine: str = None,
    lang: str = "en"
) -> str:
    """Format a complete whisper message.
    
    Args:
        name: Person's name (kept as-is)
        relation: Already-translated relation
        routine: Already-translated routine text (optional)
        lang: Language code
    
    Returns:
        Complete formatted whisper text
    """
    has_routine = bool(routine and routine.strip())
    template = get_whisper_template(lang, has_routine)
    
    if has_routine:
        return template.format(name=name, relation=relation, routine=routine)
    else:
        return template.format(name=name, relation=relation)
