"""
routers/documents.py — Phase 3: Document lifecycle management.

Implements the UPLOADED → EXTRACTED → NEEDS_REVIEW → VERIFIED → APPROVED / REJECTED
state machine for scanned land-record documents.

Each endpoint validates transitions and records audit metadata so the Officer Audit Log
is always consistent with the document state.

API surface
-----------
POST   /documents/upload          Upload a scan and register it
GET    /documents/               List documents (filterable)
GET    /documents/{id}          Fetch a single document with full extraction result
POST   /documents/{id}/extract  Re-run OCR extraction on the stored scan
POST   /documents/{id}/review    Officer corrects extracted fields and transitions state
POST   /documents/{id}/approve  Officer approves → APPROVED + SHA-256 hash generated
POST   /documents/{id}/reject    Officer rejects → REJECTED (terminal)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Document

# ---------------------------------------------------------------------------
# Pydantic schemas for request/response bodies
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    document_id: int
    status: str
    source_filename: str
    file_hash: str
    preview_url: str | None = None
    page_count: int = 1
    message: str


class ExtractResponse(BaseModel):
    document_id: int
    status: str
    parcel_id_hint: str | None
    extraction_confidence: float
    low_confidence_fields: list[str]
    engine_tag: str
    passes: int
    timing_ms: float
    preview_url: str | None = None
    page_count: int = 1
    fields: dict | None = None
    extracted_fields: dict | None = None
    raw_text: str | None = None
    uploaded_feature: dict | None = None


class OfficerCorrection(BaseModel):
    field_key: str
    corrected_value: str


class ReviewRequest(BaseModel):
    officer_name: str
    reason: str
    corrections: list[OfficerCorrection] = []
    target_status: str = "VERIFIED"   # VERIFIED or REJECTED


class ReviewResponse(BaseModel):
    document_id: int
    status: str
    reviewed_by: str
    reviewed_at: str
    corrections_applied: int
    reason: str
    message: str


class ApproveResponse(BaseModel):
    document_id: int
    status: str
    blockchain_hash: str
    timestamp: str
    message: str


class DocumentListResponse(BaseModel):
    total: int
    documents: list[dict]


class BatchUploadResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[dict]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
ALLOWED_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".pdf")


def _file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _serialize(doc: Document) -> dict:
    """Convert a Document row into the API response shape."""
    try:
        extraction_result = json.loads(doc.extraction_result or "{}")
    except json.JSONDecodeError:
        extraction_result = {}

    try:
        extracted_fields = json.loads(doc.extracted_fields or "{}")
    except json.JSONDecodeError:
        extracted_fields = {}

    try:
        low_conf_fields = json.loads(doc.low_confidence_fields or "[]")
    except json.JSONDecodeError:
        low_conf_fields = []

    try:
        corrections = json.loads(doc.officer_corrections or "{}")
    except json.JSONDecodeError:
        corrections = {}

    return {
        "id": doc.id,
        "source_filename": doc.source_filename,
        "file_hash": doc.file_hash or "",
        "status": doc.status,
        "parcel_id": doc.parcel_id,
        "parcel_id_hint": doc.parcel_id_hint,
        "upload_timestamp": doc.upload_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") if doc.upload_timestamp else None,
        "extraction_confidence": doc.extraction_confidence,
        "extraction_passes": doc.extraction_passes,
        "extraction_timing_ms": doc.extraction_timing_ms,
        "extraction_timestamp": doc.extraction_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") if doc.extraction_timestamp else None,
        "extraction_engine_tag": doc.extraction_engine_tag,
        "low_confidence_fields": low_conf_fields,
        "extraction_result": extraction_result,
        "extracted_fields": extracted_fields,
        "reviewed_by": doc.reviewed_by,
        "reviewed_at": doc.reviewed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if doc.reviewed_at else None,
        "review_reason": doc.review_reason,
        "officer_corrections": corrections,
        "blockchain_hash": doc.blockchain_hash,
        "blockchain_timestamp": doc.blockchain_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") if doc.blockchain_timestamp else None,
        "lifecycle": {
            "current": doc.status,
            "valid_transitions": list(Document.valid_transitions().get(doc.status, [])),
            "is_terminal": doc.status in {"APPROVED", "REJECTED"},
        },
    }


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/documents", tags=["Phase 3 — Document Lifecycle"])

MAX_BATCH_FILES = 20


@router.post("/batch", response_model=BatchUploadResponse)
async def batch_upload_documents(
    files: list[UploadFile] = File(...),
    extract: bool = Query(False, description="Automatically run extraction after upload"),
    db: Session = Depends(get_db),
):
    """
    Upload multiple document scans in a single request and optionally run
    OCR extraction on each one sequentially.

    Each file that fails validation is recorded in the results array with
    an error message rather than aborting the entire batch.
    """
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum {MAX_BATCH_FILES} files per batch request.",
        )

    results = []
    succeeded = 0
    failed = 0

    for file in files:
        name = (file.filename or "").lower()
        try:
            # --- upload step ---
            if name and not name.endswith(ALLOWED_SUFFIXES):
                raise ValueError(f"Unsupported file type: {name}")

            data = await file.read()
            if not data:
                raise ValueError("Empty upload.")
            if len(data) > MAX_UPLOAD_BYTES:
                raise ValueError(f"File exceeds the 12 MB limit.")

            fhash = _file_hash(data)

            # Persist
            data_dir = Path(__file__).parent.parent.parent / "data"
            uploads_dir = data_dir / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            file_path = uploads_dir / f"{fhash}_{file.filename}"
            if not file_path.exists():
                file_path.write_bytes(data)

            # Deduplicate
            existing = db.query(Document).filter(Document.file_hash == fhash).first()
            if existing:
                results.append({
                    "filename": file.filename,
                    "document_id": existing.id,
                    "status": existing.status,
                    "file_hash": fhash,
                    "extracted": False,
                    "error": None,
                })
                succeeded += 1
                continue

            doc = Document(
                source_filename=file.filename or "unknown",
                file_hash=fhash,
                status="UPLOADED",
                upload_timestamp=datetime.utcnow(),
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            entry = {
                "filename": file.filename,
                "document_id": doc.id,
                "status": doc.status,
                "file_hash": fhash,
                "extracted": False,
                "error": None,
            }

            # --- optional extraction step ---
            if extract:
                try:
                    scan_path = data_dir / "uploads" / f"{fhash}_{file.filename}"
                    if not scan_path.exists():
                        raise FileNotFoundError(f"Scan file not on disk: {file.filename}")

                    raw_bytes = scan_path.read_bytes()
                    from services import extraction_service as ex
                    result = ex.extract_document(raw_bytes, passes="auto")
                    result_dict = result.to_dict()
                    parcel_hint = ex.derive_parcel_hint(result_dict.get("values", {}))

                    doc.status = result.status
                    doc.extraction_result = json.dumps(result_dict)
                    doc.extracted_fields = json.dumps(result_dict.get("values", {}))
                    doc.extraction_confidence = result.document_confidence
                    doc.extraction_passes = result.passes
                    doc.extraction_timing_ms = result.timing_ms
                    doc.extraction_timestamp = datetime.utcnow()
                    doc.extraction_engine_tag = result.engine_tag
                    doc.low_confidence_fields = json.dumps(result.low_confidence_fields)
                    doc.parcel_id_hint = parcel_hint
                    db.commit()

                    entry["status"] = doc.status
                    entry["extracted"] = True
                    entry["extraction_confidence"] = result.document_confidence
                    entry["extraction_engine_tag"] = result.engine_tag
                    entry["low_confidence_fields"] = result.low_confidence_fields
                    entry["parcel_id_hint"] = parcel_hint
                except Exception as exc:
                    entry["extraction_error"] = str(exc)

            results.append(entry)
            succeeded += 1

        except ValueError as exc:
            results.append({
                "filename": file.filename,
                "document_id": None,
                "status": "FAILED",
                "file_hash": None,
                "extracted": False,
                "error": str(exc),
            })
            failed += 1
        except Exception as exc:
            results.append({
                "filename": file.filename,
                "document_id": None,
                "status": "FAILED",
                "file_hash": None,
                "extracted": False,
                "error": f"Unexpected error: {exc}",
            })
            failed += 1

    return BatchUploadResponse(
        total=len(files),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Register an uploaded scan and begin the document lifecycle.
    The document starts in UPLOADED state and is ready for extraction.
    """
    name = (file.filename or "").lower()
    if name and not name.endswith(ALLOWED_SUFFIXES):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Upload a scanned page: {', '.join(ALLOWED_SUFFIXES)}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Scan exceeds the 12 MB limit.")

    fhash = _file_hash(data)

    # Persist file bytes to disk
    data_dir = Path(__file__).parent.parent.parent / "data"
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / f"{fhash}_{file.filename}"
    if not file_path.exists():
        file_path.write_bytes(data)

    # Duplicate detection: if this exact file was already uploaded, return it instead.
    existing = db.query(Document).filter(Document.file_hash == fhash).first()
    if existing:
        page_cnt = 1
        if existing.source_filename.lower().endswith(".pdf"):
            try:
                import pypdfium2 as pdfium
                page_cnt = len(pdfium.PdfDocument(data))
            except Exception:
                page_cnt = 1
        return UploadResponse(
            document_id=existing.id,
            status=existing.status,
            source_filename=existing.source_filename,
            file_hash=fhash,
            preview_url=f"/api/documents/{existing.id}/page/1",
            page_count=page_cnt,
            message=f"Document already registered (id={existing.id}, status={existing.status}).",
        )

    doc = Document(
        source_filename=file.filename or "unknown",
        file_hash=fhash,
        status="UPLOADED",
        upload_timestamp=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    page_cnt = 1
    if (file.filename or "").lower().endswith(".pdf") or data.startswith(b"%PDF"):
        try:
            import pypdfium2 as pdfium
            page_cnt = len(pdfium.PdfDocument(data))
        except Exception:
            page_cnt = 1

    return UploadResponse(
        document_id=doc.id,
        status=doc.status,
        source_filename=doc.source_filename,
        file_hash=fhash,
        preview_url=f"/api/documents/{doc.id}/page/1",
        page_count=page_cnt,
        message=f"Document registered. Proceed to POST /documents/{doc.id}/extract to run OCR.",
    )


@router.get("/{doc_id}/page/{page_num}")
def get_document_page_image(doc_id: int, page_num: int = 1, db: Session = Depends(get_db)):
    """Render and stream page {page_num} of a document (PDF or image) as a high-resolution PNG."""
    import io
    from PIL import Image, ImageOps

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    data_dir = Path(__file__).parent.parent.parent / "data"
    uploads_dir = data_dir / "uploads"
    synthetic_dir = data_dir / "synthetic" / "registry_scans"

    scan_path = uploads_dir / f"{doc.file_hash}_{doc.source_filename}"
    if not scan_path.exists() and uploads_dir.exists():
        # Check by file hash prefix
        hash_matches = list(uploads_dir.glob(f"{doc.file_hash}*"))
        if hash_matches:
            scan_path = hash_matches[0]
    if not scan_path.exists():
        scan_path = synthetic_dir / doc.source_filename
    if not scan_path.exists() and synthetic_dir.exists():
        # Match by substring
        base_name = doc.source_filename.replace("odisha_bhubaneswar_", "").replace("delhi_", "")
        matches = list(synthetic_dir.glob(f"*{base_name}*")) or list(synthetic_dir.glob(f"*{doc.source_filename}*"))
        if matches:
            scan_path = matches[0]

    if not scan_path.exists():
        # Fallback to any sample deed scan
        sample_scans = list(synthetic_dir.glob("*.png")) if synthetic_dir.exists() else []
        if sample_scans:
            scan_path = sample_scans[0]
        else:
            raise HTTPException(status_code=404, detail="Scan file not on disk")

    raw_bytes = scan_path.read_bytes()

    # 1. If PDF, render the requested page via pypdfium2
    if raw_bytes.startswith(b"%PDF") or doc.source_filename.lower().endswith(".pdf"):
        try:
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(raw_bytes)
            idx = max(0, min(page_num - 1, len(pdf) - 1))
            page = pdf[idx]
            pil_img = page.render(scale=2.0).to_pil().convert("RGB")
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG", optimize=True)
            return Response(content=buf.getvalue(), media_type="image/png")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to render PDF page: {e}")

    # 2. If image, return normalized PNG
    try:
        pil_img = Image.open(io.BytesIO(raw_bytes))
        pil_img = ImageOps.exif_transpose(pil_img).convert("RGB")
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG", optimize=True)
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load image: {e}")


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    status: str | None = Query(None, description="Filter by lifecycle status"),
    parcel_id: str | None = Query(None, description="Filter by parcel ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all documents, optionally filtered."""
    q = db.query(Document)
    if status:
        q = q.filter(Document.status == status.upper())
    if parcel_id:
        q = q.filter(Document.parcel_id == parcel_id)

    total = q.count()
    docs = q.order_by(Document.upload_timestamp.desc()).offset(offset).limit(limit).all()

    return DocumentListResponse(
        total=total,
        documents=[_serialize(d) for d in docs],
    )


@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Fetch a single document with full extraction result."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    return _serialize(doc)


@router.post("/{doc_id}/extract", response_model=ExtractResponse)
def extract_document(
    doc_id: int,
    passes: str = Query("auto"),
    language: str = Query("auto", description="Indic language code"),
    db: Session = Depends(get_db)
):
    """
    Re-run Engine 1 OCR extraction on a previously-uploaded document using OCR.Space Indic Engine.

    transitions: UPLOADED → EXTRACTED / NEEDS_REVIEW
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")

    if doc.status not in {"UPLOADED", "EXTRACTED", "NEEDS_REVIEW"}:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot re-extract a document in status {doc.status}. "
                   f"Only UPLOADED/EXTRACTED/NEEDS_REVIEW can be re-processed.",
        )

    # Load extraction service lazily so the import never blocks boot
    try:
        from services import extraction_service as ex
    except ImportError:
        from backend.services import extraction_service as ex

    # Read the file bytes from uploads or static storage
    data_dir = Path(__file__).parent.parent.parent / "data"
    scan_path = data_dir / "uploads" / f"{doc.file_hash}_{doc.source_filename}"
    if not scan_path.exists():
        scan_path = data_dir / "synthetic" / "registry_scans" / doc.source_filename
    if not scan_path.exists():
        # Check any matching file in synthetic scans
        matches = list((data_dir / "synthetic" / "registry_scans").glob(f"*{doc.source_filename}*"))
        if matches:
            scan_path = matches[0]

    if not scan_path.exists():
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot locate scan file '{doc.source_filename}'. "
                "Please upload the deed scan again."
            ),
        )

    raw_bytes = scan_path.read_bytes()

    try:
        passes_arg = int(passes) if passes in {"1", "2"} else "auto"
        result = ex.extract_document(raw_bytes, passes=passes_arg, allow_fallback=True, language=language or "auto")
    except ex.ExtractionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Persist the extraction result
    result_dict = result.to_dict()

    try:
        from services import uploaded_parcels
    except ImportError:
        from backend.services import uploaded_parcels

    up_feature = uploaded_parcels.register_uploaded_parcel(
        result_dict.get("values", {}), doc_id=doc.id, filename=doc.source_filename
    )
    parcel_hint = up_feature["properties"]["parcel_id"]
    corrections: dict[str, str] = {}  # empty for a fresh extraction

    doc.status = result.status          # EXTRACTED or NEEDS_REVIEW
    doc.extraction_result = json.dumps(result_dict)
    doc.extracted_fields = json.dumps(result_dict.get("values", {}))
    doc.extraction_confidence = result.document_confidence
    doc.extraction_passes = result.passes
    doc.extraction_timing_ms = result.timing_ms
    doc.extraction_timestamp = datetime.utcnow()
    doc.extraction_engine_tag = result.engine_tag
    doc.low_confidence_fields = json.dumps(result.low_confidence_fields)
    doc.parcel_id_hint = parcel_hint
    doc.officer_corrections = json.dumps(corrections)

    db.commit()
    db.refresh(doc)

    return ExtractResponse(
        document_id=doc.id,
        status=doc.status,
        parcel_id_hint=parcel_hint,
        extraction_confidence=result.document_confidence,
        low_confidence_fields=result.low_confidence_fields,
        engine_tag=result.engine_tag,
        passes=result.passes,
        timing_ms=result.timing_ms,
        preview_url=f"/api/documents/{doc.id}/page/1",
        fields=result.fields,
        extracted_fields=result_dict.get("values", {}),
        raw_text=result.raw_text,
        uploaded_feature=up_feature,
    )


@router.post("/{doc_id}/review", response_model=ReviewResponse)
def review_document(doc_id: int, req: ReviewRequest, db: Session = Depends(get_db)):
    """
    Officer reviews extracted fields, applies corrections, and transitions state.

    Allowed transitions:
      - NEEDS_REVIEW → VERIFIED (officer accepted/corrected fields)
      - NEEDS_REVIEW → REJECTED (document is illegible / fraud detected)
      - EXTRACTED    → VERIFIED (officer accepts a clean extraction)
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")

    if doc.status not in {"EXTRACTED", "NEEDS_REVIEW"}:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot review a document in status {doc.status}. "
                   f"Only EXTRACTED / NEEDS_REVIEW can be reviewed.",
        )

    target = req.target_status.upper()
    if not doc.can_transition_to(target):
        raise HTTPException(
            status_code=409,
            detail=f"Invalid transition: {doc.status} → {target}. "
                   f"Allowed: {doc.valid_transitions().get(doc.status, [])}",
        )

    if not req.reason or len(req.reason.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="A typed reason of at least 5 characters is required for the audit trail.",
        )

    # Apply officer corrections to the stored extraction result
    try:
        corrections = {c.field_key: c.corrected_value for c in req.corrections}
    except Exception:
        corrections = {}

    doc.officer_corrections = json.dumps(corrections)
    doc.reviewed_by = req.officer_name
    doc.reviewed_at = datetime.utcnow()
    doc.review_reason = req.reason.strip()
    doc.transition_to(target)
    db.commit()
    db.refresh(doc)

    return ReviewResponse(
        document_id=doc.id,
        status=doc.status,
        reviewed_by=doc.reviewed_by,
        reviewed_at=doc.reviewed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        corrections_applied=len(corrections),
        reason=doc.review_reason,
        message=f"Document {doc_id} transitioned to {doc.status} by {doc.reviewed_by}.",
    )


@router.post("/{doc_id}/approve", response_model=ApproveResponse)
def approve_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Approve a VERIFIED document. Generates SHA-256 hash under IT Act 2000 Sec 65B.

    transitions: VERIFIED → APPROVED
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")

    if not doc.can_transition_to("APPROVED"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve document in status {doc.status}. "
                   f"Must be VERIFIED first. Allowed: {doc.valid_transitions().get(doc.status, [])}",
        )

    timestamp = datetime.utcnow()
    payload = (
        f"BHUNETRA:{doc.id}:{doc.source_filename}:{doc.file_hash}:"
        f"{doc.parcel_id or 'UNLINKED'}:{doc.extraction_confidence}:{timestamp.isoformat()}"
    )
    b_hash = "0x" + hashlib.sha256(payload.encode()).hexdigest()

    doc.transition_to("APPROVED")
    doc.blockchain_hash = b_hash
    doc.blockchain_timestamp = timestamp
    db.commit()
    db.refresh(doc)

    return ApproveResponse(
        document_id=doc.id,
        status=doc.status,
        blockchain_hash=b_hash,
        timestamp=timestamp.isoformat(),
        message=f"Document {doc_id} APPROVED. Hash: {b_hash}",
    )


@router.post("/{doc_id}/reject", response_model=ReviewResponse)
def reject_document(
    doc_id: int,
    officer_name: str = "Tahsildar / Revenue Officer",
    reason: str = "",
    db: Session = Depends(get_db),
):
    """
    Reject a document in EXTRACTED or NEEDS_REVIEW status.
    This is a terminal state; a new document must be uploaded for the same record.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")

    if not doc.can_transition_to("REJECTED"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject document in status {doc.status}. "
                   f"Allowed: {doc.valid_transitions().get(doc.status, [])}",
        )

    if not reason or len(reason.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="A typed reason of at least 5 characters is required for the audit trail.",
        )

    doc.reviewed_by = officer_name
    doc.reviewed_at = datetime.utcnow()
    doc.review_reason = reason.strip()
    doc.transition_to("REJECTED")
    db.commit()
    db.refresh(doc)

    return ReviewResponse(
        document_id=doc.id,
        status=doc.status,
        reviewed_by=doc.reviewed_by,
        reviewed_at=doc.reviewed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        corrections_applied=0,
        reason=doc.review_reason,
        message=f"Document {doc_id} REJECTED. Upload a new scan to restart.",
    )
