"""
routers/forensics.py — Endpoints for Document Tamper Detection, EXIF Forensics & Digital Watermarking
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Document
from services import forensics_service

router = APIRouter(prefix="/documents", tags=["Document Forensics & Tamper Detection"])


def _get_document_bytes(doc: Document) -> tuple[bytes, str]:
    """Retrieve raw image bytes for a document."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    uploads_dir = data_dir / "uploads"
    synthetic_dir = data_dir / "synthetic" / "registry_scans"

    scan_path = uploads_dir / f"{doc.file_hash}_{doc.source_filename}"
    if not scan_path.exists() and uploads_dir.exists():
        hash_matches = list(uploads_dir.glob(f"{doc.file_hash}*"))
        if hash_matches:
            scan_path = hash_matches[0]
    if not scan_path.exists():
        scan_path = synthetic_dir / doc.source_filename
    if not scan_path.exists() and synthetic_dir.exists():
        base_name = doc.source_filename.replace("odisha_bhubaneswar_", "").replace("delhi_", "")
        matches = list(synthetic_dir.glob(f"*{base_name}*")) or list(synthetic_dir.glob(f"*{doc.source_filename}*"))
        if matches:
            scan_path = matches[0]

    if not scan_path.exists():
        sample_scans = list(synthetic_dir.glob("*.png")) if synthetic_dir.exists() else []
        if sample_scans:
            scan_path = sample_scans[0]
        else:
            raise HTTPException(status_code=404, detail="Scan file not found on disk")

    raw_bytes = scan_path.read_bytes()

    # If PDF, rasterize first page to PNG bytes for image analysis
    if raw_bytes.startswith(b"%PDF") or doc.source_filename.lower().endswith(".pdf"):
        try:
            import io
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(raw_bytes)
            page = pdf[0]
            pil_img = page.render(scale=2.0).to_pil().convert("RGB")
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            return buf.getvalue(), doc.source_filename
        except Exception:
            pass

    return raw_bytes, doc.source_filename


@router.post("/authenticate/{doc_id}")
def authenticate_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Run comprehensive forensic analysis on a document:
    - EXIF metadata & software signature inspection
    - Error Level Analysis (ELA)
    - Invisible LSB chain-of-custody watermark check
    - Composite tamper risk score
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    image_bytes, filename = _get_document_bytes(doc)
    report = forensics_service.run_full_forensic_analysis(
        doc_id=doc.id,
        image_bytes=image_bytes,
        filename=filename,
        parcel_id_hint=doc.parcel_id_hint
    )
    return {"success": True, "data": report}


@router.get("/authenticate/{doc_id}/ela-image")
def get_ela_heatmap_image(doc_id: int, db: Session = Depends(get_db)):
    """Stream the Error Level Analysis (ELA) difference heatmap PNG."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    image_bytes, _ = _get_document_bytes(doc)
    ela_bytes = forensics_service.generate_ela_heatmap(image_bytes)
    return Response(content=ela_bytes, media_type="image/png")


@router.post("/{doc_id}/watermark")
def watermark_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Invisibly watermark document with cryptographic BhuNetra chain-of-custody stamp.
    Embeds parcel ID and SHA-256 hash into the image pixels.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    image_bytes, filename = _get_document_bytes(doc)
    payload = f"BHUNETRA:DOC_{doc.id}:PARCEL_{doc.parcel_id_hint or 'P-101'}:{doc.file_hash[:16]}"
    watermarked_bytes = forensics_service.embed_invisible_watermark(image_bytes, payload)

    # Persist watermarked bytes
    data_dir = Path(__file__).parent.parent.parent / "data"
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    out_path = uploads_dir / f"{doc.file_hash}_{doc.source_filename}"
    out_path.write_bytes(watermarked_bytes)

    return {
        "success": True,
        "message": "Chain-of-custody invisible watermark embedded successfully.",
        "payload": payload,
        "document_id": doc.id
    }
