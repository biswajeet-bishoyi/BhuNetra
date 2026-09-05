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


class Document(Base):
    """
    Persisted document record tracking the full UPLOADED → EXTRACTED → NEEDS_REVIEW →
    VERIFIED → APPROVED / REJECTED lifecycle.

    All state transitions are validated in code; the DB stores only the current state
    so the latest transition determines where the document is.
    """
    __tablename__ = "documents"

    # Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=True)       # SHA-256 of the uploaded bytes

    # Extraction inputs / outputs
    status = Column(String, default="UPLOADED", index=True)   # current lifecycle state
    parcel_id = Column(String, nullable=True, index=True)      # may be null until extracted
    parcel_id_hint = Column(String, nullable=True)             # hint from OCR (deed/ULPIN)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)

    # Engine 1 extraction result (JSON)
    extraction_result = Column(Text, default="{}")    # full ExtractionResult.to_dict()
    extracted_fields = Column(Text, default="{}")     # {key: value} for fast lookups
    extraction_engine_tag = Column(String, default="")
    extraction_passes = Column(Integer, default=0)
    extraction_confidence = Column(Float, default=0.0)
    low_confidence_fields = Column(Text, default="[]")  # JSON list of field keys
    extraction_timing_ms = Column(Float, default=0.0)
    extraction_timestamp = Column(DateTime, nullable=True)

    # Ownership chain metadata derived during extraction
    ownership_chain_json = Column(Text, default="[]")   # JSON list of {owner, date, type}

    # Review & officer actions
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_reason = Column(Text, nullable=True)
    officer_corrections = Column(Text, default="{}")   # {field: corrected_value}

    # Blockchain / legal
    blockchain_hash = Column(String, nullable=True)
    blockchain_timestamp = Column(DateTime, nullable=True)

    @staticmethod
    def valid_transitions() -> dict:
        """Return the valid next states for each current state."""
        return {
            "UPLOADED":       {"EXTRACTED", "NEEDS_REVIEW"},
            "EXTRACTED":      {"NEEDS_REVIEW", "VERIFIED"},
            "NEEDS_REVIEW":   {"VERIFIED", "REJECTED"},
            "VERIFIED":       {"APPROVED"},
            "REJECTED":       set(),        # terminal; start fresh
            "APPROVED":       set(),        # terminal
        }

    def can_transition_to(self, target: str) -> bool:
        """Return True if a state transition is legally valid."""
        return target in self.valid_transitions().get(self.status, set())

    def transition_to(self, target: str) -> None:
        """Move to a new state; raises ValueError on invalid transition."""
        if not self.can_transition_to(target):
            raise ValueError(
                f"Invalid document transition: {self.status} -> {target}. "
                f"Allowed: {self.valid_transitions().get(self.status, set())}"
            )
        self.status = target

    def __init__(self, **kwargs):
        # SQLAlchemy's Column(default=...) only fires on INSERT, not on Python
        # construction. Mirror the column defaults so an in-memory Document() has
        # the same initial state that the DB will see on commit.
        super().__init__(**kwargs)
        if self.status is None:
            self.status = "UPLOADED"
        if self.extraction_result is None:
            self.extraction_result = "{}"
        if self.extracted_fields is None:
            self.extracted_fields = "{}"
        if self.extraction_engine_tag is None:
            self.extraction_engine_tag = ""
        if self.extraction_passes is None:
            self.extraction_passes = 0
        if self.extraction_confidence is None:
            self.extraction_confidence = 0.0
        if self.low_confidence_fields is None:
            self.low_confidence_fields = "[]"
        if self.extraction_timing_ms is None:
            self.extraction_timing_ms = 0.0
        if self.ownership_chain_json is None:
            self.ownership_chain_json = "[]"
        if self.officer_corrections is None:
            self.officer_corrections = "{}"
        if self.upload_timestamp is None:
            self.upload_timestamp = datetime.utcnow()


class MutationRequest(Base):
    """
    Represents a pending parcel mutation request submitted by a Revenue Officer.
    The new geometry is stored as GeoJSON text so no spatialite extension is needed.
    """
    __tablename__ = "mutation_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String, index=True, nullable=True)  # may be null for new parcels
    requested_by = Column(String)
    reason = Column(Text)
    geometry_geojson = Column(Text)  # GeoJSON Polygon of the proposed new boundary
    status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED, SUPERSEDED
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)


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


class TitleChainDocument(Base):
    """
    Stores individual deeds / mutation records in a property's title chain
    (e.g., Grandfather Sale Deed -> Father Mutation -> Current Registration).
    """
    __tablename__ = "title_chain_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String, index=True)
    parent_document_id = Column(Integer, nullable=True) # Links to predecessor in lineage
    owner_name = Column(String, nullable=False)
    father_name = Column(String, nullable=True)
    document_type = Column(String, default="Sale Deed") # Sale Deed, Mutation Order, Patta, Gift Deed, Partition
    deed_date = Column(String, nullable=True) # YYYY-MM-DD
    deed_year = Column(Integer, nullable=True)
    registration_no = Column(String, nullable=True)
    survey_no = Column(String, nullable=True)
    khata_no = Column(String, nullable=True)
    village = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    area_sqm = Column(Float, default=0.0)
    source_filename = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    is_ancestral = Column(Boolean, default=False)
    order_index = Column(Integer, default=0) # Chronological position
    extracted_fields_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class OwnershipRepository(Base):
    """
    Permanent Property Repository: Retains verified historical property identity
    and lineage references across all uploads, never overwriting past versions.
    """
    __tablename__ = "ownership_repository"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String, unique=True, index=True)
    survey_no = Column(String, index=True)
    khata_no = Column(String, index=True)
    village = Column(String, index=True)
    mandal = Column(String, default="")
    district = Column(String, default="")
    state = Column(String, default="")
    ulpin = Column(String, nullable=True)
    latest_verified_owner = Column(String, nullable=False)
    latest_registration_no = Column(String, nullable=True)
    recorded_area_sqm = Column(Float, default=0.0)
    historical_owner_count = Column(Integer, default=1)
    status = Column(String, default="VERIFIED") # VERIFIED, DISPUTED, UNDER_REVIEW
    last_verified_at = Column(DateTime, default=datetime.utcnow)
    title_chain_summary_json = Column(Text, default="[]")


class DuplicateClaim(Base):
    """
    Automated conflict detection record when a new claimant uploads a deed
    for an existing parcel already in the repository with a different owner.
    """
    __tablename__ = "duplicate_claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_id = Column(String, index=True)
    survey_no = Column(String, index=True)
    khata_no = Column(String, index=True)
    village = Column(String, index=True)
    district = Column(String, default="")
    state = Column(String, default="")
    existing_owner = Column(String, nullable=False)
    existing_registration_no = Column(String, nullable=True)
    new_claimant = Column(String, nullable=False)
    new_registration_no = Column(String, nullable=True)
    conflict_score = Column(Float, default=0.0) # 0 to 100%
    conflict_reasons_json = Column(Text, default="[]")
    status = Column(String, default="PENDING_OFFICER_REVIEW") # PENDING_OFFICER_REVIEW, RESOLVED, DISMISSED
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    officer_notes = Column(Text, nullable=True)


class OfficerTripleComparison(Base):
    """
    Revenue Officer Triple Verification Workspace comparisons across
    Registration Deed, Revenue Record (RoR), and Survey Report.
    """
    __tablename__ = "officer_comparisons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comparison_id = Column(String, unique=True, index=True)
    parcel_id = Column(String, index=True)
    registration_ocr_json = Column(Text, default="{}")
    revenue_ocr_json = Column(Text, default="{}")
    survey_ocr_json = Column(Text, default="{}")
    comparison_matrix_json = Column(Text, default="[]")
    overall_confidence_score = Column(Float, default=0.0) # 0 to 100
    registration_match_score = Column(Float, default=0.0)
    revenue_match_score = Column(Float, default=0.0)
    survey_match_score = Column(Float, default=0.0)
    historical_chain_status = Column(String, default="Verified")
    duplicate_claim_status = Column(String, default="None")
    officer_recommendation = Column(Text, default="")
    officer_decision = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED, CALL_FOR_HEARING
    officer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

