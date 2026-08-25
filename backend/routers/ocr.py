"""
Engine 1 — Registry OCR / document extraction (HTTP layer only).

This router parses the request and delegates to `services.extraction_service`;
no extraction logic lives here (controllers thin, services own the logic).

Removed in this phase: the previous filename-lookup implementation, which read
`P-105` out of the *filename* and returned the answer from `parcels.geojson`
without ever looking at the image. Extraction now runs on the uploaded bytes.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query

try:
    from services import extraction_service as ex
except ImportError:  # running as `backend.main`
    from backend.services import extraction_service as ex

router = APIRouter(prefix="/ocr", tags=["Engine 1 - Registry OCR"])

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")


async def _read_upload(file: UploadFile) -> bytes:
    name = (file.filename or "").lower()
    if name and not name.endswith(ALLOWED_SUFFIXES):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Upload a scanned page: {', '.join(ALLOWED_SUFFIXES)}",
        )
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Scan exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )
    return contents


@router.get("/engine-status")
def get_engine_status():
    """Report whether the local extraction engine is live. Drives the UI engine badge."""
    return {"success": True, "data": ex.engine_status()}


@router.post("/warm")
def warm():
    """Pre-load model weights into VRAM so the first demo upload is not slow."""
    return {"success": True, "data": ex.warm_model()}


@router.post("/extract")
async def extract_deed(
    file: UploadFile = File(...),
    passes: str = Query("auto", pattern="^(1|2|auto)$",
                        description="1 = fast single read, 2 = always cross-check, "
                                    "auto = second read only when confidence is low"),
):
    """Extract Dharani RoR fields from a scanned or photographed land record."""
    contents = await _read_upload(file)
    passes_arg = int(passes) if passes in {"1", "2"} else "auto"

    try:
        result = ex.extract_document(contents, passes=passes_arg)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ex.ExtractionUnavailable as exc:
        # Honest failure. No filename or registry fallback: a fabricated
        # "successful" extraction would be worse than an outage.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payload = result.to_dict()
    payload["source_filename"] = file.filename
    payload["parcel_id_hint"] = ex.derive_parcel_hint(payload["values"])
    payload["parcel_id_hint_source"] = (
        "derived from the deed registration number / ULPIN read off the page"
    )
    return {"success": True, "data": payload}


@router.post("/process-deed", deprecated=True)
async def process_scanned_deed(file: UploadFile = File(...)):
    """Deprecated alias kept so the current UI keeps working until the frontend
    restructure lands. Runs the same real extraction and flattens it to the old
    response shape."""
    contents = await _read_upload(file)
    try:
        result = ex.extract_document(contents, passes=1)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ex.ExtractionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    values = {k: v["value"] for k, v in result.fields.items()}
    return {
        "status": result.status,
        "deprecated": True,
        "use_instead": "/api/ocr/extract",
        "extracted_data": {
            "parcel_id": ex.derive_parcel_hint(values),
            "registered_owner": values.get("owner_name"),
            "khatian_no": values.get("khatian_no"),
            "survey_no": values.get("survey_no"),
            "village": values.get("village"),
            "mandal": values.get("mandal"),
            "district": values.get("district"),
            "state": values.get("state"),
            "claimed_area_sqm": values.get("claimed_area_sqm"),
            "land_use_claim": values.get("land_use_claim"),
            "ulpin": values.get("ulpin"),
            "deed_registration_no": values.get("deed_registration_no"),
            "ocr_confidence_score": result.document_confidence,
            "raw_ocr_snippet": result.raw_text,
        },
        "low_confidence_fields": result.low_confidence_fields,
        "engine_tag": result.engine_tag,
    }
