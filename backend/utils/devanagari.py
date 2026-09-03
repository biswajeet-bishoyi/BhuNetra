"""
utils/devanagari.py — High-precision Devanagari (Hindi) to English transliteration & translation engine
for BhuNetra AI cadastral GIS localization.
"""

from __future__ import annotations
import re
from typing import Dict, Tuple

# Pre-compiled dictionary of known Indian States, Districts, Tehsils & Land Terms
DEVANAGARI_GEOGRAPHIC_DICTIONARY: Dict[str, str] = {
    # States
    "राजस्थान": "Rajasthan",
    "उत्तर प्रदेश": "Uttar Pradesh",
    "उत्तरप्रदेश": "Uttar Pradesh",
    "मध्य प्रदेश": "Madhya Pradesh",
    "मध्यप्रदेश": "Madhya Pradesh",
    "बिहार": "Bihar",
    "दिल्ली": "Delhi",
    "नई दिल्ली": "New Delhi",
    "हरियाणा": "Haryana",
    "पंजाब": "Punjab",
    "गुजरात": "Gujarat",
    "महाराष्ट्र": "Maharashtra",
    "ओडिशा": "Odisha",
    "उड़ीसा": "Odisha",
    "तमिलनाडु": "Tamil Nadu",
    "तमिल नाडू": "Tamil Nadu",
    "तेलंगाना": "Telangana",
    "कर्नाटक": "Karnataka",
    "उत्तराखंड": "Uttarakhand",
    "झारखंड": "Jharkhand",
    "छत्तीसगढ़": "Chhattisgarh",
    "पश्चिम बंगाल": "West Bengal",
    "हिमाचल प्रदेश": "Himachal Pradesh",

    # Rajasthan Districts & Tehsils
    "भीलवाड़ा": "Bhilwara",
    "भीलवाडा": "Bhilwara",
    "मांडलगढ़": "Mandalgarh",
    "माडलगढ़": "Mandalgarh",
    "मांडलगढ़ ग्रामीण": "Mandalgarh Rural",
    "कोटड़ी": "Kotri",
    "जयपुर": "Jaipur",
    "सांगानेर": "Sanganer",
    "आमेर": "Amer",
    "जोधपुर": "Jodhpur",
    "उदयपुर": "Udaipur",
    "कोटा": "Kota",
    "अजमेर": "Ajmer",
    "बीकानेर": "Bikaner",
    "अलवर": "Alwar",
    "सीकर": "Sikar",
    "भरतपुर": "Bharatpur",
    "पाली": "Pali",
    "बाड़मेर": "Barmer",
    "नागौर": "Nagaur",
    "झालावाड़": "Jhalawar",
    "चित्तौड़गढ़": "Chittorgarh",
    "दौसा": "Dausa",
    "टोंक": "Tonk",
    "चूरू": "Churu",
    "झुंझुनू": "Jhunjhunu",
    "सवाई माधोपुर": "Sawai Madhopur",
    "हनुमानगढ़": "Hanumangarh",
    "श्रीगंगानगर": "Sri Ganganagar",
    "धौलपुर": "Dholpur",
    "करौली": "Karauli",
    "प्रतापगढ़": "Pratapgarh",
    "राजसमंद": "Rajsamand",
    "सिरोही": "Sirohi",
    "जालोर": "Jalore",
    "बांसवाड़ा": "Banswara",
    "डूंगरपुर": "Dungarpur",

    # Uttar Pradesh Districts & Tehsils
    "लखनऊ": "Lucknow",
    "कानपुर": "Kanpur",
    "वाराणसी": "Varanasi",
    "बनारस": "Varanasi",
    "काशी": "Varanasi",
    "आगरा": "Agra",
    "प्रयागराज": "Prayagraj",
    "इलाहाबाद": "Prayagraj",
    "गाजियाबाद": "Ghaziabad",
    "नोएडा": "Noida",
    "ग्रेटर नोएडा": "Greater Noida",
    "मेरठ": "Meerut",
    "गोरखपुर": "Gorakhpur",
    "बरेली": "Bareilly",
    "अलीगढ़": "Aligarh",
    "मुरादाबाद": "Moradabad",
    "सहारनपुर": "Saharanpur",
    "झांसी": "Jhansi",
    "मथुरा": "Mathura",
    "अयोध्या": "Ayodhya",
    "फैजाबाद": "Ayodhya",
    "मुजफ्फरनगर": "Muzaffarnagar",
    "बुलंदशहर": "Bulandshahr",
    "फिरोजाबाद": "Firozabad",
    "मिर्जापुर": "Mirzapur",
    "सीतापुर": "Sitapur",
    "हरदोई": "Hardoi",
    "सुल्तानपुर": "Sultanpur",
    "बहराइच": "Bahraich",
    "गोंडा": "Gonda",
    "बस्ती": "Basti",
    "रायबरेली": "Raebareli",

    # Madhya Pradesh Districts
    "भोपाल": "Bhopal",
    "इंदौर": "Indore",
    "जबलपुर": "Jabalpur",
    "ग्वालियर": "Gwalior",
    "उज्जैन": "Ujjain",
    "सागर": "Sagar",
    "देवास": "Dewas",
    "सतना": "Satna",
    "रीवा": "Rewa",
    "रतलाम": "Ratlam",

    # Bihar Districts
    "पटना": "Patna",
    "गया": "Gaya",
    "मुजफ्फरपुर": "Muzaffarpur",
    "भागलपुर": "Bhagalpur",
    "दरभंगा": "Darbhanga",
    "पूर्णिया": "Purnia",
    "बिहारशरीफ": "Bihar Sharif",
    "आरा": "Arrah",
    "बेगूसराय": "Begusarai",
    "कटिहार": "Katihar",

    # Delhi / NCR Localities
    "संगम विहार": "Sangam Vihar",
    "शाहदरा": "Shahdara",
    "रोहिणी": "Rohini",
    "द्वारका": "Dwarka",
    "चांदनी चौक": "Chandni Chowk",
    "कनॉट प्लेस": "Connaught Place",
    "साकेत": "Saket",
    "वसंत कुंज": "Vasant Kunj",
    "लाजपत नगर": "Lajpat Nagar",
    "करोल बाग": "Karol Bagh",

    # Haryana Districts
    "गुरुग्राम": "Gurugram",
    "गुड़गांव": "Gurugram",
    "फरीदाबाद": "Faridabad",
    "अंबाला": "Ambala",
    "करनाल": "Karnal",
    "पानीपत": "Panipat",
    "रोहतक": "Rohtak",
    "हिसार": "Hisar",
    "सोनीपत": "Sonipat",
    "पंचकुला": "Panchkula",

    # Land Classifications
    "कृषि": "Agricultural",
    "अकृषि": "Non-Agricultural",
    "आवासीय": "Residential",
    "व्यावसायिक": "Commercial",
    "औद्योगिक": "Industrial",
    "सिंचित": "Irrigated Agricultural",
    "असिंचित": "Unirrigated Agricultural",
    "बंजर": "Barren / Wasteland",
    "चारागाह": "Pasture / Grazing",
    "आबादी": "Abadi / Residential",
    "नजूल": "Nazul Govt Land",
}

# Devanagari character mappings
CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'r', 'ढ़': 'rh', 'फ़': 'f',
    'क्ष': 'ksh', 'त्र': 'tr', 'ज्ञ': 'gy'
}

VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'अं': 'an', 'अः': 'ah'
}

MATRAS = {
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ं': 'n', 'ँ': 'n', 'ः': 'h'
}

VIRAMA = '्'


def is_devanagari(text: str) -> bool:
    """Return True if the text contains any Devanagari characters."""
    if not text:
        return False
    return bool(re.search(r'[\u0900-\u097F]', str(text)))


def transliterate_phonetic_devanagari(word: str) -> str:
    """Phonetic algorithmic transliteration of an arbitrary Devanagari word into English."""
    word = word.strip()
    if not word:
        return ""

    out = []
    i = 0
    n = len(word)
    while i < n:
        char = word[i]

        # Check for multi-char combinations
        if i + 1 < n and word[i:i+2] in CONSONANTS:
            base = CONSONANTS[word[i:i+2]]
            i += 2
        elif char in CONSONANTS:
            base = CONSONANTS[char]
            i += 1
        elif char in VOWELS:
            out.append(VOWELS[char])
            i += 1
            continue
        elif char in MATRAS:
            out.append(MATRAS[char])
            i += 1
            continue
        elif char == VIRAMA:
            # Virama suppresses inherent vowel of preceding consonant
            i += 1
            continue
        else:
            out.append(char)
            i += 1
            continue

        # Lookahead after consonant
        if i < n:
            next_char = word[i]
            if next_char in MATRAS:
                out.append(base + MATRAS[next_char])
                i += 1
            elif next_char == VIRAMA:
                out.append(base)
                i += 1
            elif next_char in CONSONANTS or next_char in VOWELS:
                out.append(base + 'a')
            else:
                out.append(base + 'a')
        else:
            # Word-final consonant usually drops inherent 'a' in modern Hindi
            out.append(base)

    res = "".join(out)
    return res.capitalize()


def devanagari_to_english(text: str) -> str:
    """
    Translates or transliterates Devanagari text into clean English.
    Checks dictionary first, then falls back to phonetic algorithm.
    Preserves existing English words untouched.
    """
    if not text or not str(text).strip():
        return ""

    cleaned = str(text).strip()
    if not is_devanagari(cleaned):
        return cleaned

    # Check exact dictionary match
    if cleaned in DEVANAGARI_GEOGRAPHIC_DICTIONARY:
        return DEVANAGARI_GEOGRAPHIC_DICTIONARY[cleaned]

    # Check case-folded or punctuation stripped
    norm = re.sub(r'[^\u0900-\u097F\s]', '', cleaned).strip()
    if norm in DEVANAGARI_GEOGRAPHIC_DICTIONARY:
        return DEVANAGARI_GEOGRAPHIC_DICTIONARY[norm]

    # Process word by word
    tokens = re.split(r'(\s+|[^\w\u0900-\u097F]+)', cleaned)
    converted_tokens = []
    for tok in tokens:
        if not tok or not tok.strip():
            converted_tokens.append(tok)
            continue
        if is_devanagari(tok):
            if tok in DEVANAGARI_GEOGRAPHIC_DICTIONARY:
                converted_tokens.append(DEVANAGARI_GEOGRAPHIC_DICTIONARY[tok])
            else:
                converted_tokens.append(transliterate_phonetic_devanagari(tok))
        else:
            converted_tokens.append(tok)

    result = "".join(converted_tokens)
    return result.strip()
