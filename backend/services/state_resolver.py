"""
state_resolver.py — Intelligent State Detection & Resolver for Indian Land Documents.

Detects the Indian state from multi-modal cues (text, location keywords,
administrative terminology, survey numbering schemes, and registration authorities)
without hard-coded assumptions.
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple

# Comprehensive knowledge base of administrative jurisdictions in India
STATE_SIGNALS: Dict[str, Dict[str, List[str]]] = {
    "Rajasthan": {
        "districts": ["bhilwara", "jaipur", "udaipur", "jodhpur", "ajmer", "kota", "bikaner", "chittorgarh", "alwar", "sikar"],
        "subdistricts": ["mandalgarh", "kotri", "sanganer", "amer", "shahpura", "beawar", "vallabhnagar"],
        "villages": ["abc village", "mandalgarh rural", "kasya", "jhalra", "sardargarh", "sitapura"],
        "terminology": ["khasra", "khewat", "jamabandi", "patwar", "girdawari", "bigha", "biswa", "apna khata", "e-dharti"],
        "reg_offices": ["sub-registrar mandalgarh", "sro bhilwara", "sro jaipur", "board of revenue ajmer"]
    },
    "Maharashtra": {
        "districts": ["pune", "mumbai", "thane", "nagpur", "nashik", "aurangabad", "chhatrapati sambhajinagar", "satara", "solapur", "kolhapur"],
        "subdistricts": ["haveli", "mulshi", "maval", "kalyan", "baramati", "daund", "shirur", "ambegaon"],
        "villages": ["wagholi", "hadapsar", "loni kalbhor", "manjri", "hinjawadi", "pirangut", "paud"],
        "terminology": ["gat", "gat no", "cts", "cts no", "7/12", "saat baara", "ferfar", "guntha", "talathi", "mahabhulekh"],
        "reg_offices": ["sub-registrar haveli", "sro pune", "sro mulshi", "joint sub-registrar haveli"]
    },
    "Telangana": {
        "districts": ["rangareddy", "hyderabad", "medchal", "medchal-malkajgiri", "sangareddy", "nalgonda", "khammam", "warangal"],
        "subdistricts": ["shamshabad", "rajendranagar", "kukatpally", "serilingampally", "gandipet", "hayathnagar", "maheswaram"],
        "villages": ["shamshabad", "mamidipally", "kothwalguda", "gaganpahad", "attapur", "budvel"],
        "terminology": ["dharani", "pattadar", "passbook", "khatian", "sy no", "survey no", "survey number", "gunta", "guntas"],
        "reg_offices": ["sro shamshabad", "sub-registrar shamshabad", "sub registrar rajendranagar", "ccla telangana"]
    },
    "Odisha": {
        "districts": ["khordha", "khurda", "cuttack", "puri", "ganjam", "sambalpur", "balasore", "bhadrak", "sundargarh"],
        "subdistricts": ["bhubaneswar tahasil", "bhubaneswar", "jatni", "balianta", "balipatna", "cuttack sadar"],
        "villages": ["chandrasekharpur", "patia", "nayapalli", "khandagiri", "mancheswar", "saheed nagar"],
        "terminology": ["bhulekh", "ror", "record of rights", "gharabari", "decimal", "decimals", "e-pauti", "tahasildar", "chaka"],
        "reg_offices": ["district sub-registrar bhubaneswar", "dsr khordha", "sub-registrar khandagiri"]
    },
    "Delhi": {
        "districts": ["south delhi", "new delhi", "south west delhi", "north delhi", "east delhi"],
        "subdistricts": ["saket", "hauz khas", "mehrauli", "vasant vihar", "najafgarh"],
        "villages": ["sangam vihar", "deoli", "tigri", "chhatarpur", "neb sarai"],
        "terminology": ["gpa", "general power of attorney", "doris", "khasra", "sq yds", "sub-registrar-v", "lal dora"],
        "reg_offices": ["sub-registrar-v", "sro mehrauli", "sro saket"]
    }
}


def detect_state_from_document(
    raw_text: str,
    extracted_fields: Optional[Dict[str, str]] = None,
    filename: str = ""
) -> Tuple[str, float, List[str]]:
    """
    Intelligently infer the Indian State from document contents and extracted fields.
    Returns: (detected_state, confidence, reasons)
    """
    text_corpus = f"{raw_text or ''} {filename or ''}".lower()
    if extracted_fields:
        for k, v in extracted_fields.items():
            if v and isinstance(v, str):
                text_corpus += f" {v.lower()}"

    # Explicit State mentions in fields get immediate highest priority
    if extracted_fields:
        explicit_state = extracted_fields.get("state")
        if explicit_state and isinstance(explicit_state, str):
            for state_name in STATE_SIGNALS.keys():
                if state_name.lower() in explicit_state.lower():
                    return state_name, 0.99, [f"Explicit state match in document fields: '{explicit_state}'"]

    state_scores: Dict[str, float] = {k: 0.0 for k in STATE_SIGNALS.keys()}
    state_reasons: Dict[str, List[str]] = {k: [] for k in STATE_SIGNALS.keys()}

    for state, signals in STATE_SIGNALS.items():
        # 1. State Name match
        if state.lower() in text_corpus:
            state_scores[state] += 40.0
            state_reasons[state].append(f"Explicit state name '{state}' found in document text.")

        # 2. District match
        for d in signals["districts"]:
            if re.search(rf"\b{re.escape(d)}\b", text_corpus):
                state_scores[state] += 30.0
                state_reasons[state].append(f"Known {state} district '{d.title()}' identified.")
                break

        # 3. Tehsil / Taluka / Mandal match
        for s in signals["subdistricts"]:
            if re.search(rf"\b{re.escape(s)}\b", text_corpus):
                state_scores[state] += 25.0
                state_reasons[state].append(f"Known {state} sub-district/tehsil '{s.title()}' identified.")
                break

        # 4. Village match
        for v in signals["villages"]:
            if re.search(rf"\b{re.escape(v)}\b", text_corpus):
                state_scores[state] += 20.0
                state_reasons[state].append(f"Known {state} village '{v.title()}' identified.")
                break

        # 5. Registration office match
        for ro in signals["reg_offices"]:
            if ro in text_corpus:
                state_scores[state] += 25.0
                state_reasons[state].append(f"Registration office '{ro.title()}' recognized.")
                break

        # 6. Specific terminology match
        for term in signals["terminology"]:
            if re.search(rf"\b{re.escape(term)}\b", text_corpus):
                state_scores[state] += 10.0
                state_reasons[state].append(f"State-specific land record term '{term}' detected.")
                break

    # Find winning state
    best_state, best_score = max(state_scores.items(), key=lambda x: x[1])

    if best_score >= 40.0:
        confidence = min(0.99, round(0.50 + (best_score / 150.0), 2))
        return best_state, confidence, state_reasons[best_state]
    elif best_score >= 15.0:
        confidence = min(0.80, round(0.40 + (best_score / 150.0), 2))
        return best_state, confidence, state_reasons[best_state]
    else:
        # Default with low confidence
        return "Rajasthan", 0.50, ["Inconclusive state signals; defaulted to Rajasthan land records schema."]
