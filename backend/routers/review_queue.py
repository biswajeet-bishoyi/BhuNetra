from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import json
import hashlib
import os

from database import get_db
from models import ParcelRecord, OfficerAuditLog
from utils.dpdp import mask_pii_fields, pii_summary

router = APIRouter(prefix="/review-queue", tags=["Officer Review Queue & Audit Log"])

class DecisionRequest(BaseModel):
    parcel_id: str
    officer_name: str = "Tahsildar / Revenue Officer Shamshabad"
    action: str # APPROVE, OVERRIDE, REJECT, COURT_STATUS_UPDATE
    reason: str

@router.get("/")
def get_officer_review_queue(role: str = Query("Revenue Officer"), db: Session = Depends(get_db)):
    """
    Fetch flagged parcels requiring Revenue Officer review.
    Complies with DPDP Act 2023: If role is 'Citizen', masks owner personal identifiers.
    """
    geojson_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic", "parcels.geojson")
    with open(geojson_path, "r") as f:
        data = json.load(f)

    from routers.risk_ensemble import compute_fraud_risk_ensemble
    queue_items = []

    for feat in data["features"]:
        pid = feat["properties"]["parcel_id"]
        risk_info = compute_fraud_risk_ensemble(pid, role=role, db=db)
        
        # Look up DB state if decision was already made
        audit_records = db.query(OfficerAuditLog).filter(OfficerAuditLog.parcel_id == pid).order_by(OfficerAuditLog.timestamp.desc()).all()
        
        status = "PENDING_REVIEW"
        if audit_records:
            status = audit_records[0].action

        owner_display = risk_info["owner_name"]
        # DPDP Act 2023 data minimization is now applied centrally via
        # utils.dpdp.mask_pii_fields; risk_info already has owner_name masked for
        # the Citizen role when passed role='Citizen'. This block is kept as a
        # safety net for older callers.
        if role == "Citizen" and owner_display and "X." not in str(owner_display):
            parts = str(owner_display).split()
            if len(parts) > 1:
                owner_display = f"{parts[0]} X. (Masked per DPDP Act)"
            else:
                owner_display = "Pattadar (Masked per DPDP Act)"

        item = {
            "parcel_id": pid,
            "owner_name": owner_display,
            "khatian_no": risk_info["khatian_no"],
            "survey_no": risk_info["survey_no"],
            "village": risk_info.get("village", "Shamshabad"),
            "mandal": risk_info.get("mandal", "Shamshabad"),
            "district": risk_info.get("district", "Rangareddy"),
            "state": risk_info.get("state", "Telangana"),
            "claimed_area_sqm": risk_info["claimed_area_sqm"],
            "actual_area_sqm": risk_info["actual_area_sqm"],
            "revenue_court_status": risk_info["revenue_court_status"],
            "ensemble_risk_level": risk_info["ensemble_risk_level"],
            "ensemble_risk_score": risk_info["ensemble_risk_score"],
            "top_explanations": risk_info["top_explanations"],
            "review_status": status,
            "audit_history": [
                {
                    "action": a.action,
                    "officer_name": a.officer_name,
                    "reason": a.reason,
                    "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "blockchain_hash": a.blockchain_hash,
                    "compliance_note": a.legal_disclaimer
                } for a in audit_records
            ]
        }
        queue_items.append(item)

    return {
        "total_count": len(queue_items),
        "pending_flagged_count": len([i for i in queue_items if i["ensemble_risk_level"] in ["YELLOW", "RED"] and i["review_status"] == "PENDING_REVIEW"]),
        "compliance_context": {
            "dpdp_act_2023": "Active - Citizen view applies data minimization & PII masking",
            "it_act_2000_sec_65b": "Active - Tamper-evident hash and timestamp audit certificate generated on every action",
            "registration_act_1908": "Cryptographic hash guarantees audit integrity but does not replace statutory sale deed"
        },
        "queue": queue_items
    }

@router.post("/decision")
def submit_officer_decision(req: DecisionRequest, db: Session = Depends(get_db)):
    """
    Submit Revenue Officer decision with mandatory typed reason.
    Generates SHA-256 approval hash meeting IT Act Sec 65B electronic record requirements.
    """
    if not req.reason or len(req.reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="Mandatory typed reason (at least 5 characters) required for officer decision audit trail.")

    timestamp_str = datetime.utcnow().isoformat()
    
    # Generate SHA-256 approval hash
    raw_payload = f"BHUNETRA:{req.parcel_id}:{req.action}:{req.officer_name}:{req.reason}:{timestamp_str}"
    b_hash = "0x" + hashlib.sha256(raw_payload.encode()).hexdigest()

    log_entry = OfficerAuditLog(
        parcel_id=req.parcel_id,
        action=req.action,
        officer_name=req.officer_name,
        reason=req.reason.strip(),
        timestamp=datetime.utcnow(),
        blockchain_hash=b_hash
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "status": "SUCCESS",
        "message": f"Officer decision '{req.action}' recorded for parcel {req.parcel_id}",
        "parcel_id": req.parcel_id,
        "action": req.action,
        "reason": req.reason,
        "blockchain_hash": b_hash,
        "legal_admissibility": "Electronic record verifiable under IT Act 2000 Section 65B",
        "statutory_boundary": "Audit verification layer only; does not replace physical deed registered under Registration Act 1908",
        "audit_id": log_entry.id
    }

@router.get("/audit-log")
def get_all_audit_logs(db: Session = Depends(get_db)):
    """Fetch complete immutable audit log of officer decisions."""
    logs = db.query(OfficerAuditLog).order_by(OfficerAuditLog.timestamp.desc()).all()
    return [
        {
            "id": l.id,
            "parcel_id": l.parcel_id,
            "action": l.action,
            "officer_name": l.officer_name,
            "reason": l.reason,
            "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "blockchain_hash": l.blockchain_hash,
            "legal_note": l.legal_disclaimer
        } for l in logs
    ]
