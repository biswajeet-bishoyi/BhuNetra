import hashlib
import json
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from routers.risk_ensemble import compute_fraud_risk_ensemble
from utils.dpdp import mask_pii_fields, pii_summary

router = APIRouter(prefix="/certificate", tags=["BhuNetra Land Health Card"])

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
    cert_hash = hashlib.sha256(raw_bytes).hexdigest()
    
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
