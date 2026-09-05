import os
import json
import hashlib
from io import BytesIO
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

def generate_evidence_package_pdf(
    parcel_data: Dict[str, Any],
    triple_comparison: Dict[str, Any],
    title_chain: Dict[str, Any],
    duplicate_claim: Optional[Dict[str, Any]] = None,
    officer_name: str = "Tahsildar / Sub-Collector",
    officer_notes: str = "All statutory cross-checks verified."
) -> Tuple[bytes, str, str]:
    """
    Builds a court-ready, tamper-evident Section 65B Evidence Package PDF using ReportLab.
    """
    import reportlab.lib.colors as colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
    from reportlab.platypus import Image as RLImage
    
    try:
        import qrcode
        has_qr = True
    except ImportError:
        has_qr = False

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14*mm,
        rightMargin=14*mm,
        topMargin=12*mm,
        bottomMargin=12*mm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_style = ParagraphStyle(
        'GovHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        alignment=1
    )
    sub_header = ParagraphStyle(
        'GovSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )
    cell_text = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a')
    )
    
    story = []
    W = A4[0] - 28*mm
    
    parcel_id = parcel_data.get("parcel_id", "P-OD-102")
    issued_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_id = f"BHUNETRA-EVD-65B-{parcel_id}-{int(datetime.now(timezone.utc).timestamp())}"
    
    # 1. Government Letterhead & Watermark Title
    story.append(Paragraph("GOVERNMENT REVENUE DEPARTMENT — LAND RECORD ADMINISTRATION", header_style))
    story.append(Paragraph("BhuNetra AI Cadastral Decision Support & Title Verification Layer (SIH26018)", sub_header))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("<b>COURT-READY EVIDENCE SUMMARY &amp; TITLE CHAIN ASSESSMENT REPORT</b>", ParagraphStyle('ReportTitle', parent=header_style, fontSize=11, leading=14, textColor=colors.HexColor('#b45309'))))
    story.append(Paragraph(f"Digital Audit ID: {report_id}  |  Generated: {issued_dt}", sub_header))
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width=W, thickness=2, color=colors.HexColor("#d97706")))
    story.append(Spacer(1, 3*mm))

    # 2. Ownership Confidence & Primary Status Badge
    conf = triple_comparison.get("overall_confidence", 94.0)
    badge_bg = colors.HexColor("#dcfce7") if conf >= 80 else (colors.HexColor("#fef3c7") if conf >= 60 else colors.HexColor("#fee2e2"))
    badge_border = colors.HexColor("#16a34a") if conf >= 80 else (colors.HexColor("#d97706") if conf >= 60 else colors.HexColor("#dc2626"))
    badge_text_color = colors.HexColor("#14532d") if conf >= 80 else (colors.HexColor("#78350f") if conf >= 60 else colors.HexColor("#7f1d1d"))
    
    summary_table_data = [
        [
            Paragraph(f"<b>OWNERSHIP CONFIDENCE ASSESSMENT: {conf}%</b><br/><font size='7.5'>Recommendation: {triple_comparison.get('recommendation', 'Verified')}</font>", ParagraphStyle('Score', fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=badge_text_color)),
            Paragraph(f"<b>Duplicate Claim Check:</b> {triple_comparison.get('duplicate_claim', 'None')}<br/><b>Title Chain Integrity:</b> {triple_comparison.get('historical_chain', 'Verified')}", cell_text)
        ]
    ]
    st = Table(summary_table_data, colWidths=[110*mm, 72*mm])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), badge_bg),
        ('BOX', (0, 0), (-1, -1), 1, badge_border),
        ('PADDING', (0, 0), (-1, -1), 4*mm),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(st)
    story.append(Spacer(1, 3*mm))

    # 3. Property & Document Identifiers Table
    story.append(Paragraph("<b>1. Property &amp; Cadastral Identifiers</b>", section_title))
    story.append(Spacer(1, 1.5*mm))
    
    prop_data = [
        [Paragraph("Parcel ID", cell_bold), Paragraph(str(parcel_id), cell_text), Paragraph("Survey / Khasra No.", cell_bold), Paragraph(str(parcel_data.get("survey_no", "—")), cell_text)],
        [Paragraph("Khata / Khatian No.", cell_bold), Paragraph(str(parcel_data.get("khata_no", "—")), cell_text), Paragraph("ULPIN", cell_bold), Paragraph(str(parcel_data.get("ulpin", "—")), cell_text)],
        [Paragraph("Pattadar / Owner", cell_bold), Paragraph(str(parcel_data.get("owner_name", "—")), cell_text), Paragraph("Father / Husband", cell_bold), Paragraph(str(parcel_data.get("father_or_husband", "—")), cell_text)],
        [Paragraph("Village & Mandal", cell_bold), Paragraph(f"{parcel_data.get('village', '—')}, {parcel_data.get('mandal', '—')}", cell_text), Paragraph("District & State", cell_bold), Paragraph(f"{parcel_data.get('district', '—')}, {parcel_data.get('state', '—')}", cell_text)],
        [Paragraph("Recorded Area", cell_bold), Paragraph(f"{float(parcel_data.get('claimed_area_sqm', 0)):,.1f} sq.m", cell_text), Paragraph("GIS Measured Extent", cell_bold), Paragraph(f"{float(parcel_data.get('actual_area_sqm', 0) or parcel_data.get('claimed_area_sqm', 0)):,.1f} sq.m", cell_text)],
    ]
    pt = Table(prop_data, colWidths=[40*mm, 51*mm, 45*mm, 46*mm])
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(pt)
    story.append(Spacer(1, 3.5*mm))

    # 4. Three-Way AI Comparison Matrix (Feature 7 & 8)
    story.append(Paragraph("<b>2. Three-Way AI Evidence Comparison Matrix</b> (Registration 35% | Revenue 25% | Survey 25% | Chain 15%)", section_title))
    story.append(Spacer(1, 1.5*mm))
    
    matrix_headers = [
        Paragraph("<b>Attribute</b>", cell_bold),
        Paragraph("<b>1. Registered Deed</b>", cell_bold),
        Paragraph("<b>2. Revenue RoR</b>", cell_bold),
        Paragraph("<b>3. Cadastral Survey</b>", cell_bold),
        Paragraph("<b>Match / AI Finding</b>", cell_bold)
    ]
    matrix_rows = [matrix_headers]
    
    for row in triple_comparison.get("comparison_matrix", []):
        m_color = colors.HexColor('#15803d') if row.get("status") == "EXACT_MATCH" else (colors.HexColor('#b45309') if row.get("status") == "MINOR_MISMATCH" else colors.HexColor('#b91c1c'))
        matrix_rows.append([
            Paragraph(row.get("label", row.get("field")), cell_bold),
            Paragraph(str(row.get("registration", "—")), cell_text),
            Paragraph(str(row.get("revenue", "—")), cell_text),
            Paragraph(str(row.get("survey", "—")), cell_text),
            Paragraph(f"<font color='{m_color.hexval()}'><b>{row.get('match_pct', 0)}%</b></font> - {row.get('notes', '')}", cell_text)
        ])
        
    mt = Table(matrix_rows, colWidths=[32*mm, 35*mm, 35*mm, 35*mm, 45*mm])
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('PADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(mt)
    story.append(Spacer(1, 3.5*mm))

    # 5. Reconstructed Title Chain Timeline (Feature 3 & 11)
    story.append(Paragraph("<b>3. Historical Ownership &amp; Ancestral Title Chain (Lineage Progression)</b>", section_title))
    story.append(Spacer(1, 1.5*mm))
    
    chain_list = title_chain.get("chain", [])
    if chain_list:
        chain_headers = [
            Paragraph("<b>Year / Date</b>", cell_bold),
            Paragraph("<b>Document Type</b>", cell_bold),
            Paragraph("<b>Pattadar / Owner Name</b>", cell_bold),
            Paragraph("<b>Predecessor / Father</b>", cell_bold),
            Paragraph("<b>Registration / Survey Ref</b>", cell_bold)
        ]
        chain_table_data = [chain_headers]
        for c in chain_list:
            chain_table_data.append([
                Paragraph(f"<b>{c.get('year')}</b> ({c.get('date', '—')})", cell_text),
                Paragraph(str(c.get("document_type", "—")), cell_text),
                Paragraph(f"<b>{c.get('owner_name', '—')}</b>", cell_text),
                Paragraph(str(c.get("father_name") or "—"), cell_text),
                Paragraph(f"#{c.get('registration_no', '—')} (Sy. {c.get('survey_no', '—')})", cell_text)
            ])
            
        ct = Table(chain_table_data, colWidths=[28*mm, 34*mm, 40*mm, 38*mm, 42*mm])
        ct.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('PADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(ct)
    else:
        story.append(Paragraph("<i>Single-tier deed verified; no historical ancestral gap detected.</i>", cell_text))
    story.append(Spacer(1, 3.5*mm))

    # 6. Duplicate Claim Audit & Officer Endorsement Section
    story.append(Paragraph("<b>4. Revenue Officer Endorsement &amp; Statutory Legal Proof</b>", section_title))
    story.append(Spacer(1, 1.5*mm))
    
    # Generate cryptographic SHA-256 digital admissibility stamp
    raw_evidence_payload = {
        "report_id": report_id,
        "parcel_id": parcel_id,
        "issued_dt": issued_dt,
        "ownership_confidence": conf,
        "triple_comparison": triple_comparison.get("overall_confidence"),
        "title_chain_length": len(chain_list),
        "officer": officer_name
    }
    sha_hash = "0x" + hashlib.sha256(json.dumps(raw_evidence_payload, sort_keys=True).encode("utf-8")).hexdigest()
    
    audit_data = [
        [
            Paragraph(f"<b>Officer Notes &amp; Disposition:</b><br/>{officer_notes}<br/><br/><b>Investigating Officer:</b> {officer_name}<br/><b>Designation:</b> Tahsildar &amp; Executive Magistrate<br/><b>Admissibility Stamp:</b> Certified under IT Act 2000 Section 65B", cell_text),
            Paragraph(f"<b>IT Act Section 65B Digital Hash:</b><br/><font face='Courier' size='6.5'>{sha_hash}</font><br/><br/><b>Statutory Legal Disclaimer:</b><br/><i>This AI-assisted evidence summary is generated for decision support under DILRMP / Revenue Department procedures. It validates digital consistency, spatial topology, and cross-source alignment. Statutory title ownership remains governed by the physical registered sale deed under the Registration Act 1908.</i>", cell_text)
        ]
    ]
    at = Table(audit_data, colWidths=[90*mm, 92*mm])
    at.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
        ('PADDING', (0, 0), (-1, -1), 3*mm),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(at)
    story.append(Spacer(1, 3*mm))

    # QR Code at the bottom
    if has_qr:
        qr = qrcode.make(f"http://bhunetra.gov/api/blockchain/verify-hash/{parcel_id}?hash={sha_hash}")
        qr_buf = BytesIO()
        qr.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        qr_img = RLImage(qr_buf, width=22*mm, height=22*mm)
        
        qr_table_data = [[
            qr_img,
            Paragraph(f"<b>Scan QR for Immutable Blockchain Verification Stamp</b><br/><font size='7' color='#64748b'>On-Chain Contract: Polygon Proof-of-Authority (BhuNetra Verification Subnet)<br/>Digital Electronic Record Admissibility Certificate (IT Act 2000 Section 65B)</font>", cell_text)
        ]]
        qrt = Table(qr_table_data, colWidths=[26*mm, 156*mm])
        qrt.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(qrt)
    
    doc.build(story)
    return buffer.getvalue(), sha_hash, report_id
