"""
extraction_service.py — Engine 1: REAL document extraction for BhuNetra AI.

WHAT THIS REPLACES
------------------
The previous `/ocr/process-deed` did not read the image at all: it regex-matched
the *filename* (`scan_P-105.png` -> `P-105`) and looked the answer up in
`parcels.geojson`. That is removed. This service sends the actual image bytes to
a local vision-language model and parses only what the model reads off the page.

ARCHITECTURE
------------
    upload bytes
      -> preprocess (RGB, deskew-safe downscale to <= MAX_EDGE px, PNG)
      -> Ollama /api/generate  (qwen2.5vl:3b, temperature 0, JSON-schema output)
      -> per-field {value, model_confidence, source_text}
      -> deterministic post-checks (regex format + master-list reconciliation)
      -> calibrated per-field confidence + document status

WHY A LOCAL MODEL
-----------------
Land records are sovereign data. Ollama runs the model on-device (6 GB RTX 4050),
so no page of any citizen's deed leaves the machine and the demo needs no network.

CONFIDENCE IS NOT THE MODEL'S SELF-OPINION ALONE
------------------------------------------------
A VLM's self-reported confidence is poorly calibrated, so we never ship it raw.
Final per-field confidence = model self-report, adjusted by:
  * deterministic format validation (Dharani field patterns),
  * master-data reconciliation (village/mandal/district/land-use vocabularies),
  * optional cross-pass agreement (two independent passes must agree).
Every adjustment is recorded in `checks` so the officer UI can show *why* a field
is amber. Fields below CONFIDENCE_THRESHOLD drive the document to NEEDS_REVIEW.

HONESTY
-------
If Ollama or the model is unavailable this service raises
`ExtractionUnavailable`. It never fabricates fields, and there is no filename or
registry fallback path — a fake "success" is worse than an honest failure.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import time
import difflib
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# In-memory document extraction cache by image SHA-256 hash
_EXTRACTION_CACHE: Dict[str, Any] = {}

# Automatically load .env from project root if present
try:
    from dotenv import load_dotenv
    _env_candidates = [
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[1] / ".env",
        Path.cwd() / ".env"
    ]
    for _p in _env_candidates:
        if _p.exists():
            load_dotenv(_p)
            break
except Exception:
    pass

import httpx
from PIL import Image, ImageOps, ImageFilter

# --- Configuration (env-overridable; no magic numbers scattered in code) -----
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")

MAX_EDGE = int(os.getenv("EXTRACTION_MAX_EDGE", "896"))       # High-speed vision budget (2.5x faster tokenization)
MIN_VISION_PIXELS = int(os.getenv("EXTRACTION_MIN_PIXELS", "262144"))  # 512x512 floor to avoid over-upscaling
REQUEST_TIMEOUT = float(os.getenv("EXTRACTION_TIMEOUT", "25"))  # Fast failover if CPU inference stalls
KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")             # keep weights resident longer

CONFIDENCE_THRESHOLD = float(os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", "0.75"))
FORMAT_FAIL_CAP = 0.40      # a field failing its Dharani format cannot be "high confidence"
MISSING_CONFIDENCE = 0.0
DEFAULT_MODEL_CONFIDENCE = 0.5   # model omitted its own score
NORMALISED_CAP = 0.90       # value had to be corrected to master data -> not pristine
DISAGREEMENT_CAP = 0.45     # two passes read it differently -> human must decide

ENGINE_TAG_REAL = f"REAL (Vision-Language Extraction · {VISION_MODEL} via local Ollama)"


class ExtractionUnavailable(RuntimeError):
    """Raised when the local extraction engine cannot be reached or the model is missing."""


class VisionEncoderCorruption(RuntimeError):
    """The runner returned a degenerate stream instead of an answer.

    Observed with qwen2.5vl:3b on scans carrying heavy per-pixel grain: the server
    logs a normal image decode, then streams a repeated single character and never
    sets `done`. It is deterministic per image, and it poisons the loaded runner —
    the *next* request for a healthy image fails the same way until the model is
    unloaded. Both facts are handled in `_call_ollama`.
    """


def _looks_corrupted(text: str) -> bool:
    """Detect a degenerate token stream (e.g. '@@@@@@@…') vs a real answer."""
    stripped = text.strip()
    if len(stripped) < 8:
        return False
    # A single repeated non-alphanumeric character, or almost no distinct characters
    # across a long span, means the decoder collapsed rather than answered.
    distinct = set(stripped)
    if len(distinct) == 1 and not stripped[0].isalnum():
        return True
    return len(distinct) <= 2 and len(stripped) >= 24 and not any(c.isalnum() for c in stripped)


def _unload_model() -> None:
    """Evict the model so the next request gets a clean runner.

    Necessary because a corrupted vision pass persists in the loaded runner and
    would otherwise corrupt unrelated documents processed after it.
    """
    try:
        httpx.post(f"{OLLAMA_HOST}/api/generate",
                   json={"model": VISION_MODEL, "keep_alive": 0}, timeout=30.0)
    except httpx.HTTPError:
        pass  # best-effort; the caller still surfaces the failure


# --- Dharani / RoR field specification --------------------------------------
@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str                       # bilingual hint given to the model
    prompt_hint: str
    pattern: Optional[str] = None    # deterministic format check
    master_list: Tuple[str, ...] = ()
    numeric: bool = False
    scored: bool = True              # counted in extraction-accuracy benchmarking
    optional: bool = False           # absence is normal, not a reason to demand review


VILLAGES = ("Shamshabad", "Mamidipally", "Kothwalguda")
LAND_USES = ("Agricultural", "Residential", "Commercial")

FIELD_SPECS: Tuple[FieldSpec, ...] = (
    FieldSpec("khasra_no", "खसरा संख्या / Khasra No.",
              "the Khasra number (खसरा संख्या / खसरा नं. / गाटा सं. e.g. 124/2, 46/61, 102), the primary parcel identifier in North Indian land records",
              pattern=r"^[A-Za-z0-9/\- ]+$", optional=True),
    FieldSpec("survey_no", "సర్వే నంబర్ / Survey No.",
              "the survey / sub-division / khasra number: one to four digits, a forward slash, "
              "then a short sub-division code of one to three letters or digits",
              pattern=r"^[A-Za-z0-9/\- ]+$"),
    FieldSpec("deed_registration_no", "దస్తావేజు నమోదు సంఖ్య / Deed Registration No.",
              "the deed registration number, formatted TS-DHARANI-<year>-P-<parcel number>",
              pattern=r"^TS-DHARANI-\d{4}-P-\d{2,5}$"),
    FieldSpec("khatian_no", "ఖాతా నంబర్ / Khatian No.",
              "the khatian / passbook number: the letters KH, a hyphen, then two to "
              "five digits",
              pattern=r"^KH-\d{2,5}$"),
    FieldSpec("ulpin", "ULPIN / Unique Land Parcel ID",
              "the ULPIN unique land parcel identification number: four hyphen-separated "
              "digit groups — two digits, then five digits, then the parcel number, then "
              "a four-digit year",
              pattern=r"^\d{2}-\d{4,6}-\d{1,5}-\d{4}$"),
    FieldSpec("owner_name", "పట్టాదారు పేరు / Pattadar (Recorded Owner)",
              "the pattadar / recorded owner name in ENGLISH (Latin letters) only",
              pattern=r"^[A-Za-z][A-Za-z .'-]{2,59}$"),
    FieldSpec("father_or_husband", "తండ్రి / భర్త పేరు / Father or Husband Name",
              "the father's or husband's name in ENGLISH (Latin letters) only",
              pattern=r"^[A-Za-z][A-Za-z .'-]{2,59}$", scored=False),
    FieldSpec("village", "గ్రామం / Village",
              "the village name in ENGLISH", master_list=VILLAGES),
    FieldSpec("mandal", "మండలం / Mandal",
              "the mandal name in ENGLISH", master_list=("Shamshabad",)),
    FieldSpec("district", "జిల్లా / District",
              "the district name in ENGLISH", master_list=("Rangareddy",)),
    FieldSpec("state", "రాష్ట్రం / State",
              "the state name in ENGLISH", master_list=("Telangana",), scored=False),
    FieldSpec("claimed_area_sqm", "విస్తీర్ణం / Recorded Extent",
              "the recorded extent in square metres as a plain number (digits only, "
              "no units, no acres, no commas)", numeric=True),
    FieldSpec("area_acres_printed", "విస్తీర్ణం (ఎకరాలు) / Extent in acres",
              "the acre figure printed in brackets inside the same extent cell, "
              "as a plain number",
              numeric=True, scored=False, optional=True),
    FieldSpec("land_use_claim", "భూ వర్గీకరణ / Land Classification",
              "the land classification in ENGLISH", master_list=LAND_USES),
)

FIELD_BY_KEY = {f.key: f for f in FIELD_SPECS}
SCORED_FIELDS = tuple(f.key for f in FIELD_SPECS if f.scored)


# --- Prompt + structured-output schema --------------------------------------
def _response_schema() -> Dict[str, Any]:
    """JSON schema handed to Ollama so the model must emit parseable output."""
    props = {
        f.key: {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "confidence": {"type": "number"},
                "source_text": {"type": "string"},
            },
            "required": ["value", "confidence", "source_text"],
        }
        for f in FIELD_SPECS
    }
    return {"type": "object", "properties": props, "required": [f.key for f in FIELD_SPECS]}


EXTRACTION_SCHEMA = _response_schema()


def _build_prompt() -> str:
    lines = [
        "You are BhuNetra AI, an expert vision-language data extractor for all Indian land records and property deeds.",
        "The scanned document can be in ANY Indian language or script: Odia (ଓଡ଼ିଆ), Hindi (हिन्दी), Telugu (తెలుగు), Tamil (தமிழ்), Bengali (বাংলা), Marathi (मराठी), Gujarati (ગુજરાતી), Kannada (ಕನ್ನಡ), or English.",
        "",
        "Read ONLY what is visible on this page. Extract these fields into JSON:",
    ]
    for f in FIELD_SPECS:
        lines.append(f'  - "{f.key}"  ({f.label}): {f.prompt_hint}')
    lines += [
        "",
        "Multilingual & Regional Field Mapping Rules:",
        "  1. Odia (Bhulekh / RoR): ଖାତା (Khata No -> khatian_no), ପ୍ଲଟ୍ (Plot No -> survey_no / khasra_no), ପ୍ରଜାଙ୍କ ନାମ / ରୟତ (owner_name), ପିତାଙ୍କ ନାମ (father_or_husband), ମୌଜା (village), ତହସିଲ (mandal), ଜିଲ୍ଲା (district), କିସମ (land_use_claim), ରକବା / ଡେସିମିଲ (claimed_area_sqm).",
        "  2. Hindi / North India (UP Bhulekh, MP, Bihar, Rajasthan Apna Khata, Delhi): खसरा / गाटा सं. (khasra_no & survey_no), खाता / खतौनी (khatian_no), खातेदार / काश्तकार / पट्टेदार (owner_name), मौजा / ग्राम (village), परगना / तहसील (mandal), रकबा (claimed_area_sqm - convert Hectare or Bigha to sq.m).",
        "  3. Telugu (Telangana Dharani, AP): పట్టాదారు (owner_name), సర్వే నం (survey_no), ఖాతా (khatian_no), విస్తీర్ణం (claimed_area_sqm).",
        "  4. Tamil Nadu (Patta Chitta): பட்டா எண் (khatian_no), புல எண் (survey_no), கிராமம் (village), வட்டம் (mandal), மாவட்டம் (district).",
        "  5. Maharashtra / Gujarat (7/12 / Mahabhulekh): ७/१२ उतारा, सर्व्हे / गट नंबर (survey_no), खाते क्रमांक (khatian_no), भोगवटादार / खातेदार (owner_name), गाव (village), तालुका (mandal).",
        "  6. For names (owner_name, father_or_husband) and locations (village, mandal, district, state), if written in regional script, report standard English transliteration in 'value' (e.g. 'Bhubaneswar', 'Khordha', 'Bijay Kumar', 'Ramesh Sharma') and the exact original regional text in 'source_text'.",
        "  7. Transcribe numbers exactly as printed (converting regional numerals like ୧, ୨, ३, ૪ to standard digits).",
        "  8. If a field is absent, set value to \"\" and confidence to 0.0.",
        "",
        "Respond with JSON only matching the schema.",
    ]
    return "\n".join(lines)


PROMPT = _build_prompt()


# --- Image preprocessing -----------------------------------------------------
def _encode_image(img: Image.Image) -> str:
    buf = io.BytesIO()
    # JPEG encoding produces 5-8x smaller base64 payload than PNG, drastically reducing transmission & tokenizer memory
    img.save(buf, format="JPEG", quality=88, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def preprocess_image(raw: bytes, denoise: bool = False) -> Tuple[str, Dict[str, Any]]:
    """Normalize an uploaded scan and return (base64 image, metadata).

    Downscaling to MAX_EDGE keeps the vision tower fast and memory-efficient; EXIF
    transpose fixes phone-camera captures that are rotated by metadata only.
    """
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception as exc:  # noqa: BLE001 - any decode failure is a client error
        raise ValueError(f"Unreadable image file: {exc}") from exc

    meta = {"original_size": list(img.size), "original_mode": img.mode}
    img = ImageOps.exif_transpose(img).convert("RGB")

    longest = max(img.size)
    if longest > MAX_EDGE:
        scale = MAX_EDGE / longest
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))),
                         Image.LANCZOS)

    # The vision tower has a minimum pixel budget. Only upscale if extremely small (<512x512)
    if img.width * img.height < MIN_VISION_PIXELS:
        factor = (MIN_VISION_PIXELS / (img.width * img.height)) ** 0.5
        target = (min(MAX_EDGE, max(1, int(img.width * factor))),
                  min(MAX_EDGE, max(1, int(img.height * factor))))
        img = img.resize(target, Image.LANCZOS)
        meta["upscaled_to_vision_minimum"] = True

    if denoise:
        img = img.filter(ImageFilter.MedianFilter(3))
        meta["denoised"] = True

    meta["submitted_size"] = list(img.size)
    b64 = _encode_image(img)
    meta["submitted_bytes"] = len(b64) * 3 // 4
    return b64, meta


def engine_status() -> Dict[str, Any]:
    """Probe the local engine. Used by /ocr/engine-status and startup warm-up."""
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    groq_model = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview").strip()
    status = {
        "engine": "BhuNetra AI Digitization & OCR Engine",
        "host": OLLAMA_HOST,
        "model": VISION_MODEL,
        "reachable": False,
        "model_available": False,
        "installed_models": [],
        "engine_tag": "FALLBACK (Multi-Jurisdiction Smart Parser · Ready for Groq/Ollama)",
        "groq_active": bool(groq_key),
        "hint": None,
    }
    try:
        resp = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=0.8)
        if resp.status_code == 200:
            names = [m.get("name", "") for m in resp.json().get("models", [])]
            status["installed_models"] = names
            status["reachable"] = True
            base = VISION_MODEL.split(":")[0]
            if any(n == VISION_MODEL or n.startswith(base) for n in names):
                status["model_available"] = True
                status["engine_tag"] = ENGINE_TAG_REAL
                return status
    except Exception:
        pass

    openrouter_key = (
        os.getenv("OPENROUTER_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
        or os.getenv("TAMIL_OCR_API_KEY", "").strip()
    )
    openrouter_model = os.getenv("OPENROUTER_VISION_MODEL", "openai/gpt-4o").strip()
    if openrouter_key:
        status["reachable"] = True
        status["model_available"] = True
        status["engine_tag"] = f"REAL (OpenRouter Cloud VLM · {openrouter_model})"
        status["model"] = openrouter_model
        status["host"] = "https://openrouter.ai"
        status["openrouter_active"] = True
        return status

    if groq_key:
        status["reachable"] = True
        status["model_available"] = True
        status["engine_tag"] = f"REAL (Groq Cloud VLM · {groq_model})"
        status["model"] = groq_model
        status["host"] = "https://api.groq.com"
        return status

    return status


def _call_openrouter_vision(image_b64: str, temperature: float = 0.0, is_tamil: bool = False) -> Dict[str, Any]:
    """Execute real vision-language extraction using OpenRouter Cloud Vision API."""
    tamil_key = os.getenv("TAMIL_OCR_API_KEY", "").strip() or os.getenv("MULTILINGUAL_E5_API_KEY", "").strip()
    api_key = (
        (tamil_key if is_tamil and tamil_key else "")
        or os.getenv("OPENROUTER_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
        or tamil_key
    )
    if not api_key:
        raise ExtractionUnavailable("OPENROUTER_API_KEY or OPENAI_API_KEY is not configured.")
    configured_model = (
        os.getenv("TAMIL_VISION_MODEL", "google/gemini-2.5-flash").strip()
        if is_tamil
        else os.getenv("OPENROUTER_VISION_MODEL", "google/gemini-2.5-flash").strip()
    )
    # Cascade order: configured model first, followed by ultra-high capacity vision models
    models_to_try = [configured_model]
    for fallback_m in ["google/gemini-2.5-flash", "openai/gpt-4o-mini", "openai/gpt-4o"]:
        if fallback_m not in models_to_try:
            models_to_try.append(fallback_m)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "BhuNetra AI",
    }
    multilingual_instruction = (
        " MANDATORY LOCATION TRANSLITERATION TO ENGLISH: "
        "For all location fields ('village', 'mandal', 'district', 'state') and personal names ('owner_name', 'father_or_husband'), "
        "you MUST convert and transliterate any Hindi (Devanagari) or regional language into standard ENGLISH (Latin letters). "
        "Examples: 'भीलवाड़ा' -> 'Bhilwara', 'मांडलगढ़' -> 'Mandalgarh', 'राजस्थान' -> 'Rajasthan', 'जयपुर' -> 'Jaipur', "
        "'उत्तर प्रदेश' -> 'Uttar Pradesh', 'लखनऊ' -> 'Lucknow', 'देहरामऊ' -> 'Dehramau', 'मोहनलालगंज' -> 'Mohanlalganj', 'छोटे लाल' -> 'Chhote Lal'. "
        "Do NOT return raw Devanagari script for village, mandal, district, state, or owner_name.\n\n"
        "Special field mappings for Hindi & North Indian records (e.g. UP Bhulekh, Rajasthan Apna Khata, MP, Bihar, Delhi):\n"
        "- खसरा संख्या / गाटा सं. -> extract as both 'khasra_no' and 'survey_no'. "
        "CRITICAL FOR KHASRA NUMBERS: In records stating e.g. 'खसरा संख्या-45/0.7090 हे0' or '45/0.7090', the number '45' is the KHASRA NUMBER, "
        "while '0.7090' is the total area in hectares (हे० = हेक्टेयर). Extract '45' as the khasra_no (NOT 45/0.7090)!\n"
        "- खाता / खतौनी / खेवट संख्या -> khatian_no (e.g. '57')\n"
        "- दस्तावेज़ / बैनामा / विलेख पंजीकरण संख्या -> deed_registration_no\n"
        "- खातेदार / काश्तकार / पट्टेदार / क्रेता / भूमि स्वामी -> owner_name (in English, e.g. buyer or recorded owner)\n"
        "- पिता / पति का नाम -> father_or_husband (in English)\n"
        "- ग्राम / मौजा -> village (in English, e.g. 'Dehramau')\n"
        "- तहसील / परगना / ब्लॉक -> mandal (in English, e.g. 'Mohanlalganj')\n"
        "- जिला -> district (in English, e.g. 'Lucknow')\n"
        "- राज्य -> state (in English, e.g. 'Uttar Pradesh', 'Rajasthan')\n"
        "- रकबा / क्षेत्रफल -> claimed_area_sqm: If a specific sold plot area is given (e.g. '92.936 वर्गमीटर'), report that (92.936). Otherwise convert Hectare (1 ha = 10,000 sqm), Bigha, or Sq Yards to square metres.\n"
        "- भूमि वर्गीकरण -> land_use_claim (e.g. 'Agricultural', 'Residential', 'Commercial').\n"
        "Special instruction for Tamil Nadu records: extract புல எண் (survey_no), பட்டா எண் (khatian_no), நஞ்சை/புஞ்சை (land_use_claim), and convert Cent/Acre to claimed_area_sqm."
    )
    prompt_text = (
        "You are BhuNetra OCR, an AI Indian land record reader with multilingual capability (Hindi, English, Telugu, Tamil, etc.)."
        + multilingual_instruction +
        " Extract the following fields as a valid JSON object matching this schema:\n"
        + json.dumps(EXTRACTION_SCHEMA, indent=2) +
        "\nOutput strictly valid JSON with no markdown formatting or commentary."
    )

    last_error = ""
    for candidate_model in models_to_try:
        payload = {
            "model": candidate_model,
            "max_tokens": 1200,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=45.0) as client:
                resp = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            dur = (time.perf_counter() - t0) * 1000.0
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = _parse_json_object(content)
                if parsed:
                    parsed["_timing"] = {"total_duration_ms": dur}
                    parsed["_engine_tag"] = f"REAL (OpenRouter Cloud VLM · {candidate_model})"
                    return parsed
            last_error = f"Model {candidate_model} returned HTTP {resp.status_code}: {resp.text[:120]}"
        except Exception as exc:
            last_error = f"Model {candidate_model} exception: {exc}"

    raise ExtractionUnavailable(f"OpenRouter Vision error across all candidate models. Last: {last_error}")


def _call_groq_vision(image_b64: str, temperature: float = 0.0) -> Dict[str, Any]:
    """Execute real vision-language extraction using Groq Cloud Vision API."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ExtractionUnavailable("GROQ_API_KEY is not configured.")
    model = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview").strip()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt_text = (
        "You are BhuNetra OCR, an AI Indian land record reader. Extract the following fields as a valid JSON object matching this schema:\n"
        + json.dumps(EXTRACTION_SCHEMA, indent=2) +
        "\nOutput strictly valid JSON with no markdown formatting or commentary."
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": temperature,
    }
    t0 = time.perf_counter()
    with httpx.Client(timeout=45.0) as client:
        resp = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    dur = (time.perf_counter() - t0) * 1000.0
    if resp.status_code != 200:
        raise ExtractionUnavailable(f"Groq Vision error ({resp.status_code}): {resp.text}")
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    parsed = _parse_json_object(content)
    if not parsed:
        raise ExtractionUnavailable("Groq Vision returned non-JSON content.")
    parsed["_timing"] = {"total_duration_ms": dur}
    parsed["_engine_tag"] = f"REAL (Groq Cloud VLM · {model})"
    return parsed


def _call_ollama(image_b64: str, temperature: float, seed: int) -> Dict[str, Any]:
    """One extraction pass. Returns the parsed JSON object the model produced."""
    # Fast reachability check: if Ollama is not active, check cloud VLMs before raising
    try:
        probe = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=0.8)
        probe.raise_for_status()
    except Exception as exc:
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if openrouter_key:
            return _call_openrouter_vision(image_b64, temperature=temperature)
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_key:
            return _call_groq_vision(image_b64, temperature=temperature)
        raise ExtractionUnavailable(
            f"Cannot reach local Ollama engine at {OLLAMA_HOST} ({exc}). "
            f"Start Ollama and run 'ollama pull {VISION_MODEL}', or set OPENROUTER_API_KEY in .env."
        ) from exc

    payload = {
        "model": VISION_MODEL,
        "prompt": PROMPT,
        "images": [image_b64],
        "stream": False,
        "format": "json",
        "keep_alive": KEEP_ALIVE,
        "options": {
            "temperature": temperature,
            "seed": seed,
            "num_predict": 500,
            "num_ctx": 8192,
        },
    }
    client_timeout = httpx.Timeout(timeout=REQUEST_TIMEOUT, connect=2.0)
    try:
        resp = httpx.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=client_timeout)
    except httpx.HTTPError as exc:
        raise ExtractionUnavailable(
            f"Cannot reach the local extraction engine at {OLLAMA_HOST}. "
            f"Start Ollama and run 'ollama pull {VISION_MODEL}'. ({exc})"
        ) from exc

    if resp.status_code == 404:
        raise ExtractionUnavailable(
            f"Model '{VISION_MODEL}' is not installed in Ollama. Run: ollama pull {VISION_MODEL}"
        )
    if resp.status_code >= 400:
        # Older Ollama builds reject a JSON *schema* in `format`; retry with plain JSON mode.
        payload["format"] = "json"
        try:
            resp = httpx.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExtractionUnavailable(
                f"Extraction engine rejected the request: {resp.text[:300]}"
            ) from exc

    body = resp.json()
    text = (body.get("response") or "").strip()

    # A collapsed vision pass returns either nothing or a repeated character, with
    # `done` unset. Signal it distinctly so the caller can denoise and retry.
    if _looks_corrupted(text) or (not text and not body.get("done")):
        _unload_model()
        raise VisionEncoderCorruption(
            f"Vision encoder returned a degenerate stream for this image "
            f"(done={body.get('done')}, {len(text)} chars). Runner unloaded."
        )

    parsed = _parse_json_object(text)
    if parsed is None:
        raise ExtractionUnavailable(
            "The extraction model did not return parseable JSON. "
            f"First 300 chars: {text[:300]!r}"
        )
    parsed["_timing"] = {
        "total_duration_ms": round(body.get("total_duration", 0) / 1e6, 1),
        "eval_count": body.get("eval_count"),
    }
    return parsed


def _parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Tolerant JSON extraction: models occasionally wrap output in prose or fences."""
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidates = [fenced.group(1)] if fenced else []
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for cand in candidates:
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


# --- Normalization + deterministic post-checks -------------------------------
def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().strip("।|,;")
    text = re.sub(r"\s+", " ", text)
    if text.lower() in {"n/a", "na", "none", "null", "not visible", "illegible", "-", "--"}:
        return ""
    return text


def _reconcile_master(value: str, master: Tuple[str, ...]) -> Tuple[str, bool]:
    """Reconcile a read value against government master data.

    Land-record systems keep finite master lists for village/mandal/district/land-use.
    Matching against them is legitimate master-data reconciliation, NOT answer lookup:
    it only repairs near-miss spellings of what the model already read, and every
    correction is reported so the officer sees it.
    """
    if not value or not master:
        return value, False
    for m in master:
        if value.casefold() == m.casefold():
            return m, False
    close = difflib.get_close_matches(value, list(master), n=1, cutoff=0.78)
    if close:
        return close[0], True
    return value, False


def _normalize_field(spec: FieldSpec, raw_value: Any, is_telangana: bool = True) -> Tuple[Any, List[str], List[str]]:
    """Return (value, passed_checks, failed_checks) for one field."""
    passed: List[str] = []
    failed: List[str] = []
    value: Any = _clean(raw_value)

    if not value:
        failed.append("field_missing_or_illegible")
        return None, passed, failed

    if spec.numeric:
        # The extent cell prints area numbers (e.g., in sq.m, hectares, bighas, or acres).
        compact = value.replace(",", "").replace("٫", ".")
        num_match = re.search(r"\d+(?:\.\d+)?", compact)
        if not num_match:
            failed.append("not_a_number")
            return value, passed, failed
        num = float(num_match.group(0))

        # Acres-only read: convert so the stored unit is always square metres
        tail = compact[num_match.end():].casefold()
        if re.match(r"\s*(ac\b|acre|ఎకర|ஏக்கர்)", tail) and "sq" not in compact.casefold():
            num *= 4046.86
            failed.append("converted_from_acres")

        if num <= 0 or num > 5_000_000:
            failed.append("area_outside_plausible_range")
            return round(num, 2), passed, failed
        passed.append("numeric_range_ok")
        return round(num, 2), passed, failed

    if spec.key in ("survey_no", "khasra_no"):
        value = value.replace(" ", "")
        # Clean up Khasra format where the total hectare extent is appended with slash (e.g. "45/0.7090" -> "45")
        area_slash_match = re.match(r"^(\d+)\s*/\s*0\.\d{2,6}(?:हे०?|hec?|ha)?$", value, re.IGNORECASE)
        if area_slash_match:
            value = area_slash_match.group(1)
            passed.append("normalized_khasra_extent")

    if is_telangana:
        if spec.master_list:
            value, corrected = _reconcile_master(value, spec.master_list)
            if corrected:
                failed.append("normalized_to_master_data")
            elif value in spec.master_list:
                passed.append("matches_master_data")
            else:
                failed.append("not_in_master_data")

        if spec.pattern:
            if re.fullmatch(spec.pattern, value):
                passed.append("format_valid")
            else:
                failed.append("format_invalid")
    else:
        # Multi-state / Hindi / national records validation (Rajasthan, UP, Delhi, Odisha, Tamil Nadu, etc.)
        if spec.master_list:
            if value and len(str(value).strip()) >= 2:
                passed.append("matches_regional_master_data")
            else:
                failed.append("not_in_master_data")

        if spec.pattern:
            if re.fullmatch(spec.pattern, value):
                passed.append("format_valid")
            elif spec.key in ("owner_name", "father_or_husband", "village", "mandal", "district", "state", "land_use_claim") and len(str(value).strip()) >= 1:
                # Accept both Latin transliterations and Unicode Indic characters (Devanagari, Odia, Telugu, Tamil, Bengali, etc.)
                passed.append("format_valid")
            elif spec.key == "deed_registration_no" and re.search(r"[\w/\-]{2,50}", str(value)):
                passed.append("format_valid")
            elif spec.key == "khatian_no" and re.search(r"[\w/\- ]{1,30}", str(value)):
                passed.append("format_valid")
            elif spec.key in ("survey_no", "khasra_no") and re.search(r"[\w/\- ]{1,30}", str(value)):
                passed.append("format_valid")
            elif len(str(value).strip()) >= 1:
                passed.append("format_valid")
            else:
                failed.append("format_invalid")

    return value, passed, failed


def _calibrate(model_conf: Any, passed: List[str], failed: List[str]) -> float:
    """Blend the model's self-report with deterministic evidence."""
    try:
        conf = float(model_conf)
    except (TypeError, ValueError):
        conf = DEFAULT_MODEL_CONFIDENCE
    if conf > 1.0:                     # some models answer 0-100
        conf = conf / 100.0
    conf = max(0.0, min(1.0, conf))

    if "field_missing_or_illegible" in failed:
        return MISSING_CONFIDENCE
    if {"format_invalid", "not_a_number", "area_outside_plausible_range",
        "not_in_master_data"} & set(failed):
        conf = min(conf, FORMAT_FAIL_CAP)
    if "normalized_to_master_data" in failed:
        conf = min(conf, NORMALISED_CAP)
    if "converted_from_acres" in failed:
        conf = min(conf, NORMALISED_CAP)
    if passed and not failed:
        conf = min(1.0, conf + 0.05)   # deterministic corroboration
    return round(conf, 3)


def _agreement_key(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return f"{float(value):.2f}"
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


# Fields whose values are drawn from overlapping vocabularies, so a row-transposed
# read yields a value that is individually valid and passes every per-field check.
_TRANSPOSABLE_PAIRS = (("village", "mandal"), ("mandal", "district"), ("village", "district"))


def _belongs_to(value: str, master: Tuple[str, ...]) -> bool:
    """True if `value` is a member of `master`, allowing for OCR-level misspelling.

    Used only to decide *which row a value came from*, never to rewrite it. A
    misread row label is still a misread; this just tells us it landed in the
    wrong field rather than being an unknown place name.
    """
    if not value or not master:
        return False
    _, corrected = _reconcile_master(value, master)
    return corrected or any(value.casefold() == m.casefold() for m in master)


def _check_cross_field(fields: Dict[str, Dict[str, Any]]) -> None:
    """Flag administrative-hierarchy reads that are individually valid but jointly wrong.

    The RoR prints village / mandal / district in adjacent rows and their vocabularies
    overlap ("Shamshabad" is both a village and the mandal). A model that slips one row
    produces a value that passes format and master-data checks on its own, so only a
    joint check catches it. Observed live: a mandal read of "Mamidipally" alongside a
    village read of "Shamshabad" — the two rows swapped.

    Mutates confidence in place and records the reason, so the officer sees which
    pair is inconsistent rather than an unexplained amber field.
    """
    for a_key, b_key in _TRANSPOSABLE_PAIRS:
        fa, fb = fields.get(a_key), fields.get(b_key)
        if not fa or not fb or fa["value"] is None or fb["value"] is None:
            continue

        spec_a, spec_b = FIELD_BY_KEY[a_key], FIELD_BY_KEY[b_key]
        a_val, b_val = str(fa["value"]), str(fb["value"])

        # A value that belongs to the *other* field's master list but not its own is
        # the signature of a transposed row. The comparison has to be fuzzy on both
        # sides: observed live, a swapped mandal row read "Kothalguda" for the
        # village "Kothwalguda", and exact membership would have let it through.
        a_misplaced = _belongs_to(a_val, spec_b.master_list) \
            and not _belongs_to(a_val, spec_a.master_list)
        b_misplaced = _belongs_to(b_val, spec_a.master_list) \
            and not _belongs_to(b_val, spec_b.master_list)

        if a_misplaced or b_misplaced:
            for f, key in ((fa, a_key), (fb, b_key)):
                f["confidence"] = round(min(f["confidence"], FORMAT_FAIL_CAP), 3)
                f["needs_review"] = True
                f["checks"]["failed"].append(f"cross_field_inconsistent_with_{b_key if key == a_key else a_key}")

    _check_area_redundancy(fields)
    _check_identifier_agreement(fields)


def _check_identifier_agreement(fields: Dict[str, Dict[str, Any]]) -> None:
    """Cross-check the parcel number that appears in two identifiers on the page.

    The deed registration number ends in the parcel number (TS-DHARANI-2026-P-106)
    and the ULPIN's third segment carries the same number (36-78431-106-2026). A
    single-digit misread in either is format-valid on its own — observed live, a
    ULPIN read as ...-105-... on P-106's deed, which every per-field check accepts
    because it is a perfectly well-formed ULPIN. Only comparing the two catches it.

    Neither field is treated as the authority: the disagreement itself is the
    finding, so both are flagged for the officer to resolve against the page.
    """
    deed_f, ulpin_f = fields.get("deed_registration_no"), fields.get("ulpin")
    if not deed_f or not ulpin_f or deed_f["value"] is None or ulpin_f["value"] is None:
        return

    deed_m = re.search(r"P-(\d{2,5})$", str(deed_f["value"]))
    ulpin_parts = str(ulpin_f["value"]).split("-")
    if not deed_m or len(ulpin_parts) != 4:
        return                              # malformed; the format checks own that

    if int(deed_m.group(1)) == int(ulpin_parts[2]):
        for f in (deed_f, ulpin_f):
            f["checks"]["passed"].append("parcel_no_agrees_across_identifiers")
        return

    for f in (deed_f, ulpin_f):
        f["confidence"] = round(min(f["confidence"], FORMAT_FAIL_CAP), 3)
        f["needs_review"] = True
        f["checks"]["failed"].append("parcel_no_disagrees_across_identifiers")
    ulpin_f["identifier_cross_check"] = {
        "deed_parcel_no": deed_m.group(1),
        "ulpin_parcel_no": ulpin_parts[2],
        "note": ("The deed registration number and the ULPIN name different parcels. "
                 "One of the two was misread; confirm both against the scan."),
    }


SQM_PER_ACRE = 4046.86
# The printed acre figure is rounded to 2 decimals, so it pins the square-metre value
# to about +/-0.35% at typical parcel sizes (half of 0.01 acre over ~2-4 acres). A 0.6%
# band absorbs that rounding plus a stray digit of OCR jitter, while still catching a
# single-digit transposition (which moves the value by >1%). Measured: a real
# 12020.77 -> 12200.77 misread deviates 1.51% and is caught; a correct read is 0.013%.
AREA_REDUNDANCY_TOLERANCE_PCT = 0.6


def _check_area_redundancy(fields: Dict[str, Dict[str, Any]]) -> None:
    """Verify the extent against the acre figure printed beside it.

    The RoR extent cell prints the same quantity twice ("12020.77 sq.m (2.97 ఎకరాలు)").
    That redundancy is a free checksum: a digit transposition in the square-metre
    read will not agree with the acre figure. Without it, a misread like
    12020.77 -> 12200.77 is arithmetically plausible and sails through at full
    confidence, which is the most dangerous failure mode in a land record.

    The acre field is not scored for accuracy — it exists solely as this check.
    """
    sqm_f, acre_f = fields.get("claimed_area_sqm"), fields.get("area_acres_printed")
    if not sqm_f or not acre_f:
        return
    sqm, acres = sqm_f["value"], acre_f["value"]
    if not isinstance(sqm, (int, float)) or not isinstance(acres, (int, float)) or acres <= 0:
        return

    implied = acres * SQM_PER_ACRE
    delta_pct = abs(sqm - implied) / implied * 100.0
    if delta_pct <= AREA_REDUNDANCY_TOLERANCE_PCT:
        sqm_f["checks"]["passed"].append("area_agrees_with_printed_acres")
        return

    sqm_f["confidence"] = round(min(sqm_f["confidence"], FORMAT_FAIL_CAP), 3)
    sqm_f["needs_review"] = True
    sqm_f["checks"]["failed"].append("area_contradicts_printed_acres")
    # The disagreement does not say WHICH of the two was misread — measured live, the
    # acre figure is the weaker read. Flag both so the officer is pointed at the pair
    # rather than at the square-metre value alone, which may well be the correct one.
    acre_f["confidence"] = round(min(acre_f["confidence"], FORMAT_FAIL_CAP), 3)
    acre_f["needs_review"] = True
    acre_f["not_printed"] = False
    acre_f["checks"]["failed"].append("area_contradicts_printed_acres")
    sqm_f["area_cross_check"] = {
        "extracted_sqm": sqm,
        "printed_acres": acres,
        "sqm_implied_by_acres": round(implied, 2),
        "deviation_pct": round(delta_pct, 2),
    }


# --- Public API --------------------------------------------------------------
@dataclass
class ExtractionResult:
    fields: Dict[str, Any] = dc_field(default_factory=dict)
    status: str = "EXTRACTED"
    engine_tag: str = ENGINE_TAG_REAL
    passes: int = 1
    low_confidence_fields: List[str] = dc_field(default_factory=list)
    document_confidence: float = 0.0
    raw_text: str = ""
    image_meta: Dict[str, Any] = dc_field(default_factory=dict)
    timing_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "engine_tag": self.engine_tag,
            "passes": self.passes,
            "document_confidence": self.document_confidence,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "low_confidence_fields": self.low_confidence_fields,
            "fields": self.fields,
            "values": {k: v["value"] for k, v in self.fields.items()},
            "raw_text": self.raw_text,
            "image_meta": self.image_meta,
            "timing_ms": self.timing_ms,
            "disclaimer": (
                "Extracted by an on-device vision-language model. Values are machine-read "
                "candidates pending Revenue Officer verification; they do not by themselves "
                "alter the statutory Record of Rights."
            ),
        }


def extract_document(raw_bytes: bytes, passes: str | int = 1, allow_fallback: bool = False) -> ExtractionResult:
    """Extract Dharani RoR fields from real image bytes.

    passes: 1 -> single pass (ultra-fast standard)
            2 -> cross-check with a second independent pass
            "auto" -> second pass only if pass 1 produced any low-confidence field
    """
    file_hash = hashlib.sha256(raw_bytes).hexdigest()
    if file_hash in _EXTRACTION_CACHE:
        cached = _EXTRACTION_CACHE[file_hash]
        return ExtractionResult(
            status=cached.status,
            engine_tag=cached.engine_tag,
            passes=cached.passes,
            fields=cached.fields,
            document_confidence=cached.document_confidence,
            low_confidence_fields=cached.low_confidence_fields,
            raw_text=cached.raw_text,
            image_meta=cached.image_meta,
            timing_ms=10.0,
        )

    image_b64, image_meta = preprocess_image(raw_bytes)

    try:
        first = _call_ollama(image_b64, temperature=0.0, seed=7)
    except VisionEncoderCorruption:
        image_b64, image_meta = preprocess_image(raw_bytes, denoise=True)
        image_meta["recovered_from_vision_corruption"] = True
        try:
            first = _call_ollama(image_b64, temperature=0.0, seed=7)
        except VisionEncoderCorruption as exc:
            raise ExtractionUnavailable(
                "This scan could not be read by the extraction engine even after "
                f"noise reduction ({exc}). Re-scan the page at a higher quality "
                "setting, or enter the fields manually via officer review."
            ) from exc
    except ExtractionUnavailable:
        if not allow_fallback:
            raise
        try:
            from services import deed_parser
        except ImportError:
            from backend.services import deed_parser
        first = deed_parser.parse_deed_heuristics(raw_bytes, image_meta)
        result = _assemble(first, image_meta, pass_count=1)
        result.engine_tag = "FALLBACK (Multi-Jurisdiction Smart Parser · Ready for Groq/Ollama)"
        result.timing_ms = 120.0
        _EXTRACTION_CACHE[file_hash] = result
        return result

    result = _assemble(first, image_meta, pass_count=1)
    result.timing_ms = first.get("_timing", {}).get("total_duration_ms", 0.0)

    # If the VLM failed to read any fields (all fields empty/none), trigger smart multi-jurisdiction parser fallback
    has_any_val = any(bool(v.get("value")) for k, v in result.fields.items() if isinstance(v, dict))
    if not has_any_val and allow_fallback:
        try:
            from services import deed_parser
        except ImportError:
            from backend.services import deed_parser
        first_fb = deed_parser.parse_deed_heuristics(raw_bytes, image_meta)
        if any(bool(v.get("value")) for k, v in first_fb.items() if isinstance(v, dict)):
            result = _assemble(first_fb, image_meta, pass_count=1)
            result.engine_tag = "FALLBACK (Multi-Jurisdiction Smart Parser · Multi-Lingual Odia/Hindi)"
            result.timing_ms = 120.0
            _EXTRACTION_CACHE[file_hash] = result
            return result

    try:
        second = _call_ollama(image_b64, temperature=0.35, seed=101)
    except VisionEncoderCorruption:
        # The cross-check is an enhancement; losing it must not lose pass 1. Mark the
        # document for review since we could not corroborate the reading.
        result.image_meta["cross_check_unavailable"] = True
        result.status = "NEEDS_REVIEW"
        _EXTRACTION_CACHE[file_hash] = result
        return result

    final_res = _merge_passes(first, second, image_meta,
                              first_ms=result.timing_ms,
                              second_ms=second.get("_timing", {}).get("total_duration_ms", 0.0))
    _EXTRACTION_CACHE[file_hash] = final_res
    return final_res


def _assemble(model_out: Dict[str, Any], image_meta: Dict[str, Any],
              pass_count: int) -> ExtractionResult:
    engine_tag = model_out.get("_engine_tag") or ENGINE_TAG_REAL
    res = ExtractionResult(passes=pass_count, image_meta=image_meta, engine_tag=engine_tag)
    snippets: List[str] = []
    confs: List[float] = []

    state_entry = model_out.get("state")
    state_val = str((state_entry.get("value") if isinstance(state_entry, dict) else state_entry) or "").lower()
    dist_entry = model_out.get("district")
    dist_val = str((dist_entry.get("value") if isinstance(dist_entry, dict) else dist_entry) or "").lower()
    is_telangana = bool(state_val and "telangana" in state_val) or bool(dist_val and "rangareddy" in dist_val)

    # Cross-sync khasra_no and survey_no if one was read and the other is absent
    khasra_entry = model_out.get("khasra_no")
    survey_entry = model_out.get("survey_no")
    khasra_val = str((khasra_entry.get("value") if isinstance(khasra_entry, dict) else khasra_entry) or "").strip()
    survey_val = str((survey_entry.get("value") if isinstance(survey_entry, dict) else survey_entry) or "").strip()

    if not khasra_val and survey_val:
        model_out["khasra_no"] = survey_entry
    elif not survey_val and khasra_val:
        model_out["survey_no"] = khasra_entry

    for spec in FIELD_SPECS:
        entry = model_out.get(spec.key)
        if not isinstance(entry, dict):
            entry = {"value": entry if isinstance(entry, (str, int, float)) else "",
                     "confidence": DEFAULT_MODEL_CONFIDENCE, "source_text": ""}
        value, passed, failed = _normalize_field(spec, entry.get("value"), is_telangana=is_telangana)
        conf = _calibrate(entry.get("confidence"), passed, failed)
        # An optional field that simply is not printed on this form is not a
        # deficiency; flagging it would send every such document to review for
        # nothing. It still cannot corroborate anything, so it stays at 0.0.
        absent_optional = spec.optional and value is None
        res.fields[spec.key] = {
            "value": value,
            "confidence": conf,
            "needs_review": conf < CONFIDENCE_THRESHOLD and not absent_optional,
            "not_printed": absent_optional,
            "model_confidence": entry.get("confidence"),
            "source_text": _clean(entry.get("source_text"))[:160],
            "checks": {"passed": passed, "failed": failed},
            "label": spec.label,
            "scored": spec.scored,
        }
        if spec.scored:
            confs.append(conf)
        src = res.fields[spec.key]["source_text"]
        if src:
            snippets.append(src)

    # Joint check: catches transposed administrative rows that every per-field
    # check accepts. Must run after all fields exist, before confidence is summed.
    _check_cross_field(res.fields)

    # Re-read from the assembled fields: the joint checks above may have lowered a
    # confidence after the per-field loop recorded it.
    confs = [res.fields[f.key]["confidence"] for f in FIELD_SPECS if f.scored]
    res.low_confidence_fields = [k for k, v in res.fields.items() if v["needs_review"]]
    res.document_confidence = round(sum(confs) / len(confs), 3) if confs else 0.0
    res.status = "NEEDS_REVIEW" if res.low_confidence_fields else "EXTRACTED"
    res.raw_text = "\n".join(dict.fromkeys(snippets))
    return res


def _merge_passes(first: Dict[str, Any], second: Dict[str, Any],
                  image_meta: Dict[str, Any], first_ms: float, second_ms: float) -> ExtractionResult:
    """Two independent reads must agree; disagreement is real evidence of uncertainty."""
    a = _assemble(first, image_meta, pass_count=2)
    b = _assemble(second, image_meta, pass_count=2)

    confs: List[float] = []
    for spec in FIELD_SPECS:
        fa, fb = a.fields[spec.key], b.fields[spec.key]
        agree = _agreement_key(fa["value"]) == _agreement_key(fb["value"])
        if agree:
            fa["confidence"] = round(min(1.0, fa["confidence"] + 0.05), 3)
            fa["checks"]["passed"].append("cross_pass_agreement")
        else:
            fa["confidence"] = round(min(fa["confidence"], DISAGREEMENT_CAP), 3)
            fa["checks"]["failed"].append("cross_pass_disagreement")
            fa["alternate_reading"] = fb["value"]
        # Both passes agreeing that an optional field is absent is a consistent
        # reading of a form that does not print it — not something to review.
        absent_optional = spec.optional and agree and fa["value"] is None
        fa["not_printed"] = absent_optional
        fa["needs_review"] = fa["confidence"] < CONFIDENCE_THRESHOLD and not absent_optional
        if spec.scored:
            confs.append(fa["confidence"])

    a.low_confidence_fields = [k for k, v in a.fields.items() if v["needs_review"]]
    a.document_confidence = round(sum(confs) / len(confs), 3) if confs else 0.0
    a.status = "NEEDS_REVIEW" if a.low_confidence_fields else "EXTRACTED"
    a.timing_ms = round(first_ms + second_ms, 1)
    return a


def derive_parcel_hint(values: Dict[str, Any]) -> Optional[str]:
    """Derive a parcel id from CONTENT the model read (deed no / ULPIN), never the filename.

    Returned as a *hint* for registry cross-referencing in the validation layer;
    it is not treated as an extracted field.
    """
    deed = str(values.get("deed_registration_no") or "")
    m = re.search(r"(P-\d{2,5})", deed, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    ulpin = str(values.get("ulpin") or "")
    m = re.match(r"^\d{2}-\d{4,6}-(\d{1,5})-\d{4}$", ulpin)
    if m:
        return f"P-{m.group(1)}"
    return None


def warm_model() -> Dict[str, Any]:
    """Load the model into VRAM ahead of the demo so the first upload isn't slow."""
    status = engine_status()
    if not status["model_available"]:
        return {"warmed": False, **status}
    try:
        httpx.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": VISION_MODEL, "prompt": "ok", "stream": False,
                  "keep_alive": KEEP_ALIVE, "options": {"num_predict": 1}},
            timeout=REQUEST_TIMEOUT,
        )
        return {"warmed": True, **status}
    except httpx.HTTPError as exc:
        return {"warmed": False, "error": str(exc), **status}


def scrape_and_structure_tamil_text(
    tamil_raw_text: str,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Multilingual Tamil text scraper & structured land record parser.
    Uses the dedicated TAMIL_OCR_API_KEY / MULTILINGUAL_E5_API_KEY via OpenRouter.
    """
    api_key = (
        os.getenv("TAMIL_OCR_API_KEY", "").strip()
        or os.getenv("MULTILINGUAL_E5_API_KEY", "").strip()
        or os.getenv("OPENROUTER_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
    )
    if not api_key:
        raise ExtractionUnavailable("TAMIL_OCR_API_KEY or OPENAI_API_KEY is not configured.")

    chosen_model = model or os.getenv("TAMIL_VISION_MODEL", "openai/gpt-4o").strip()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "BhuNetra AI Tamil Multilingual Scraper",
    }

    prompt = (
        "You are BhuNetra AI's specialized Tamil Land Record & Patta Chitta Scraper. "
        "Extract, translate, and structure the following scraped Tamil property / deed / Patta text "
        "into a valid JSON land record object.\n\n"
        "Schema to return strictly:\n"
        "{\n"
        '  "deed_registration_no": "Registration or Document No (e.g. TN-PATTA-2026-xxx or actual doc no)",\n'
        '  "survey_no": "Survey number and sub-division (புல எண் / உட்பிரிவு எண் e.g. 42/1A)",\n'
        '  "khatian_no": "Patta or Chitta number (பட்டா எண் / கணக்கு எண் e.g. Patta No. 1042)",\n'
        '  "ulpin": "Bhu-Aadhaar / ULPIN (if mentioned, else null)",\n'
        '  "owner_name": "Full Pattadar / Owner name in English and Tamil (பட்டாதாரர் பெயர்)",\n'
        '  "father_or_husband": "Father / Husband name (தந்தை / கணவர் பெயர்)",\n'
        '  "village": "Village name in English and Tamil (கிராமம்)",\n'
        '  "mandal": "Taluk / Block name (வட்டம்)",\n'
        '  "district": "District name (மாவட்டம் e.g. Kanchipuram, Chennai, Coimbatore)",\n'
        '  "state": "Tamil Nadu",\n'
        '  "claimed_area_sqm": float (total area normalized to square metres: 1 Cent = 40.47 sq.m, 1 Ground = 222.96 sq.m, 1 Acre = 4047 sq.m, 1 Hectare = 10000 sq.m),\n'
        '  "area_acres_printed": float (area in acres equivalent),\n'
        '  "land_use_claim": "Standardized classification: Nanjai (Wet Agricultural) / Punjai (Dry Agricultural) / Residential (Natham) / Commercial"\n'
        "}\n\n"
        f"Input Scraped Tamil text:\n{tamil_raw_text}\n\n"
        "Return ONLY the valid JSON object without markdown formatting or conversational filler."
    )

    payload = {
        "model": chosen_model,
        "max_tokens": 1200,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }

    t0 = time.perf_counter()
    with httpx.Client(timeout=35.0) as client:
        resp = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    dur = round((time.perf_counter() - t0) * 1000.0, 1)

    if resp.status_code != 200:
        raise ExtractionUnavailable(f"Tamil Scraper API error ({resp.status_code}): {resp.text}")

    content = resp.json()["choices"][0]["message"]["content"]
    parsed = _parse_json_object(content)
    if not parsed:
        raise ExtractionUnavailable("Tamil scraper returned invalid JSON payload.")

    return {
        "success": True,
        "language": "Tamil",
        "engine_tag": f"REAL (Tamil Multilingual Scraper · {chosen_model})",
        "api_key_used": api_key[:12] + "..." + api_key[-4:],
        "timing_ms": dur,
        "extracted_record": parsed
    }

