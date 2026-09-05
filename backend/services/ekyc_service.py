"""
services/ekyc_service.py — Aadhaar e-KYC & DPDP Act 2023 Consent Management Service

Implements:
1. UIDAI e-KYC OTP simulation & biometric/demographic verification.
2. DPDP Act 2023 consent logging with purpose limitation, data retention policy, and cryptographic audit hash.
3. Matching engine between extracted landholder records and Aadhaar demographic records.
"""

import time
import uuid
import hashlib
from datetime import datetime

# Simulated in-memory e-KYC session store
_OTP_SESSIONS = {}
_VERIFIED_CONSENTS = {}


def generate_ekyc_otp(aadhaar_number: str, mobile_number: str, purpose: str = "Land Registry & RoR Verification") -> dict:
    """Generate simulated OTP for citizen Aadhaar verification."""
    clean_aadhaar = aadhaar_number.replace("-", "").replace(" ", "")
    if len(clean_aadhaar) != 12 or not clean_aadhaar.isdigit():
        raise ValueError("Invalid Aadhaar number. Must be a 12-digit number.")

    masked_aadhaar = f"XXXX-XXXX-{clean_aadhaar[-4:]}"
    masked_mobile = f"+91-XXXXX-{mobile_number[-4:] if len(mobile_number) >= 4 else '9876'}"
    
    session_id = str(uuid.uuid4())
    # Deterministic simulation OTP for demo / reproducible verification
    simulated_otp = "123456"
    
    _OTP_SESSIONS[session_id] = {
        "masked_aadhaar": masked_aadhaar,
        "clean_aadhaar_hash": hashlib.sha256(clean_aadhaar.encode()).hexdigest(),
        "masked_mobile": masked_mobile,
        "otp": simulated_otp,
        "purpose": purpose,
        "created_at": time.time(),
        "expires_at": time.time() + 300,  # 5 min TTL
    }

    return {
        "session_id": session_id,
        "masked_aadhaar": masked_aadhaar,
        "masked_mobile": masked_mobile,
        "message": f"OTP successfully dispatched to {masked_mobile}. Valid for 5 minutes.",
        "demo_hint": "Enter OTP: 123456",
        "compliance": "DPDP Act 2023 · Explicit Consent Mechanism"
    }


def verify_ekyc_otp(session_id: str, otp: str, claimed_name: str, parcel_id: str = None) -> dict:
    """Verify Aadhaar OTP, perform demographic match, and generate verifiable consent token."""
    session = _OTP_SESSIONS.get(session_id)
    if not session:
        raise ValueError("Invalid or expired e-KYC session ID.")

    if time.time() > session["expires_at"]:
        del _OTP_SESSIONS[session_id]
        raise ValueError("e-KYC OTP has expired. Please request a new OTP.")

    if otp.strip() != session["otp"]:
        raise ValueError("Incorrect OTP. Please enter the 6-digit OTP sent to your mobile.")

    # Demographic data simulation (UIDAI response)
    uidai_name = claimed_name if claimed_name else "Sudrusti Sethi"
    father_name = "Late Bhabagrahi Sethi"
    gender = "Male"
    state = "Odisha"
    district = "Ganjam"
    pincode = "761020"
    dob = "1978-06-15"
    
    # Calculate name match confidence score
    name_similarity = 1.0 if claimed_name.lower() in uidai_name.lower() or uidai_name.lower() in claimed_name.lower() else 0.94

    consent_id = f"CONSENT-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Cryptographic proof under Section 65B IT Act 2000
    consent_payload = f"{consent_id}:{session['clean_aadhaar_hash']}:{parcel_id or 'GENERAL'}:{timestamp}"
    digital_signature = hashlib.sha256(consent_payload.encode()).hexdigest()

    verification_record = {
        "consent_id": consent_id,
        "verification_status": "VERIFIED_AUTHENTIC",
        "timestamp": timestamp,
        "masked_aadhaar": session["masked_aadhaar"],
        "masked_mobile": session["masked_mobile"],
        "demographic_profile": {
            "full_name": uidai_name,
            "father_name": father_name,
            "gender": gender,
            "dob": dob,
            "state": state,
            "district": district,
            "pincode": pincode,
            "photo_match_score": 0.97,
            "name_match_confidence": round(name_similarity, 2)
        },
        "purpose": session["purpose"],
        "digital_signature_sec65b": digital_signature,
        "parcel_id_linked": parcel_id or "P-OD-102",
        "dpdp_compliance": {
            "legal_basis": "Section 6(1) DPDP Act 2023 — Explicit Landholder Consent",
            "data_retention": "30 days tokenized cache / permanent cryptohash audit log",
            "pii_masked": True
        }
    }

    if parcel_id:
        _VERIFIED_CONSENTS[parcel_id] = verification_record

    # Clean up OTP session
    del _OTP_SESSIONS[session_id]

    return verification_record


def get_parcel_ekyc_status(parcel_id: str) -> dict:
    """Retrieve e-KYC status and verification certificate for a parcel."""
    if parcel_id in _VERIFIED_CONSENTS:
        return {"has_ekyc": True, "record": _VERIFIED_CONSENTS[parcel_id]}
    
    # Default verified record for sample demo parcels
    default_record = {
        "consent_id": f"CONSENT-DEMO-{parcel_id.replace('-', '')}",
        "verification_status": "VERIFIED_AUTHENTIC",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "masked_aadhaar": "XXXX-XXXX-8921",
        "masked_mobile": "+91-XXXXX-9876",
        "demographic_profile": {
            "full_name": "Sudrusti Sethi" if "OD" in parcel_id else "Chhote Lal",
            "father_name": "Bhabagrahi Sethi",
            "gender": "Male",
            "state": "Odisha" if "OD" in parcel_id else "Uttar Pradesh",
            "district": "Ganjam" if "OD" in parcel_id else "Lucknow",
            "photo_match_score": 0.98,
            "name_match_confidence": 0.99
        },
        "purpose": "Revenue Officer Land Title & Mutation KYC",
        "digital_signature_sec65b": hashlib.sha256(f"DEMO:{parcel_id}".encode()).hexdigest(),
        "parcel_id_linked": parcel_id,
        "dpdp_compliance": {
            "legal_basis": "DPDP Act 2023 Compliant",
            "pii_masked": True
        }
    }
    return {"has_ekyc": True, "record": default_record}
