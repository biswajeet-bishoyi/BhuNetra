"""
backend/services/ocr_space_service.py — Production OCR.Space Multilingual Indic OCR Engine.

Integrates OCR.Space API (https://api.ocr.space/parse/image) using OCR Engine 3
with automatic multilingual detection across Hindi, Bengali, Telugu, Tamil,
Kannada, Malayalam, Gujarati, Marathi, Punjabi, Odia, Urdu, Assamese, Sanskrit, and English.

Performs:
  1. Direct image submission to OCR.Space Engine 3 with autolanguage & scaling.
  2. Unicode normalization (NFKC) and noise filtering.
  3. Multilingual keyword-dictionary-based field extraction for all 13 canonical land record attributes.
  4. Unit conversions from regional Indic measurements (Bigha, Biswa, Gunta, Cent, Ground, etc.) to sq.m.
  5. Calibrated multi-factor confidence scoring.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
    _candidates = [
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[1] / ".env",
        Path.cwd() / ".env"
    ]
    for _p in _candidates:
        if _p.exists():
            load_dotenv(_p)
            break
except Exception:
    pass

import httpx
from PIL import Image, ImageOps

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_OCR_KEY = "K81655746788957"
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", DEFAULT_OCR_KEY).strip() or DEFAULT_OCR_KEY
OCR_SPACE_ENDPOINT = os.getenv("OCR_SPACE_ENDPOINT", "https://api.ocr.space/parse/image").strip()
OCR_SPACE_ENGINE = str(os.getenv("OCR_SPACE_ENGINE", "3")).strip()
OCR_SPACE_LANGUAGE = os.getenv("OCR_SPACE_LANGUAGE", "auto").strip()
OCR_SPACE_TIMEOUT = float(os.getenv("OCR_SPACE_TIMEOUT", "45.0"))

SUPPORTED_LANGUAGES_LIST = [
    {"code": "auto", "label": "🌐 Auto-Detect Indic Language", "native": "Auto-Detect (14+ Languages)"},
    {"code": "hin", "label": "🇮🇳 Hindi (हिन्दी)", "native": "हिन्दी"},
    {"code": "ben", "label": "🇮🇳 Bengali (বাংলা)", "native": "বাংলা"},
    {"code": "tel", "label": "🇮🇳 Telugu (తెలుగు)", "native": "తెలుగు"},
    {"code": "tam", "label": "🇮🇳 Tamil (தமிழ்)", "native": "தமிழ்"},
    {"code": "kan", "label": "🇮🇳 Kannada (ಕನ್ನಡ)", "native": "ಕನ್ನಡ"},
    {"code": "mal", "label": "🇮🇳 Malayalam (മലയാളം)", "native": "മലയാളം"},
    {"code": "guj", "label": "🇮🇳 Gujarati (ગુજરાતી)", "native": "ગુજરાતી"},
    {"code": "mar", "label": "🇮🇳 Marathi (मराठी)", "native": "मराठी"},
    {"code": "pan", "label": "🇮🇳 Punjabi (ਪੰਜਾਬੀ)", "native": "ਪੰਜਾਬੀ"},
    {"code": "ori", "label": "🇮🇳 Odia (ଓଡ଼ିଆ)", "native": "ଓଡ଼ିଆ"},
    {"code": "urd", "label": "🇮🇳 Urdu (اردو)", "native": "اردو"},
    {"code": "asm", "label": "🇮🇳 Assamese (অসমীয়া)", "native": "অসমীয়া"},
    {"code": "san", "label": "🇮🇳 Sanskrit (संस्कृतम्)", "native": "संस्कृतम्"},
    {"code": "eng", "label": "🇬🇧 English", "native": "English"},
]

# ---------------------------------------------------------------------------
# Regional Unit Conversions to Standard Square Metres (sq.m)
# ---------------------------------------------------------------------------

UNIT_CONVERSIONS_TO_SQM = {
    "sqm": 1.0, "sq.m": 1.0, "sq m": 1.0, "square metre": 1.0, "square meter": 1.0, "చ.మీ": 1.0, "वर्ग मीटर": 1.0,
    "sq yards": 0.836127, "sq yd": 0.836127, "sq.yd": 0.836127, "gaj": 0.836127, "गज": 0.836127,
    "acre": 4046.86, "acres": 4046.86, "ekaram": 4046.86, "ఎకరాలు": 4046.86, "एकड़": 4046.86, "একর": 4046.86, "ஏக்கர்": 4046.86, "ಎಕರೆ": 4046.86,
    "hectare": 10000.0, "hectares": 10000.0, "हेक्टेयर": 10000.0, "హెక్టార్": 10000.0, "ஹெக்டேர்": 10000.0,
    "guntha": 101.17, "gunthas": 101.17, "gunta": 101.17, "guntas": 101.17, "గుంటలు": 101.17, "गुंठा": 101.17, "குண்டா": 101.17,
    "cent": 40.4686, "cents": 40.4686, "సెంట్లు": 40.4686, "சென்ட்": 40.4686, "सेंन्ट": 40.4686,
    "ground": 222.96, "grounds": 222.96, "கிரவுண்ட்": 222.96,
    "bigha": 2529.285, "बीघा": 2529.285, "বিঘা": 2529.285, "ਵੀਘਾ": 2529.285,
    "biswa": 126.464, "बिस्वा": 126.464, "ਵਿਸਵਾ": 126.464,
    "katha": 126.46, "कट्ठा": 126.46, "কাঠা": 126.46,
    "kanal": 505.857, "कनाल": 505.857, "ਕਨਾਲ": 505.857,
    "marla": 25.293, "मरला": 25.293, "ਮਰਲਾ": 25.293,
    "decimal": 40.4686, "डेसिमल": 40.4686, "ডেসিমেল": 40.4686,
}


def get_supported_languages() -> List[Dict[str, str]]:
    return SUPPORTED_LANGUAGES_LIST


def normalize_language_code(lang: Optional[str]) -> str:
    if not lang:
        return "auto"
    cleaned = str(lang).strip().lower()
    valid_codes = {item["code"] for item in SUPPORTED_LANGUAGES_LIST}
    if cleaned in valid_codes:
        return cleaned
    alias_map = {
        "auto": "auto", "hindi": "hin", "hi": "hin", "bengali": "ben", "bn": "ben",
        "telugu": "tel", "te": "tel", "tamil": "tam", "ta": "tam",
        "kannada": "kan", "kn": "kan", "marathi": "mar", "mr": "mar",
        "gujarati": "guj", "gu": "guj", "punjabi": "pan", "pa": "pan",
        "malayalam": "mal", "ml": "mal", "odia": "ori", "or": "ori",
        "urdu": "urd", "ur": "urd", "assamese": "asm", "as": "asm",
        "sanskrit": "san", "sa": "san", "english": "eng", "en": "eng"
    }
    return alias_map.get(cleaned, "auto")


# ---------------------------------------------------------------------------
# OCR.Space API Caller
# ---------------------------------------------------------------------------

def call_ocr_space_api(
    image_bytes: bytes,
    language: str = "auto",
    engine: str = OCR_SPACE_ENGINE,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submits image bytes to OCR.Space API with Engine 3 and returns clean parsed text.
    """
    key = api_key or OCR_SPACE_API_KEY
    endpoint = OCR_SPACE_ENDPOINT

    # Preprocess image to optimal dimensions
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img).convert("RGB")
        max_dim = 1800
        if max(img.size) > max_dim:
            scale = max_dim / max(img.size)
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90, optimize=True)
        processed_bytes = buf.getvalue()
    except Exception:
        processed_bytes = image_bytes

    b64_img = f"data:image/jpeg;base64,{base64.b64encode(processed_bytes).decode('ascii')}"

    # Parameters per master prompt specification:
    # apikey, OCREngine=3, language=auto, scale=true, isOverlayRequired=false
    payload = {
        "apikey": key,
        "base64Image": b64_img,
        "language": normalize_language_code(language),
        "isOverlayRequired": False,
        "OCREngine": str(engine) if engine in {"1", "2", "3"} else "3",
        "detectOrientation": True,
        "scale": True,
        "isTable": True,
    }

    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=OCR_SPACE_TIMEOUT) as client:
            resp = client.post(endpoint, data=payload)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"OCR.Space API network connection error: {exc}") from exc

    dur_ms = round((time.perf_counter() - t0) * 1000.0, 1)

    if resp.status_code != 200:
        raise RuntimeError(f"OCR.Space HTTP {resp.status_code}: {resp.text[:300]}")

    try:
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"OCR.Space returned non-JSON response: {resp.text[:300]}") from exc

    if data.get("IsErroredOnProcessing", False):
        err = data.get("ErrorMessage") or "OCR.Space processing error"
        if isinstance(err, list):
            err = "; ".join(err)
        raise RuntimeError(f"OCR.Space Error: {err}")

    parsed_results = data.get("ParsedResults", [])
    if not parsed_results:
        return {
            "parsed_text": "",
            "timing_ms": dur_ms,
            "engine_used": engine,
            "raw_response": data
        }

    first_res = parsed_results[0]
    raw_text = first_res.get("ParsedText", "")
    # Normalize unicode text (NFKC) and clean noise
    norm_text = unicodedata.normalize("NFKC", raw_text)
    clean_lines = [line.strip() for line in norm_text.splitlines() if line.strip()]
    cleaned_text = "\n".join(clean_lines)

    return {
        "parsed_text": cleaned_text,
        "timing_ms": dur_ms,
        "exit_code": first_res.get("FileParseExitCode", 1),
        "engine_used": engine,
        "raw_response": data
    }


# ---------------------------------------------------------------------------
# Multilingual Keyword Dictionaries & Intelligent Field Extraction
# ---------------------------------------------------------------------------

MULTILINGUAL_DICTIONARY = {
    "state": [
        r"state", r"राज्य", r"రాష్ట్రం", r"রাজ্য", r"மாநிலம்", r"રાજ્ય", r"ರಾಜ್ಯ", r"സംസ്ഥാനം", r"ਰਾਜ",
        r"Telangana", r"Uttar Pradesh", r"Odisha", r"Delhi", r"Rajasthan", r"Maharashtra",
        r"Tamil Nadu", r"Karnataka", r"Gujarat", r"West Bengal", r"Punjab", r"Kerala", r"Assam"
    ],
    "district": [
        r"district", r"dist\b", r"जिला", r"जिल्ला", r"జిల్లా", r"জেলা", r"மாவட்டம்", r"જિલ્લો", r"ಜಿಲ್ಲೆ", r"ജില്ല", r"ਜ਼ਿਲ੍ਹਾ",
        r"Rangareddy", r"Lucknow", r"Khordha", r"South Delhi", r"Bhilwara", r"Pune", r"Chennai", r"Kanchipuram", r"Hyderabad"
    ],
    "village": [
        r"village", r"mauza", r"moza", r"ग्राम", r"गांव", r"मौजा", r"గ్రామం", r"గ్రామము", r"গ্রাম", r"கிராமம்", r"ગામ", r"ಗ್ರಾಮ", r"ഗ്രാമം", r"ਪਿੰਡ",
        r"Shamshabad", r"Mamidipally", r"Kothwalguda", r"Chandrasekharpur", r"Sangam Vihar", r"Dehramau", r"Mandalgarh", r"Haveli"
    ],
    "survey_no": [
        r"survey\s*(?:no|number|#)?", r"సర్వే\s*నం(?:బరు)?", r"खसरा\s*(?:संख्या|नं|नंबर)", r"गाटा\s*(?:सं(?:ख्या)?)?",
        r"सर्वे\s*नं", r"புல\s*எண்", r"સર્વે\s*નંબર", r"ಸರ್ವೆ\s*ನಂಬರ್", r"గట్\s*నం", r"गट\s*(?:क्रमांक|नं)"
    ],
    "khatian_no": [
        r"khatian\s*(?:no|#)?", r"khata\s*(?:no|number|#)?", r"खाता\s*(?:संख्या|नं)?", r"खतौनी\s*(?:संख्या|नं)?",
        r"ఖాతా\s*నం", r"খতিয়ান", r"பட்டா\s*எண்", r"ਖਾਤਾ", r"ಖಾತೆ\s*ನಂ", r"ખાતા\s*નંબર", r"पट्ठा\s*नं"
    ],
    "owner_name": [
        r"pattadar\s*(?:name)?", r"owner\s*(?:name)?", r"పట్టాదారు\s*(?:పేరు)?", r"खातेदार(?:\s*का)?\s*नाम",
        r"मालिक", r"भूमिस्वामी", r"యజమాని", r"பட்டாதாரர்\s*பெயர்", r"মালিক", r"खातेदाराचे\s*नाव", r"જમીનદાર", r"ಮಾಲೀಕರು", r"ਮਾਲਕ"
    ],
    "father_or_husband": [
        r"father\s*(?:or\s*husband)?(?:\s*name)?", r"s/o", r"w/o", r"d/o", r"पिता\s*/\s*पति(?:\s*का)?\s*नाम",
        r"तండ్రి\s*/\s*భర్త\s*పేరు", r"தந்தை\s*/\s*கணவர்\s*பெயர்", r"পিতা", r"वडिलांचे\s*नाव", r"પિતાનું\s*નામ"
    ],
    "mandal": [
        r"mandal", r"tehsil", r"taluk", r"block", r"तहसील", r"तालुका", r"मण्डल", r"ప్రखंड", r"మండలం", r"வட்டம்", r"તાલુકો", r"ತಾಲೂಕು", r"താലൂക്ക്"
    ],
    "claimed_area_sqm": [
        r"area", r"extent", r"रकबा", r"क्षेत्रफल", r"విస్తీర్ణం", r"பரப்பு", r"ক্ষেত্রফল", r"વિસ્તાર", r"ವಿಸ್ತೀರ್ಣ", r"വിസ്തീർണ്ണം", r"ਰਕਬਾ", r"क्षेत्र"
    ],
    "land_use_claim": [
        r"land\s*(?:classification|use)", r"भूमि\s*वर्गीकरण", r"उपयोग", r"భూమి\s*వర్గీకరణ", r"நில\s*வகைப்பாடு", r"જમીન\s*વર્ગીકરણ"
    ],
    "deed_registration_no": [
        r"deed\s*(?:registration|reg)?\s*(?:no|#)?", r"registration\s*(?:no|#)?", r"दस्तावेज़\s*(?:संख्या|नं)?",
        r"पंजीकरण\s*(?:संख्या|नं)?", r"దస్తావేజు\s*(?:నమోదు)?\s*సంఖ్య", r"ஆவண\s*எண்"
    ],
    "ulpin": [
        r"ulpin", r"bhu-aadhaar", r"bhu\s*aadhaar", r"भू-आधार", r"యుఎల్పిఐఎన్"
    ]
}


def parse_indic_land_record_text(
    raw_text: str,
    language_hint: str = "auto",
    filename_hint: str = ""
) -> Dict[str, Any]:
    """
    Intelligent Dynamic Multilingual Cadastral Field Extraction across Indian regional languages.
    Delegates to dynamic multilingual parser with state-specific profiles.
    """
    try:
        from services import multilingual_parser
    except ImportError:
        from backend.services import multilingual_parser

    return multilingual_parser.parse_document_text(
        raw_text=raw_text,
        language_hint=language_hint,
        filename_hint=filename_hint
    )

