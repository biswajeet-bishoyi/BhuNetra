import hashlib
import json
import os
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from routers.risk_ensemble import compute_fraud_risk_ensemble
from utils.dpdp import mask_pii_fields, pii_summary

router = APIRouter(prefix="/certificate", tags=["BhuNetra Land Health Card"])

# Lazy-import PDF libraries so the app boots even without them
def _make_pdf(cert_payload: dict, cert_hash: str, cert_id: str, timestamp: str, role: str) -> bytes:
    import reportlab.lib.colors as colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.platypus import Image as RLImage
    try:
        import qrcode
        has_qr = True
    except ImportError:
        has_qr = False

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    story = []

    W = A4[0] - 30*mm

    # ---- Header ----
    story.append(Paragraph("Government of Telangana — Revenue Department", styles["Normal"]))
    story.append(Paragraph("<b>BhuNetra AI — Land Health &amp; Title Admissibility Certificate</b>",
                            styles["Title"]))
    story.append(Paragraph(f"Certificate ID: {cert_id}", styles["Normal"]))
    story.append(HRFlowable(width=W, thickness=2, color=colors.HexColor("#f59e0b")))
    story.append(Spacer(1, 6*mm))

    # ---- Risk level banner ----
    level = cert_payload.get("ensemble_risk_level", "GREEN")
    level_color = {"RED": colors.HexColor("#dc2626"), "YELLOW": colors.HexColor("#d97706"),
                   "GREEN": colors.HexColor("#16a34a")}.get(level, colors.gray)
    story.append(Paragraph(
        f"<b>Risk Level: {level}</b> — Ensemble Score: {cert_payload.get('ensemble_risk_score', 0)} / 100",
        styles["Normal"]))

    # ---- Parcel details ----
    details = [
        ["Parcel / Survey No", f"{cert_payload.get('parcel_id')} / Sy. {cert_payload.get('survey_no')}"],
        ["Recorded Pattadar", cert_payload.get("owner_name", "—")],
        ["Village & Mandal", f"{cert_payload.get('village')}, {cert_payload.get('mandal')}"],
        ["District & State", f"{cert_payload.get('district')}, {cert_payload.get('state')}"],
        ["Khatian No", cert_payload.get("khatian_no", "—")],
        ["ULPIN", cert_payload.get("ulpin", "—")],
        ["Claimed Extent", f"{cert_payload.get('claimed_area_sqm', 0):.2f} sqm"],
        ["Actual GIS Extent", f"{cert_payload.get('actual_area_sqm', 0):.2f} sqm"],
        ["Land Use Claim", cert_payload.get("land_use_claim", "—")],
        ["Revenue Court Status", cert_payload.get("revenue_court_status", "—")],
    ]
    t = Table(details, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    # ---- Engine score matrix ----
    scores = cert_payload.get("engine_scores", {})
    score_data = [
        ["Engine", "Score"],
        ["GIS Topology (E2)", f"{scores.get('gis_validation', 0):.1f}"],
        ["Ownership Intelligence (E3)", f"{scores.get('ownership_intelligence', 0):.1f}"],
        ["Satellite Verification (E4)", f"{scores.get('satellite_verification', 0):.1f}"],
        ["Registry OCR (E1)", f"{scores.get('registry_ocr', 0):.1f}"],
    ]
    st = Table(score_data, colWidths=[80*mm, 95*mm])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(st)
    story.append(Spacer(1, 4*mm))

    # ---- SHA-256 Hash ----
    story.append(Paragraph("<b>IT Act 2000 Section 65B Digital Admissibility Hash</b>", styles["Normal"]))
    story.append(Paragraph(f"<font face='Courier' size='8'>{cert_hash}</font>", styles["Normal"]))
    story.append(Spacer(1, 4*mm))

    # ---- QR Code ----
    if has_qr:
        qr = qrcode.make(f"http://bhunetra.gov/api/blockchain/verify-hash/{cert_payload.get('parcel_id')}")
        qr_buf = BytesIO()
        qr.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        qr_img = RLImage(qr_buf, width=30*mm, height=30*mm)
        story.append(qr_img)
        story.append(Paragraph("<i>Scan to verify hash on-chain</i>", styles["Normal"]))
        story.append(Spacer(1, 4*mm))

    # ---- Legal disclaimer ----
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#94a3b8")))
    story.append(Paragraph(
        "<i>This certificate is issued under the authority of the Tahsildar &amp; Executive "
        "Magistrate, Shamshabad Mandal, Rangareddy District, Telangana. The SHA-256 hash "
        "verifies digital audit integrity under IT Act 2000 Section 65B. This certificate "
        "does not replace the physical registered sale deed under the Registration Act 1908. "
        "Statutory ownership remains with the registered deed.</i>",
        styles["Normal"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f"<i>Issued: {timestamp}</i>", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()


@router.get("/{parcel_id}/export-pdf")
def export_land_health_pdf(
    parcel_id: str,
    role: str = Query("Revenue Officer"),
    db: Session = Depends(get_db),
):
    """
    Generate a printable PDF Land Health Certificate using reportlab.

    Includes:
    - Government letterhead (Government of Telangana — Revenue Department)
    - Parcel details, risk level, engine scores
    - DPDP-masked owner for Citizen role
    - SHA-256 hash (IT Act 2000 Sec 65B)
    - QR code linking to /api/blockchain/verify-hash/{parcel_id}
    - Legal disclaimer under Registration Act 1908
    """
    risk_data = compute_fraud_risk_ensemble(parcel_id, role=role, db=db)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    cert_id = f"BHUNETRA-CERT-{parcel_id}-{int(datetime.now(timezone.utc).timestamp())}"

    import json
    cert_payload = {
        "system": "BhuNetra AI — Ministry of Rural Development (SIH26018)",
        "parcel_id": parcel_id,
        "ulpin": risk_data.get("ulpin", f"TS-RR-{parcel_id}"),
        "survey_no": risk_data.get("survey_no"),
        "khatian_no": risk_data.get("khatian_no"),
        "village": risk_data.get("village", "Shamshabad"),
        "mandal": risk_data.get("mandal", "Shamshabad"),
        "district": risk_data.get("district", "Rangareddy"),
        "state": risk_data.get("state", "Telangana"),
        "owner_name": risk_data.get("owner_name"),
        "claimed_area_sqm": risk_data.get("claimed_area_sqm"),
        "actual_area_sqm": risk_data.get("actual_area_sqm"),
        "land_use_claim": risk_data.get("land_use_claim"),
        "revenue_court_status": risk_data.get("revenue_court_status"),
        "ensemble_risk_level": risk_data.get("ensemble_risk_level"),
        "ensemble_risk_score": risk_data.get("ensemble_risk_score"),
        "engine_scores": risk_data.get("engine_scores"),
        "top_explanations": risk_data.get("top_explanations"),
    }
    raw_bytes = json.dumps(cert_payload, sort_keys=True).encode("utf-8")
    cert_hash = "0x" + hashlib.sha256(raw_bytes).hexdigest()

    try:
        pdf_bytes = _make_pdf(cert_payload, cert_hash, cert_id, timestamp, role)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {exc}. Ensure reportlab and qrcode[pil] are installed."
        ) from exc

    filename = f"BhuNetra-Certificate-{parcel_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get("/{parcel_id}")
def generate_land_health_certificate(
    parcel_id: str,
    role: str = Query("Revenue Officer", description="Requesting role for DPDP masking"),
    db: Session = Depends(get_db),
):
    """
    Generate an official, tamper-evident Land Health & Title Admissibility Certificate.
    Includes deterministic multi-engine risk breakdown, IT Act 2000 Section 65B electronic
    admissibility hash, DPDP Act compliance note, and statutory deed references.
    """
    risk_data = compute_fraud_risk_ensemble(parcel_id, role=role, db=db)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Generate cryptographic certificate payload for SHA-256 digital admissibility
    cert_payload = {
        "system": "BhuNetra AI — Ministry of Rural Development (SIH26018)",
        "parcel_id": parcel_id,
        "ulpin": risk_data.get("ulpin", f"TS-RR-{parcel_id}"),
        "survey_no": risk_data.get("survey_no"),
        "khatian_no": risk_data.get("khatian_no"),
        "village": risk_data.get("village", "Shamshabad"),
        "mandal": risk_data.get("mandal", "Shamshabad"),
        "district": risk_data.get("district", "Rangareddy"),
        "state": risk_data.get("state", "Telangana"),
        "owner_name": risk_data.get("owner_name"),
        "claimed_area_sqm": risk_data.get("claimed_area_sqm"),
        "actual_area_sqm": risk_data.get("actual_area_sqm"),
        "revenue_court_status": risk_data.get("revenue_court_status"),
        "ensemble_risk_level": risk_data.get("ensemble_risk_level"),
        "ensemble_risk_score": risk_data.get("ensemble_risk_score"),
        "engine_scores": risk_data.get("engine_scores"),
        "top_explanations": risk_data.get("top_explanations"),
        "issued_at_utc": timestamp
    }
    
    raw_bytes = json.dumps(cert_payload, sort_keys=True).encode("utf-8")
    cert_hash = f"0x{hashlib.sha256(raw_bytes).hexdigest()}"

    return {
        "certificate_id": f"BHUNETRA-CERT-{parcel_id}-{int(datetime.now(timezone.utc).timestamp())}",
        "issued_timestamp": timestamp,
        "digital_admissibility_hash": f"0x{cert_hash}",
        "statutory_authority": "Tahsildar & Executive Magistrate, Shamshabad Mandal, Rangareddy",
        "legal_clauses": {
            "it_act_2000_sec_65b": "Certified as an authentic computer-generated digital audit record under Section 65B of the Indian Evidence Act / IT Act 2000.",
            "registration_act_1908": "This certificate validates algorithmic digital consistency and spatial topology. Statutory ownership remains governed by the registered title deed.",
            "dpdp_act_2023": "Issued with consent-based data minimization in compliance with Digital Personal Data Protection Act 2023."
        },
        "payload": cert_payload,
        "dpdp_context": pii_summary(cert_payload, role)
    }
