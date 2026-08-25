# Phase 2 — Extraction Engine (Engine 1)

**Status:** code complete and offline-verified. Live accuracy numbers pending the
one-time Ollama model install (below).

---

## 1. What changed, and why it matters

The previous `/ocr/process-deed` **never looked at the image**. It regex-matched the
*filename* (`scan_P-105.png` → `P-105`), looked the answer up in `parcels.geojson`,
and returned a hardcoded `0.95` confidence with a manufactured "raw OCR snippet".
Rename the file and the "OCR" produced the wrong record; upload a scan that wasn't in
the registry and it silently returned parcel P-105's data. The PaddleOCR branch was
dead code (`np.array` with numpy never imported).

That is now gone. Extraction runs on the uploaded bytes through an on-device
vision-language model, and there is **no filename path and no registry fallback**.

| | Before | After |
|---|---|---|
| Input actually read | filename string | image pixels |
| Confidence | hardcoded 0.95 / 0.88 | per-field, calibrated against deterministic checks |
| Unknown document | returns P-105's data | reads it, or fails honestly |
| Engine offline | fake success | HTTP 503 with a fix hint |
| Field provenance | none | `source_text` + passed/failed checks per field |

---

## 2. Architecture

```
upload bytes
  → preprocess        EXIF-transpose, RGB, downscale to ≤1280px (6 GB VRAM guardrail)
  → Ollama            qwen2.5vl:3b, temperature 0, JSON-schema-constrained output
  → normalize         per-field regex format checks + master-data reconciliation
  → calibrate         model self-report adjusted by deterministic evidence
  → route             any field < 0.75 confidence ⇒ document status NEEDS_REVIEW
```

**Confidence is never the model's raw self-opinion.** A VLM's self-reported certainty
is poorly calibrated, so the final per-field score starts there and is then adjusted by:

- **Format validation** — a khatian that doesn't match `KH-\d+` is capped at 0.40 even
  if the model claimed 0.97.
- **Master-data reconciliation** — village/mandal/district/land-use are matched against
  finite government master lists. A near-miss (`Shamshabaad` → `Shamshabad`) is repaired,
  but the repair is *disclosed* and the field is capped at 0.90, never presented as pristine.
  A value outside the list is flagged, not silently replaced.
- **Cross-pass agreement** — when pass 1 produces any low-confidence field, a second
  independent read runs at a different temperature. Fields where the two reads disagree
  are capped at 0.45 and the alternate reading is shown to the officer.

Every adjustment is recorded in `checks.passed` / `checks.failed`, so the UI explains
*why* a field is amber instead of just colouring it.

**Honesty over convenience.** If Ollama is down or the model is missing, the service
raises and the API returns 503. It never fabricates fields — a fake success is worse
than an outage.

**Data sovereignty.** The model runs on-device. No page of any citizen's land record
leaves the machine, and the demo needs no network.

---

## 3. Files

| File | Status | Purpose |
|---|---|---|
| `backend/services/extraction_service.py` | **new** | The engine: preprocessing, Ollama transport, field spec, normalization, calibration, cross-pass merge |
| `backend/routers/ocr.py` | **rewritten** | Thin HTTP layer; filename lookup deleted |
| `backend/tests/test_extraction_pipeline.py` | **new** | 50 offline checks (stubs the model, verifies everything else) |
| `backend/tools/run_extraction_benchmark.py` | **new** | Live accuracy harness over all 16 scans vs ground truth |
| `backend/services/__init__.py` | **new** | Service package |
| `backend/main.py` | modified | Background model warm-up on startup; engine status in `/` |
| `frontend/src/components/OCRScanner.jsx` | **rewritten** | Per-field confidence cards, amber review inputs, honest error state |
| `requirements.txt` | **new** | Pinned deps + Ollama setup notes |

---

## 4. API

### `POST /api/ocr/extract?passes=auto`
`passes`: `1` (fast) · `2` (always cross-check) · `auto` (second read only when confidence is low)

```json
{
  "success": true,
  "data": {
    "status": "NEEDS_REVIEW",
    "engine_tag": "REAL (Vision-Language Extraction · qwen2.5vl:3b via local Ollama)",
    "passes": 2,
    "document_confidence": 0.71,
    "confidence_threshold": 0.75,
    "low_confidence_fields": ["khatian_no"],
    "fields": {
      "khatian_no": {
        "value": "KH-2O4",
        "confidence": 0.4,
        "needs_review": true,
        "model_confidence": 0.88,
        "source_text": "KH-2O4",
        "checks": { "passed": [], "failed": ["format_invalid"] },
        "label": "ఖాతా నంబర్ / Khatian No.",
        "scored": true
      }
    },
    "values": { "khatian_no": "KH-2O4" },
    "raw_text": "...",
    "parcel_id_hint": "P-106",
    "parcel_id_hint_source": "derived from the deed registration number / ULPIN read off the page"
  }
}
```

`parcel_id_hint` is derived from the **deed number / ULPIN the model read off the page**,
never from the filename. It is a hint for the validation layer, not an extracted field.

### `GET /api/ocr/engine-status`
Reports reachability, installed models, and a fix hint. Drives the UI engine badge.

### `POST /api/ocr/warm`
Loads weights into VRAM so the first demo upload isn't slow. Also fired in a background
thread at server startup.

### `POST /api/ocr/process-deed` *(deprecated)*
Kept so the existing UI path keeps working until the frontend restructure; runs the same
real extraction and flattens it to the old response shape.

---

## 5. How to run it

**One-time setup** (this is the only outstanding step):

```bash
winget install Ollama.Ollama
```

```bash
ollama pull qwen2.5vl:3b
```

**Run the backend:**

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**Run the frontend:**

```bash
cd frontend && npm run dev
```

---

## 6. How to test it

**Offline pipeline tests — no GPU or model needed (currently 50/50 passing):**

```bash
python backend/tests/test_extraction_pipeline.py
```

Covers: image preprocessing and downscaling, tolerant JSON parsing, numeric/unit
normalization (`"15,075.63 sq.m (3.73 ఎకరాలు)"` → `15075.63`; acres auto-converted and
disclosed), format-failure capping, master-data reconciliation, cross-pass disagreement
handling, auto-escalation to a second read, honest failure on engine outage, ground-truth
conformance across all 16 scans, and an AST-level assertion that neither the router nor
the service touches the registry or the filesystem.

**Live accuracy benchmark (after `ollama pull`):**

```bash
python backend/tools/run_extraction_benchmark.py
```

Writes `data/synthetic/extraction_benchmark.json` and reports field accuracy overall and
split printed/handwritten, plus two calibration metrics that matter more than raw accuracy:

- **High-confidence accuracy** — of the fields the engine did *not* flag, how many were right.
- **Review-flag recall** — of the fields it got wrong, how many it correctly routed to an officer.

A digitization system is only trustworthy if its uncertainty is honest, so those are the
numbers the Collector dashboard will surface in Phase 7.

**Proving it isn't a filename trick (the judge-facing demo):**

1. Copy `data/synthetic/registry_scans/scan_P-105.png` to `xyz123.png` and upload it —
   the same fields still come back.
2. Upload the handwritten `scan_P-106.png` — low-confidence fields render amber with
   editable inputs and the document status becomes `NEEDS_REVIEW`.
3. Stop Ollama and upload anything — a clear 503, no invented data.

---

## 7. What's left

Phase 2 is code-complete. Outstanding before it can be signed off:

- [ ] `ollama pull qwen2.5vl:3b`, then run the benchmark and record the real numbers here.
- [ ] Tune the prompt against measured per-field errors (survey-no slashes and ULPIN digit
      groups are the likely weak spots).
- [ ] Optional Surya OCR Telugu reading-assist for the handwritten cases, if the 3B model's
      handwritten accuracy proves too low.

Then Phase 3: `documents` table + status state machine (`UPLOADED → EXTRACTED →
NEEDS_REVIEW → VERIFIED → APPROVED`), persisting extractions and officer corrections.
