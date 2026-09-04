"""
Engine 1 — Registry OCR / document extraction (HTTP layer only).

This router parses the request and delegates to `services.extraction_service`;
no extraction logic lives here (controllers thin, services own the logic).

Removed in this phase: the previous filename-lookup implementation, which read
`P-105` out of the *filename* and returned the answer from `parcels.geojson`
without ever looking at the image. Extraction now runs on the uploaded bytes.
"""

from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel

try:
    from services import extraction_service as ex
except ImportError:  # running as `backend.main`
    from backend.services import extraction_service as ex

router = APIRouter(prefix="/ocr", tags=["Engine 1 - Registry OCR"])

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".pdf")


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
    """Report whether the extraction engine is live and its supported Indian languages."""
    return {"success": True, "data": ex.engine_status()}


@router.get("/languages")
def get_supported_languages():
    """Return the list of all supported Indian regional languages for OCR."""
    try:
        from services import ocr_space_service
    except ImportError:
        from backend.services import ocr_space_service
    return {"success": True, "data": ocr_space_service.get_supported_languages()}


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
    language: str = Query("auto", description="Indic language code (auto, hin, tel, tam, kan, mar, guj, ben, pan, mal, urd, eng)"),
):
    """Extract land record fields from a scanned or photographed land record using OCR.Space Indic Engine."""
    contents = await _read_upload(file)
    passes_arg = int(passes) if passes in {"1", "2"} else "auto"

    try:
        result = ex.extract_document(contents, passes=passes_arg, allow_fallback=True, language=language or "auto")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ex.ExtractionUnavailable as exc:
        # Honest failure when neither OCR.Space nor fallback could parse
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payload = result.to_dict()
    payload["source_filename"] = file.filename

    try:
        from services import uploaded_parcels
    except ImportError:
        from backend.services import uploaded_parcels

    up_feature = uploaded_parcels.register_uploaded_parcel(payload.get("values", {}), filename=file.filename)
    payload["parcel_id_hint"] = up_feature["properties"]["parcel_id"]
    payload["uploaded_feature"] = up_feature
    payload["parcel_id_hint_source"] = (
        f"derived from the uploaded deed (Survey/Khasra {up_feature['properties']['survey_no']})"
    )
    return {"success": True, "data": payload}


@router.post("/process-deed", deprecated=True)
async def process_scanned_deed(
    file: UploadFile = File(...),
    language: str = Query("auto")
):
    """Deprecated alias kept so older components keep working. Runs OCR.Space Indic extraction."""
    contents = await _read_upload(file)
    try:
        result = ex.extract_document(contents, passes=1, allow_fallback=True, language=language or "auto")
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


class TamilScrapeRequest(BaseModel):
    tamil_text: str
    model: Optional[str] = None


@router.post("/scrape-tamil")
def scrape_tamil_record(req: TamilScrapeRequest):
    """
    Scrape and structure Tamil land record / Patta Chitta text using the dedicated
    Tamil multilingual model & TAMIL_OCR_API_KEY.
    """
    if not req.tamil_text or not req.tamil_text.strip():
        raise HTTPException(status_code=400, detail="tamil_text cannot be empty.")
    try:
        res = ex.scrape_and_structure_tamil_text(req.tamil_text, model=req.model)
        rec = res.get("extracted_record", {})
        dynamic_plot = uploaded_parcels.register_uploaded_parcel(
            fields=rec,
            filename="scraped_tamil_record.txt"
        )
        res["dynamic_gis_plot"] = dynamic_plot
        return res
    except ex.ExtractionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/paddle-extract")
async def paddle_ocr_extract(
    file: UploadFile = File(...),
    lang: str = Query("en", description="PaddleOCR language: 'en', 'devanagari', 'tamil', 'telugu', 'kannada', 'bengali'"),
):
    """
    Ultra-fast multilingual document OCR and cadastral field extraction using PaddleOCR (PP-OCRv4).
    """
    contents = await _read_upload(file)
    try:
        try:
            from services import paddle_ocr_service as p_ocr
        except ImportError:
            from backend.services import paddle_ocr_service as p_ocr

        res = p_ocr.extract_cadastral_fields_paddle(contents, lang=lang)
        res["source_filename"] = file.filename
        return {"success": True, "data": res}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PaddleOCR extraction error: {exc}") from exc

