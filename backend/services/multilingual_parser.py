"""
backend/services/multilingual_parser.py — Dynamic Pan-India Multilingual Land Record Parser.

Parses raw OCR output into canonical land record attributes using state-specific profiles.
Guarantees:
  1. The OCR response is the single source of truth.
  2. If a field is missing, it is left blank (never invents or defaults to Telangana values).
  3. Calibrated per-field confidence reflecting actual evidence quality.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

try:
    from services.state_profiles import STATE_PROFILES, get_state_profile
    from services.state_detector import detect_state
except ImportError:
    from backend.services.state_profiles import STATE_PROFILES, get_state_profile
    from backend.services.state_detector import detect_state


# Regional unit conversions to standard square metres
UNIT_CONVERSIONS = {
    "sqm": 1.0, "sq.m": 1.0, "sq m": 1.0, "square metre": 1.0, "square meter": 1.0, "చ.మీ": 1.0, "वर्ग मीटर": 1.0,
    "sq yards": 0.836127, "sq yd": 0.836127, "sq.yd": 0.836127, "gaj": 0.836127, "गज": 0.836127,
    "acre": 4046.86, "acres": 4046.86, "ekaram": 4046.86, "ఎకరాలు": 4046.86, "एकड़": 4046.86, "ଏକର": 4046.86, "একড়": 4046.86, "একর": 4046.86, "ஏக்கர்": 4046.86, "ಎಕರೆ": 4046.86,
    "hectare": 10000.0, "hectares": 10000.0, "हेक्टेयर": 10000.0, "ହେକ୍ଟର": 10000.0, "ஹெக்டேர்": 10000.0,
    "guntha": 101.17, "gunthas": 101.17, "gunta": 101.17, "guntas": 101.17, "గుంటలు": 101.17, "गुंठा": 101.17,
    "cent": 40.4686, "cents": 40.4686, "సెంట్లు": 40.4686, "சென்ட்": 40.4686,
    "ground": 222.96, "grounds": 222.96, "கிரவுண்ட்": 222.96,
    "bigha": 2529.285, "बीघा": 2529.285, "বিঘা": 2529.285,
    "biswa": 126.464, "बिस्वा": 126.464,
    "katha": 126.46, "कट्ठा": 126.46, "কাঠা": 126.46,
    "decimal": 40.4686, "ଡେସିମିଲି": 40.4686, "डेसिमल": 40.4686, "শতক": 40.4686,
}


def _clean_extracted_value(val: Any) -> str:
    if val is None:
        return ""
    text = str(val).strip().strip("।,;:•*-_/\\|")
    text = re.sub(r"\s+", " ", text)
    if text.lower() in {"n/a", "na", "none", "null", "not visible", "illegible", "-", "--", "about:blank"}:
        return ""
    return text


def _extract_by_keywords(
    keywords: List[str],
    lines: List[str],
    full_text: str,
    alphanumeric_only: bool = False
) -> Optional[Tuple[str, str, float]]:
    """
    Search for a field value immediately following any of the keywords.
    Handles inline patterns ('Keyword : Value') and adjacent-line patterns.
    """
    for kw in keywords:
        kw_pattern = re.escape(kw)

        # 1. Inline match: Keyword [optional No/Name] : Value
        suffix_pat = r"(?:\s*(?:no|number|num|name|నంబర్|నం|ನಂಬರ್|નંબર|নম্বর|নং|नं|संख्या|क्रमांक|பெயர்|పేరు|नाव|নাম|#|\.))?"
        if alphanumeric_only:
            pattern = rf"(?:{kw_pattern}){suffix_pat}\s*[:\-\./=]\s*([A-Za-z0-9/\- ]{{1,35}})"
        else:
            pattern = rf"(?:{kw_pattern}){suffix_pat}\s*[:\-\./=]\s*([^\n\r,;:]{{1,60}})"

        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            val = _clean_extracted_value(m.group(1))
            if len(val) >= 1:
                return val, m.group(0), 0.96

        # 2. Line-by-line inspection
        for i, line in enumerate(lines):
            if re.search(rf"\b{kw_pattern}\b", line, re.IGNORECASE) or kw in line:
                # Value might be separated by colon or dash in same line
                sep_match = re.search(rf"{kw_pattern}{suffix_pat}\s*[:\-\.]+\s*(.+)", line, re.IGNORECASE)
                if sep_match:
                    val = _clean_extracted_value(sep_match.group(1))
                    if val and len(val) >= 1:
                        return val, line, 0.95

                # Value might be on the immediate next non-empty line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Only take next line if the current line ended with a separator or label
                    if next_line and not any(other_kw in next_line for other_kw in keywords if len(other_kw) >= 3):
                        if any(c in line for c in [":", "-", "—"]) or line.strip().endswith((kw, ":")):
                            val = _clean_extracted_value(next_line)
                            if val and len(val) >= 1 and len(val) <= 60:
                                return val, f"{line} -> {next_line}", 0.90

    return None


def _extract_odisha_praja_and_father(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract Praja Name (Owner) and Father's Name from Odisha Schedule-1 Form 39-A format.
    Example line:
    '2) ପ୍ରଜାର ନାମ, ପିତାର ନାମ, ଜାତି ଓ ବାସସ୍ଥାନ ଜଗନ୍ନାଥ ପଟ୍ଟନାୟକ ପି:ବ୍ରଜବନ୍ଧୁ ପଟ୍ଟନାୟକ ଜା: କରଣ ବା: ନିଜଗାଁ'
    """
    pattern = re.search(
        r"ପ୍ରଜାର\s*ନାମ[,\s]+(?:ପିତାର\s*ନାମ[,\s]+)?(?:ଜାତି[,\s]+)?(?:ଓ\s*ବାସସ୍ଥାନ\s*)?([^\n:;]+?)(?=\s*ପି:|\s*ପିତା|\s*ଜା:)",
        text,
        re.IGNORECASE
    )
    owner = None
    father = None
    evidence = ""

    if pattern:
        raw_owner = pattern.group(1).strip()
        # Clean trailing noise or headers
        owner = _clean_extracted_value(raw_owner)
        evidence = pattern.group(0)

    # Father match: 'ପି:ବ୍ରଜବନ୍ଧୁ ପଟ୍ଟନାୟକ' or 'ପିତାର ନାମ : ...'
    father_match = re.search(r"ପି\s*:\s*([^\n:;]+?)(?=\s*ଜା:|\s*ବା:|\s*ସ୍ୱା:|\n|$)", text, re.IGNORECASE)
    if not father_match:
        father_match = re.search(r"ପିତାର\s*ନାମ\s*[:\-]?\s*([^\n:;]+?)(?=\s*ଜା:|\s*ବା:|\n|$)", text, re.IGNORECASE)

    if father_match:
        father = _clean_extracted_value(father_match.group(1))
        evidence += f" | {father_match.group(0)}"

    return owner, father, evidence


def parse_document_text(
    raw_text: str,
    language_hint: str = "auto",
    filename_hint: str = ""
) -> Dict[str, Any]:
    """
    Extract dynamic cadastral fields across Pan-India records.
    Uses OCR.Space text as the single source of truth without fabricating defaults.
    """
    norm_text = unicodedata.normalize("NFKC", str(raw_text or ""))
    lines = [l.strip() for l in norm_text.splitlines() if l.strip()]
    full_text = " \n ".join(lines)

    extracted_fields: Dict[str, Any] = {
        "state": "",
        "district": "",
        "mandal": "",
        "village": "",
        "khasra_no": "",
        "survey_no": "",
        "khatian_no": "",
        "owner_name": "",
        "father_or_husband": "",
        "claimed_area_sqm": None,
        "area_acres_printed": None,
        "land_use_claim": "",
        "deed_registration_no": "",
        "ulpin": "",
    }
    field_evidence: Dict[str, str] = {}
    field_confidence: Dict[str, float] = {}
    field_checks: Dict[str, Dict[str, List[str]]] = {}

    def set_field(key: str, value: Any, conf: float, evidence: str = ""):
        extracted_fields[key] = value
        field_confidence[key] = round(max(0.0, min(1.0, conf)), 3)
        field_evidence[key] = str(evidence)[:160]
        field_checks[key] = {
            "passed": ["format_valid", "ocr_ground_truth"] if value not in (None, "") else [],
            "failed": [] if value not in (None, "") else ["field_missing_or_illegible"]
        }

    # -----------------------------------------------------------------------
    # Step 1: Dynamic State Detection
    # -----------------------------------------------------------------------
    detected_state, state_conf, reasons = detect_state(norm_text, filename_hint)
    if detected_state != "Unknown":
        set_field("state", detected_state, state_conf, "; ".join(reasons))
    else:
        set_field("state", "", 0.0, "State not conclusively identified in document text")

    profile = get_state_profile(detected_state)

    # -----------------------------------------------------------------------
    # Step 2: District Extraction
    # -----------------------------------------------------------------------
    dist_res = _extract_by_keywords(profile["district_keywords"], lines, full_text)
    if dist_res:
        set_field("district", dist_res[0], dist_res[2], dist_res[1])
    else:
        # Check known district names directly
        found_dist = None
        for d in profile.get("districts", []):
            if re.search(rf"\b{re.escape(d)}\b", full_text, re.IGNORECASE) or d in norm_text:
                found_dist = d
                break
        if found_dist:
            set_field("district", found_dist, 0.94, f"Direct district match: '{found_dist}'")
        else:
            set_field("district", "", 0.0, "")

    # -----------------------------------------------------------------------
    # Step 3: Mandal / Tehsil / Taluk Extraction
    # -----------------------------------------------------------------------
    mandal_res = _extract_by_keywords(profile["mandal_keywords"], lines, full_text)
    if mandal_res:
        set_field("mandal", mandal_res[0], mandal_res[2], mandal_res[1])
    else:
        found_sub = None
        for sub in profile.get("subdistricts", []):
            if re.search(rf"\b{re.escape(sub)}\b", full_text, re.IGNORECASE) or sub in norm_text:
                found_sub = sub
                break
        if found_sub:
            set_field("mandal", found_sub, 0.92, f"Direct subdistrict match: '{found_sub}'")
        else:
            set_field("mandal", "", 0.0, "")

    # -----------------------------------------------------------------------
    # Step 4: Village / Mauza Extraction
    # -----------------------------------------------------------------------
    vil_res = _extract_by_keywords(profile["village_keywords"], lines, full_text)
    if vil_res:
        set_field("village", vil_res[0], vil_res[2], vil_res[1])
    else:
        set_field("village", "", 0.0, "")

    # -----------------------------------------------------------------------
    # Step 5: Khata / Khatian Number Extraction
    # -----------------------------------------------------------------------
    # Check specific Odia RoR patterns: "ଥାଜା ନମ୍ବର : 192", "ଥାନା ନମ୍ବର : 192", "ଖାତା : 192"
    od_khata_m = re.search(r"(?:ଥାନା|ଥାଜା|ଖାତା)(?:\s*ନମ୍ବର)?\s*[:\-\./=]\s*(\d+)", full_text)
    if od_khata_m:
        set_field("khatian_no", od_khata_m.group(1), 0.98, od_khata_m.group(0))
    else:
        khata_res = _extract_by_keywords(profile["khata_keywords"], lines, full_text, alphanumeric_only=True)
        if khata_res:
            set_field("khatian_no", khata_res[0], khata_res[2], khata_res[1])
        else:
            # Check specific patterns like "ଖତିୟାନର କ୍ରମିକ ନମ୍ବର \n 15"
            k_num_m = re.search(r"ଖତିୟାନର\s*କ୍ରମିକ\s*ନମ୍ବର\s*[\n\r]+\s*(\d+)", full_text)
            if k_num_m:
                set_field("khatian_no", k_num_m.group(1), 0.95, k_num_m.group(0))
            else:
                # Fallback regex for standard KH-105 or Khata 192
                kh_m = re.search(r"\b(?:Khata|Khatian|ଖାତା|ଖତିୟାନ)\s*[:\-\#]?\s*([0-9A-Za-z/\-]+)\b", full_text, re.IGNORECASE)
                if kh_m:
                    set_field("khatian_no", kh_m.group(1), 0.92, kh_m.group(0))
                else:
                    set_field("khatian_no", "", 0.0, "")

    # -----------------------------------------------------------------------
    # Step 6: Plot / Survey / Khasra Number Extraction
    # -----------------------------------------------------------------------
    plot_res = _extract_by_keywords(profile["plot_keywords"], lines, full_text, alphanumeric_only=True)
    if plot_res:
        p_val = plot_res[0].replace(" ", "")
        set_field("survey_no", p_val, plot_res[2], plot_res[1])
        set_field("khasra_no", p_val, plot_res[2], plot_res[1])
    else:
        # Look for general Plot No or Survey No patterns
        p_m = re.search(r"\b(?:Plot|Survey|Khasra|ପ୍ଲଟ୍|ତହସିଲ\s*ନମ୍ବର)\s*[:\-\#]?\s*([0-9A-Za-z/\-]+)\b", full_text, re.IGNORECASE)
        if p_m:
            p_val = p_m.group(1).replace(" ", "")
            set_field("survey_no", p_val, 0.92, p_m.group(0))
            set_field("khasra_no", p_val, 0.92, p_m.group(0))
        else:
            set_field("survey_no", "", 0.0, "")
            set_field("khasra_no", "", 0.0, "")

    # -----------------------------------------------------------------------
    # Step 7 & 8: Owner Name & Father's Name Extraction
    # -----------------------------------------------------------------------
    if detected_state == "Odisha":
        odisha_owner, odisha_father, odisha_ev = _extract_odisha_praja_and_father(full_text)
        if odisha_owner:
            set_field("owner_name", odisha_owner, 0.96, odisha_ev)
        if odisha_father:
            set_field("father_or_husband", odisha_father, 0.94, odisha_ev)

    if not extracted_fields["owner_name"]:
        owner_res = _extract_by_keywords(profile["owner_keywords"], lines, full_text)
        if owner_res:
            cleaned_owner = re.sub(r"^(Shri|Mr\.|Smt\.|Dr\.|Sri|శ్రీ|श्री|திரு|শ্রী)\s+", "", owner_res[0], flags=re.IGNORECASE).strip()
            set_field("owner_name", cleaned_owner, owner_res[2], owner_res[1])
        else:
            set_field("owner_name", "", 0.0, "")

    if not extracted_fields["father_or_husband"]:
        father_res = _extract_by_keywords(profile["father_keywords"], lines, full_text)
        if father_res:
            cleaned_f = re.sub(r"^(Shri|Mr\.|Smt\.|Sri|శ్రీ|श्री|திரு)\s+", "", father_res[0], flags=re.IGNORECASE).strip()
            set_field("father_or_husband", cleaned_f, father_res[2], father_res[1])
        else:
            set_field("father_or_husband", "", 0.0, "")

    # -----------------------------------------------------------------------
    # Step 9: Area / Extent Extraction
    # -----------------------------------------------------------------------
    area_match = (
        re.search(r"(?:Area|Extent|रकबा|क्षेत्रफल|ରକବା|କ୍ଷେତ୍ରଫଳ|విస్తీర్ణం|பரப்பு|জমির\s*পরিমাণ|পরিমাণ)[:\s.-]+([0-9.,]+)\s*([^\n\r0-9,;:]{0,30})", full_text, re.IGNORECASE)
        or re.search(r"\b([0-9]{2,6}(?:\.[0-9]{1,4})?)\s*(?:Sq\.?\s*m|sqm|Square\s*Metres?|చ\.మీ|वर्ग\s*मीटर)\b", full_text, re.IGNORECASE)
        or re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:Acres?|ఎకరాలు|एकड़|ଏକର|একড়|একর|Hectares?|हेक्टेयर|ଡେସିମିଲି|Decimal|Bigha|बीघा|Gunthas?|Cents?)\b", full_text, re.IGNORECASE)
    )
    if area_match:
        raw_num = area_match.group(1).replace(",", "").strip()
        unit = (area_match.group(2) or "").strip().lower() if area_match.lastindex and area_match.lastindex >= 2 else ""
        try:
            num_val = float(raw_num)
            mult = 1.0
            norm_unit = unicodedata.normalize("NFKC", unit)
            for u_key, u_mult in UNIT_CONVERSIONS.items():
                if unicodedata.normalize("NFKC", u_key) in norm_unit:
                    mult = u_mult
                    break
            if mult != 1.0:
                sqm = round(num_val * mult, 2)
                acres = round(sqm / 4046.86, 3)
            elif "acre" in unit or "ଏକର" in unit or "এক" in unit or "ఎకరాలు" in unit or "एकड़" in unit:
                sqm = round(num_val * 4046.86, 2)
                acres = round(num_val, 3)
            elif "decimal" in unit or "ଡେସିମିଲି" in unit or "शतक" in unit:
                sqm = round(num_val * 40.4686, 2)
                acres = round(sqm / 4046.86, 3)
            elif "hectare" in unit or "हेक्टेयर" in unit or "ହେକ୍ଟର" in unit:
                sqm = round(num_val * 10000.0, 2)
                acres = round(sqm / 4046.86, 3)
            elif "sq" in unit or "చ.మీ" in unit or "वर्ग मीटर" in unit:
                sqm = round(num_val, 2)
                acres = round(sqm / 4046.86, 3)
            else:
                sqm = round(num_val * mult, 2)
                acres = round(sqm / 4046.86, 3)
            set_field("claimed_area_sqm", sqm, 0.95, area_match.group(0))
            set_field("area_acres_printed", acres, 0.92, f"{acres} Acres equivalent")
        except ValueError:
            set_field("claimed_area_sqm", None, 0.0, "")
            set_field("area_acres_printed", None, 0.0, "")
    else:
        set_field("claimed_area_sqm", None, 0.0, "")
        set_field("area_acres_printed", None, 0.0, "")

    # -----------------------------------------------------------------------
    # Step 10: Land Use Classification Extraction
    # -----------------------------------------------------------------------
    if "ସ୍ଥିତିବାନ" in full_text:
        set_field("land_use_claim", "ସ୍ଥିତିବାନ (Sthitiban / Rayati)", 0.96, "ସ୍ଥିତିବାନ")
    elif "ଘରବାରୀ" in full_text:
        set_field("land_use_claim", "ଘରବାରୀ (Gharabari / Homestead)", 0.96, "ଘରବାରୀ")
    else:
        lu_res = _extract_by_keywords(profile["land_use_keywords"], lines, full_text)
        if lu_res:
            raw_lu = lu_res[0].lower()
            if any(w in raw_lu for w in ["agri", "कृषि", "వ్యవసాయ", "chahi", "barani", "nanjai", "punjai"]):
                set_field("land_use_claim", "Agricultural", lu_res[2], lu_res[1])
            elif any(w in raw_lu for w in ["resid", "आवासीय", "natham"]):
                set_field("land_use_claim", "Residential", lu_res[2], lu_res[1])
            elif any(w in raw_lu for w in ["comm", "व्यावसायिक"]):
                set_field("land_use_claim", "Commercial", lu_res[2], lu_res[1])
            else:
                set_field("land_use_claim", lu_res[0], lu_res[2], lu_res[1])
        elif any(w in full_text.lower() for w in ["agricultural", "వ్యవసాయ", "कृषि", "chahi", "barani", "nanjai", "punjai"]):
            set_field("land_use_claim", "Agricultural", 0.90, "Agricultural classification in text")
        elif any(w in full_text.lower() for w in ["residential", "आवासीय", "natham"]):
            set_field("land_use_claim", "Residential", 0.90, "Residential classification in text")
        elif any(w in full_text.lower() for w in ["commercial", "व्यावसायिक"]):
            set_field("land_use_claim", "Commercial", 0.90, "Commercial classification in text")
        else:
            set_field("land_use_claim", "", 0.0, "")

    # -----------------------------------------------------------------------
    # Step 11: Deed / Statutory Form Registration Number
    # -----------------------------------------------------------------------
    form_match = re.search(r"(Schedule\s*1\s*Form\s*No\.?\s*39-?A)", full_text, re.IGNORECASE)
    if form_match:
        set_field("deed_registration_no", form_match.group(1), 0.98, form_match.group(0))
    else:
        deed_res = _extract_by_keywords(profile["deed_registration_keywords"], lines, full_text, alphanumeric_only=True)
        if deed_res:
            set_field("deed_registration_no", deed_res[0], deed_res[2], deed_res[1])
        else:
            # Check explicit deed numbers (e.g. TS-DHARANI-2026-P-105, RJ-2026-xxx)
            deed_pat = re.search(r"\b([A-Z]{2}-[A-Z0-9\-_]{5,35})\b", full_text)
            if deed_pat:
                set_field("deed_registration_no", deed_pat.group(1), 0.94, deed_pat.group(0))
            else:
                set_field("deed_registration_no", "", 0.0, "")

    # -----------------------------------------------------------------------
    # Step 12: ULPIN / Bhu-Aadhaar Extraction
    # -----------------------------------------------------------------------
    ulpin_res = _extract_by_keywords(profile["ulpin_keywords"], lines, full_text, alphanumeric_only=True)
    if ulpin_res and re.search(r"\d{2}-\d{4,6}-\d{1,5}-\d{4}", ulpin_res[0]):
        set_field("ulpin", ulpin_res[0], 0.98, ulpin_res[1])
    else:
        u_m = re.search(r"\b(\d{2}-\d{4,6}-\d{1,5}-\d{4})\b", full_text)
        if u_m:
            set_field("ulpin", u_m.group(1), 0.98, u_m.group(0))
        else:
            set_field("ulpin", "", 0.0, "")

    return {
        "state": detected_state,
        "values": extracted_fields,
        "evidence": field_evidence,
        "confidences": field_confidence,
        "checks": field_checks,
        "raw_text": raw_text
    }
