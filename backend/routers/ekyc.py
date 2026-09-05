"""
routers/ekyc.py — Endpoints for Aadhaar e-KYC & DPDP Act 2023 Consent Management
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services import ekyc_service

router = APIRouter(prefix="/ekyc", tags=["Aadhaar e-KYC & Consent"])


class GenerateOTPRequest(BaseModel):
    aadhaar_number: str
    mobile_number: str = "9876543210"
    purpose: str = "Land Record Digitalization & RoR Verification"


class VerifyOTPRequest(BaseModel):
    session_id: str
    otp: str
    claimed_name: str
    parcel_id: str | None = None


@router.post("/generate-otp")
def generate_otp(req: GenerateOTPRequest):
    """Initiate simulated UIDAI Aadhaar e-KYC OTP dispatch."""
    try:
        res = ekyc_service.generate_ekyc_otp(
            aadhaar_number=req.aadhaar_number,
            mobile_number=req.mobile_number,
            purpose=req.purpose
        )
        return {"success": True, "data": res}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/verify-otp")
def verify_otp(req: VerifyOTPRequest):
    """Verify Aadhaar OTP, perform demographic match, and register DPDP consent."""
    try:
        res = ekyc_service.verify_ekyc_otp(
            session_id=req.session_id,
            otp=req.otp,
            claimed_name=req.claimed_name,
            parcel_id=req.parcel_id
        )
        return {"success": True, "data": res}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/status/{parcel_id}")
def get_ekyc_status(parcel_id: str):
    """Retrieve e-KYC verification status and certificate for a parcel."""
    res = ekyc_service.get_parcel_ekyc_status(parcel_id)
    return {"success": True, "data": res}
