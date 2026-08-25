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
import io
import json
import os
import re
import difflib
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageOps

# --- Configuration (env-overridable; no magic numbers scattered in code) -----
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")

MAX_EDGE = int(os.getenv("EXTRACTION_MAX_EDGE", "1280"))       # VRAM guardrail
REQUEST_TIMEOUT = float(os.getenv("EXTRACTION_TIMEOUT", "300"))  # cold start is slow
KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "15m")             # keep weights resident

CONFIDENCE_THRESHOLD = float(os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", "0.75"))
FORMAT_FAIL_CAP = 0.40      # a field failing its Dharani format cannot be "high confidence"
MISSING_CONFIDENCE = 0.0
DEFAULT_MODEL_CONFIDENCE = 0.5   # model omitted its own score
NORMALISED_CAP = 0.90       # value had to be corrected to master data -> not pristine
DISAGREEMENT_CAP = 0.45     # two passes read it differently -> human must decide

ENGINE_TAG_REAL = f"REAL (Vision-Language Extraction · {VISION_MODEL} via local Ollama)"


class ExtractionUnavailable(RuntimeError):
    """Raised when the local extraction engine cannot be reached or the model is missing."""


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


VILLAGES = ("Shamshabad", "Mamidipally", "Kothwalguda")
LAND_USES = ("Agricultural", "Residential", "Commercial")

FIELD_SPECS: Tuple[FieldSpec, ...] = (
    FieldSpec("deed_registration_no", "దస్తావేజు నమోదు సంఖ్య / Deed Registration No.",
              "the deed registration number, e.g. TS-DHARANI-2026-P-105",
              pattern=r"^TS-DHARANI-\d{4}-P-\d{2,5}$"),
    FieldSpec("survey_no", "సర్వే నంబర్ / Survey No.",
              "the survey / sub-division number, e.g. 104/A",
              pattern=r"^\d{1,4}\s*/\s*[A-Za-z0-9]{1,3}$"),
    FieldSpec("khatian_no", "ఖాతా నంబర్ / Khatian No.",
              "the khatian / passbook number, e.g. KH-204",
              pattern=r"^KH-\d{2,5}$"),
    FieldSpec("ulpin", "ULPIN / Unique Land Parcel ID",
              "the ULPIN unique land parcel identification number, e.g. 36-78431-105-2026",
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


def _build_prompt() -> str:
    lines = [
        "You are a data-entry assistant digitizing an Indian land record: a Telangana "
        "Dharani Record of Rights (RoR / Pahani, Form 1-B). The document is bilingual "
        "Telugu and English and may be a scan of a printed form or a hand-filled form.",
        "",
        "Read ONLY what is actually visible on this page. Extract these fields:",
    ]
    for f in FIELD_SPECS:
        lines.append(f'  - "{f.key}"  ({f.label}): {f.prompt_hint}')
    lines += [
        "",
        "Rules:",
        "  1. Transcribe exactly what is printed or written. Do not correct, complete, "
        "     or invent values, and do not use outside knowledge of Indian land records.",
        "  2. Where a value appears in both Telugu and English, report the ENGLISH form.",
        "  3. If a field is absent, illegible, or you are guessing, set value to \"\" "
        "     and confidence to a low number. An empty field is far better than a guess.",
        "  4. confidence is your own certainty for THAT field, from 0.0 to 1.0. Handwriting, "
        "     blur, smudges, ink over printed lines and skew should all lower it.",
        "  5. source_text is the short verbatim text you read that field from.",
        "",
        "Respond with JSON only.",
    ]
    return "\n".join(lines)


PROMPT = _build_prompt()


# --- Image preprocessing -----------------------------------------------------
def preprocess_image(raw: bytes) -> Tuple[str, Dict[str, Any]]:
    """Normalize an uploaded scan and return (base64 PNG, metadata).

    Downscaling to MAX_EDGE keeps the vision tower inside 6 GB of VRAM; EXIF
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
    meta["submitted_size"] = list(img.size)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    meta["submitted_bytes"] = buf.tell()
    return base64.b64encode(buf.getvalue()).decode("ascii"), meta


# --- Ollama transport --------------------------------------------------------
def engine_status() -> Dict[str, Any]:
    """Probe the local engine. Used by /ocr/engine-status and startup warm-up."""
    status = {
        "engine": "Ollama (local vision-language model)",
        "host": OLLAMA_HOST,
        "model": VISION_MODEL,
        "reachable": False,
        "model_available": False,
        "installed_models": [],
        "engine_tag": "UNAVAILABLE",
        "hint": None,
    }
    try:
        resp = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=5.0)
        resp.raise_for_status()
        names = [m.get("name", "") for m in resp.json().get("models", [])]
        status["reachable"] = True
        status["installed_models"] = names
        base = VISION_MODEL.split(":")[0]
        status["model_available"] = any(n == VISION_MODEL or n.startswith(base) for n in names)
    except Exception:  # noqa: BLE001 - a probe never raises
        status["hint"] = ("Ollama is not responding. Install it from https://ollama.com/download, "
                          "then run: ollama pull " + VISION_MODEL)
        return status

    if status["model_available"]:
        status["engine_tag"] = ENGINE_TAG_REAL
    else:
        status["hint"] = f"Ollama is running but the model is missing. Run: ollama pull {VISION_MODEL}"
    return status


def _call_ollama(image_b64: str, temperature: float, seed: int) -> Dict[str, Any]:
    """One extraction pass. Returns the parsed JSON object the model produced."""
    payload = {
        "model": VISION_MODEL,
        "prompt": PROMPT,
        "images": [image_b64],
        "stream": False,
        "format": _response_schema(),
        "keep_alive": KEEP_ALIVE,
        "options": {
            "temperature": temperature,
            "seed": seed,
            "num_predict": 1600,
            "num_ctx": 4096,
        },
    }
    try:
        resp = httpx.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=REQUEST_TIMEOUT)
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


def _normalize_field(spec: FieldSpec, raw_value: Any) -> Tuple[Any, List[str], List[str]]:
    """Return (value, passed_checks, failed_checks) for one field."""
    passed: List[str] = []
    failed: List[str] = []
    value: Any = _clean(raw_value)

    if not value:
        failed.append("field_missing_or_illegible")
        return None, passed, failed

    if spec.numeric:
        # The extent cell on a Dharani RoR prints "15075.63 sq.m (3.73 ఎకరాలు)", so the
        # raw read can carry thousands separators, a unit, and a parenthesised acre
        # equivalent. Take the first numeric run rather than stripping characters —
        # stripping leaves the dot in "sq.m" attached to the number.
        compact = value.replace(",", "").replace("٫", ".")
        num_match = re.search(r"\d+(?:\.\d+)?", compact)
        if not num_match:
            failed.append("not_a_number")
            return value, passed, failed
        num = float(num_match.group(0))

        # Acres-only read: convert so the stored unit is always square metres, and
        # disclose the conversion so the officer sees the value was transformed.
        tail = compact[num_match.end():].casefold()
        if re.match(r"\s*(ac\b|acre|ఎకర)", tail) and "sq" not in compact.casefold():
            num *= 4046.86
            failed.append("converted_from_acres")

        if num <= 0 or num > 5_000_000:
            failed.append("area_outside_plausible_range")
            return round(num, 2), passed, failed
        passed.append("numeric_range_ok")
        return round(num, 2), passed, failed

    if spec.key == "survey_no":
        value = value.replace(" ", "")

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


def extract_document(raw_bytes: bytes, passes: str | int = "auto") -> ExtractionResult:
    """Extract Dharani RoR fields from real image bytes.

    passes: 1 -> single pass (fast, stage demo)
            2 -> always cross-check with a second independent pass
            "auto" -> second pass only if pass 1 produced any low-confidence field
    """
    image_b64, image_meta = preprocess_image(raw_bytes)

    first = _call_ollama(image_b64, temperature=0.0, seed=7)
    result = _assemble(first, image_meta, pass_count=1)
    result.timing_ms = first.get("_timing", {}).get("total_duration_ms", 0.0)

    wants_second = (passes == 2) or (passes == "auto" and bool(result.low_confidence_fields))
    if not wants_second:
        return result

    second = _call_ollama(image_b64, temperature=0.35, seed=101)
    return _merge_passes(first, second, image_meta,
                         first_ms=result.timing_ms,
                         second_ms=second.get("_timing", {}).get("total_duration_ms", 0.0))


def _assemble(model_out: Dict[str, Any], image_meta: Dict[str, Any],
              pass_count: int) -> ExtractionResult:
    res = ExtractionResult(passes=pass_count, image_meta=image_meta)
    snippets: List[str] = []
    confs: List[float] = []

    for spec in FIELD_SPECS:
        entry = model_out.get(spec.key)
        if not isinstance(entry, dict):
            entry = {"value": entry if isinstance(entry, (str, int, float)) else "",
                     "confidence": DEFAULT_MODEL_CONFIDENCE, "source_text": ""}
        value, passed, failed = _normalize_field(spec, entry.get("value"))
        conf = _calibrate(entry.get("confidence"), passed, failed)
        res.fields[spec.key] = {
            "value": value,
            "confidence": conf,
            "needs_review": conf < CONFIDENCE_THRESHOLD,
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
        fa["needs_review"] = fa["confidence"] < CONFIDENCE_THRESHOLD
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
