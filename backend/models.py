import os
import sys

try:
    from database import Base
except ImportError:
    from backend.database import Base

from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime
from datetime import datetime

class ParcelRecord(Base):
    __tablename__ = "parcels"

    parcel_id = Column(String, primary_key=True, index=True)
    survey_no = Column(String)
    khatian_no = Column(String)
    ulpin = Column(String)
    owner_name = Column(String)
    village = Column(String)
    mandal = Column(String, default="Shamshabad")
    district = Column(String, default="Rangareddy")
    state = Column(String, default="Telangana")
    claimed_area_sqm = Column(Float)
    actual_area_sqm = Column(Float)
    land_use_claim = Column(String)
    revenue_court_status = Column(String, default="Clean")
    
    # Plain text geometry storage (Zero C-extension / SpatiaLite dependency)
    geometry_wkt = Column(Text, default="")
    geometry_geojson = Column(Text, default="")
    
    # Engine risk outputs
    gis_risk_score = Column(Float, default=0.0)
    gis_anomaly_flag = Column(Boolean, default=False)
    gis_explanation = Column(Text, default="")

    ownership_risk_score = Column(Float, default=0.0)
    ownership_anomaly_flag = Column(Boolean, default=False)
    ownership_explanation = Column(Text, default="")

    satellite_risk_score = Column(Float, default=0.0)
    satellite_mismatch_flag = Column(Boolean, default=False)
    satellite_explanation = Column(Text, default="")

    ocr_verification_status = Column(String, default="UNVERIFIED")

    ensemble_risk_level = Column(String, default="GREEN") # GREEN, YELLOW, RED
    ensemble_risk_score = Column(Float, default=0.0) # 0 to 100
    top_explanations = Column(Text, default="[]") # JSON list of explanation strings

    review_status = Column(String, default="PENDING_REVIEW") # PENDING_REVIEW, APPROVED, REJECTED, OVERRIDDEN
    assigned_officer = Column(String, default="Tahsildar / Revenue Officer Shamshabad")
    blockchain_hash = Column(String, default="")
    blockchain_tx_id = Column(String, default="")


class OfficerAuditLog(Base):
    """
    Audit log designed to comply with IT Act 2000 Section 65B electronic record
    admissibility criteria and DPDP Act 2023 accountability principles.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String, index=True)
    action = Column(String) # APPROVE, OVERRIDE, REJECT, COURT_STATUS_UPDATE
    officer_name = Column(String)
    reason = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    blockchain_hash = Column(String, default="")
    legal_disclaimer = Column(
        Text,
        default="Hash verified for digital audit integrity under IT Act 2000 Sec 65B; does not replace statutory Registered Sale Deed under Registration Act 1908."
    )


class OwnershipTransfer(Base):
    __tablename__ = "ownership_transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String, index=True)
    owner_name = Column(String)
    transfer_date = Column(String)
    transfer_type = Column(String)
    deed_number = Column(String)
    price_inr = Column(Float)
    flag_rapid_resale = Column(Boolean, default=False)
