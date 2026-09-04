"""
backend/services/state_detector.py — Dynamic Pan-India State Detection Engine.

Analyzes raw multilingual OCR text, Indic script signatures, statutory form identifiers,
and administrative keywords to detect the originating state with high precision.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

try:
    from services.state_profiles import STATE_PROFILES
except ImportError:
    from backend.services.state_profiles import STATE_PROFILES


# Script Unicode ranges
SCRIPT_RANGES = {
    "Odia": (0x0B00, 0x0B7F),
    "Telugu": (0x0C00, 0x0C7F),
    "Tamil": (0x0B80, 0x0BFF),
    "Bengali": (0x0980, 0x09FF),
    "Kannada": (0x0C80, 0x0CFF),
    "Malayalam": (0x0D00, 0x0D7F),
    "Gujarati": (0x0A80, 0x0AFF),
    "Gurmukhi": (0x0A00, 0x0A7F),
    "Devanagari": (0x0900, 0x097F),
}


def detect_dominant_indic_script(text: str) -> Optional[str]:
    """Detect the primary regional Indic script present in the text."""
    counts = {script: 0 for script in SCRIPT_RANGES}
    for char in text:
        cp = ord(char)
        for script, (start, end) in SCRIPT_RANGES.items():
            if start <= cp <= end:
                counts[script] += 1
                break

    best_script, best_count = max(counts.items(), key=lambda x: x[1])
    return best_script if best_count >= 3 else None


def detect_state(raw_text: str, filename_hint: str = "") -> Tuple[str, float, List[str]]:
    """
    Intelligently infer the Indian State from multilingual OCR text and document cues.
    Returns: (detected_state, confidence, matched_signals)
    """
    if not raw_text and not filename_hint:
        return "Unknown", 0.0, ["No text or filename provided"]

    norm_text = unicodedata.normalize("NFKC", str(raw_text or ""))
    full_corpus = f"{norm_text}\n{filename_hint}"
    full_lower = full_corpus.lower()

    # Step 1: Check dominant Indic script
    dominant_script = detect_dominant_indic_script(norm_text)

    state_scores: Dict[str, float] = {k: 0.0 for k in STATE_PROFILES.keys()}
    state_signals: Dict[str, List[str]] = {k: [] for k in STATE_PROFILES.keys()}

    # Script-to-state boosts
    if dominant_script == "Odia":
        state_scores["Odisha"] += 50.0
        state_signals["Odisha"].append("Dominant Odia script detected")
    elif dominant_script == "Telugu":
        # Can be Telangana or AP, check cues
        if any(k in full_lower for k in ["dharani", "shamshabad", "rangareddy", "ts-dharani"]):
            state_scores["Telangana"] += 50.0
            state_signals["Telangana"].append("Dominant Telugu script with Telangana Dharani terminology")
        else:
            state_scores["Telangana"] += 35.0
            state_signals["Telangana"].append("Telugu script detected")
    elif dominant_script == "Tamil":
        state_scores["Tamil Nadu"] += 55.0
        state_signals["Tamil Nadu"].append("Dominant Tamil script detected")
    elif dominant_script == "Bengali":
        state_scores["West Bengal"] += 45.0
        state_signals["West Bengal"].append("Dominant Bengali/Assamese script detected")
    elif dominant_script == "Kannada":
        state_scores["Karnataka"] += 55.0
        state_signals["Karnataka"].append("Dominant Kannada script detected")

    # Step 2: High-priority statutory document forms & unique keywords
    if re.search(r"Schedule\s*1\s*Form\s*No\.?\s*39-?A", norm_text, re.IGNORECASE) or "ଓଡିଶା ସରକାର" in norm_text or "ଓଡ଼ିଶା" in norm_text:
        state_scores["Odisha"] += 90.0
        state_signals["Odisha"].append("Odisha statutory record indicator: 'Schedule 1 Form No.39-A' / 'ଓଡିଶା ସରକାର'")

    if "dharani" in full_lower or "ts-dharani" in full_lower or "ధరణి" in norm_text:
        state_scores["Telangana"] += 90.0
        state_signals["Telangana"].append("Telangana statutory record indicator: Dharani RoR")

    if "7/12" in norm_text or "सातबारा" in norm_text or "mahabhulekh" in full_lower:
        state_scores["Maharashtra"] += 90.0
        state_signals["Maharashtra"].append("Maharashtra statutory 7/12 (Satbara) indicator")

    if "patta" in full_lower and "chitta" in full_lower or "பட்டா" in norm_text:
        state_scores["Tamil Nadu"] += 85.0
        state_signals["Tamil Nadu"].append("Tamil Nadu Patta Chitta statutory indicator")

    if "rtc" in full_lower and "pahani" in full_lower or "ಪಹಣಿ" in norm_text:
        state_scores["Karnataka"] += 85.0
        state_signals["Karnataka"].append("Karnataka RTC / Pahani statutory indicator")

    # Step 3: Match profile keywords, districts, subdistricts
    for state_name, profile in STATE_PROFILES.items():
        # Match state keywords
        for kw in profile.get("state_keywords", []):
            if kw.lower() in full_lower:
                state_scores[state_name] += 30.0
                state_signals[state_name].append(f"Keyword match: '{kw}'")
                break

        # Match districts
        for dist in profile.get("districts", []):
            if re.search(rf"\b{re.escape(dist.lower())}\b", full_lower) or dist in norm_text:
                state_scores[state_name] += 25.0
                state_signals[state_name].append(f"District match: '{dist}'")
                break

        # Match subdistricts
        for sub in profile.get("subdistricts", []):
            if re.search(rf"\b{re.escape(sub.lower())}\b", full_lower) or sub in norm_text:
                state_scores[state_name] += 20.0
                state_signals[state_name].append(f"Subdistrict match: '{sub}'")
                break

    best_state, best_score = max(state_scores.items(), key=lambda x: x[1])

    if best_score >= 40.0:
        conf = min(0.99, round(0.70 + (best_score / 200.0), 3))
        return best_state, conf, state_signals[best_state]
    elif best_score >= 20.0:
        conf = min(0.85, round(0.50 + (best_score / 200.0), 3))
        return best_state, conf, state_signals[best_state]
    else:
        return "Unknown", 0.0, ["Inconclusive state signals"]
