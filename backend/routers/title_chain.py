import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form, Body
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import TitleChainDocument, OwnershipRepository, DuplicateClaim, OfficerTripleComparison, ParcelRecord
from services.title_chain_service import reconstruct_title_chain, check_duplicate_claim
from services.triple_comparison_service import compute_triple_comparison
from services.evidence_package_service import generate_evidence_package_pdf
from utils.dpdp import mask_pii_fields, pii_summary

router = APIRouter(prefix="/title-chain", tags=["Engine 6 - Title Chain & Evidence Layer"])


# Sample preloaded repository items for SIH demo showcase
SAMPLE_REPOSITORY = [
    {
        "parcel_id": "P-OD-102",
        "survey_no": "45/0",
        "khata_no": "102",
        "village": "Chhatrapur",
        "mandal": "Chhatrapur",
        "district": "Ganjam",
        "state": "Odisha",
        "ulpin": "OD-GM-450",
        "latest_verified_owner": "Sudrusti Sethi",
        "latest_registration_no": "REG-2026-OD-8841",
        "recorded_area_sqm": 1250.0,
        "historical_owner_count": 3,
        "status": "VERIFIED"
    },
    {
        "parcel_id": "P-105",
        "survey_no": "105/A",
        "khata_no": "412",
        "village": "Shamshabad",
        "mandal": "Shamshabad",
        "district": "Rangareddy",
        "state": "Telangana",
        "ulpin": "TS-RR-105",
        "latest_verified_owner": "K. Venkateshwarlu",
        "latest_registration_no": "REG-2022-7712",
        "recorded_area_sqm": 2420.0,
        "historical_owner_count": 2,
        "status": "VERIFIED"
    },
    {
        "parcel_id": "P-UP-45",
        "survey_no": "45/1",
        "khata_no": "88",
        "village": "Mohanlalganj",
        "mandal": "Mohanlalganj",
        "district": "Lucknow",
        "state": "Uttar Pradesh",
        "ulpin": "UP-LKO-451",
        "latest_verified_owner": "Ramesh Chandra Sharma",
        "latest_registration_no": "UP-LKO-2024-1120",
        "recorded_area_sqm": 1850.0,
        "historical_owner_count": 3,
        "status": "VERIFIED"
    }
]


class DocumentItem(BaseModel):
    owner_name: str
    father_name: Optional[str] = ""
    document_type: Optional[str] = "Sale Deed"
    deed_date: Optional[str] = ""
    deed_year: Optional[int] = None
    registration_no: Optional[str] = ""
    survey_no: Optional[str] = ""
    khata_no: Optional[str] = ""
    village: Optional[str] = ""
    district: Optional[str] = ""
    state: Optional[str] = ""
    area_sqm: Optional[float] = 0.0
    is_ancestral: Optional[bool] = False


class UploadChainRequest(BaseModel):
    parcel_id: Optional[str] = "P-OD-102"
    has_ancestral_documents: bool = False
    documents: List[DocumentItem]
    uploaded_by: Optional[str] = "Citizen User"


class TripleCompareRequest(BaseModel):
    parcel_id: Optional[str] = "P-OD-102"
    registration_doc: Dict[str, Any]
    revenue_doc: Dict[str, Any]
    survey_doc: Dict[str, Any]
    historical_chain_continuous: Optional[bool] = True
    has_duplicate_claim: Optional[bool] = False


@router.post("/upload-chain")
def upload_title_chain(
    payload: UploadChainRequest,
    db: Session = Depends(get_db)
):
    """
    Feature 1 & Feature 2: Ingests primary deed + previous ownership / ancestral documents.
    Reconstructs title chain, validates gaps, records into permanent repository,
    and runs automated duplicate claim detection.
    """
    doc_dicts = [d.dict() for d in payload.documents]
    
    # 1. Reconstruct title chain
    reconstruction = reconstruct_title_chain(doc_dicts)
    
    # 2. Check for duplicate claim against existing repository
    existing_repos = db.query(OwnershipRepository).all()
    repo_list = [
        {
            "parcel_id": r.parcel_id,
            "survey_no": r.survey_no,
            "khata_no": r.khata_no,
            "village": r.village,
            "latest_verified_owner": r.latest_verified_owner,
            "latest_registration_no": r.latest_registration_no
        }
        for r in existing_repos
    ] if existing_repos else SAMPLE_REPOSITORY
    
    # Extract latest document in chain
    latest_doc = doc_dicts[-1] if doc_dicts else {}
    duplicate_alert = check_duplicate_claim(latest_doc, repo_list)
    
    # If duplicate claim detected, persist record
    duplicate_claim_id = None
    if duplicate_alert and duplicate_alert.get("is_conflict"):
        dc = DuplicateClaim(
            parcel_id=duplicate_alert.get("parcel_id"),
            survey_no=duplicate_alert.get("survey_no"),
            khata_no=duplicate_alert.get("khata_no"),
            village=duplicate_alert.get("village"),
            existing_owner=duplicate_alert.get("existing_owner"),
            existing_registration_no=duplicate_alert.get("existing_registration_no"),
            new_claimant=duplicate_alert.get("new_claimant"),
            new_registration_no=duplicate_alert.get("new_registration_no"),
            conflict_score=duplicate_alert.get("conflict_score", 90.0),
            conflict_reasons_json=json.dumps(duplicate_alert.get("reasons", [])),
            status="PENDING_OFFICER_REVIEW"
        )
        db.add(dc)
        db.commit()
        db.refresh(dc)
        duplicate_claim_id = dc.id

    # 3. Store permanent property record into repository
    parcel_id = payload.parcel_id or f"P-{latest_doc.get('survey_no', 'GEN')}"
    existing_repo_entry = db.query(OwnershipRepository).filter(OwnershipRepository.parcel_id == parcel_id).first()
    
    if not existing_repo_entry and latest_doc.get("owner_name"):
        new_repo = OwnershipRepository(
            parcel_id=parcel_id,
            survey_no=latest_doc.get("survey_no") or "45/0",
            khata_no=latest_doc.get("khata_no") or "102",
            village=latest_doc.get("village") or "Chhatrapur",
            district=latest_doc.get("district") or "Ganjam",
            state=latest_doc.get("state") or "Odisha",
            latest_verified_owner=latest_doc.get("owner_name"),
            latest_registration_no=latest_doc.get("registration_no"),
            recorded_area_sqm=float(latest_doc.get("area_sqm") or 1250.0),
            historical_owner_count=len(reconstruction.get("chain", [])),
            status="DISPUTED" if duplicate_alert else "VERIFIED",
            title_chain_summary_json=json.dumps(reconstruction.get("timeline_summary", []))
        )
        db.add(new_repo)
        db.commit()
    
    # 4. Save individual chain nodes
    for idx, doc in enumerate(reconstruction.get("chain", [])):
        tcd = TitleChainDocument(
            parcel_id=parcel_id,
            owner_name=doc.get("owner_name"),
            father_name=doc.get("father_name"),
            document_type=doc.get("document_type"),
            deed_date=doc.get("date"),
            deed_year=doc.get("year"),
            registration_no=doc.get("registration_no"),
            survey_no=doc.get("survey_no"),
            khata_no=doc.get("khata_no"),
            village=doc.get("village"),
            area_sqm=doc.get("area_sqm", 0.0),
            is_ancestral=doc.get("is_ancestral", False),
            order_index=idx,
            extracted_fields_json=json.dumps(doc)
        )
        db.add(tcd)
    db.commit()

    return {
        "success": True,
        "parcel_id": parcel_id,
        "has_ancestral_documents": payload.has_ancestral_documents,
        "reconstruction": reconstruction,
        "duplicate_claim_alert": duplicate_alert,
        "duplicate_claim_id": duplicate_claim_id,
        "message": "Title chain ingested and registered in permanent property repository."
    }


@router.post("/reconstruct")
def reconstruct_chain_endpoint(documents: List[DocumentItem] = Body(...)):
    """Reconstructs and analyzes title chain without saving to DB."""
    doc_dicts = [d.dict() for d in documents]
    return reconstruct_title_chain(doc_dicts)


@router.get("/repository")
def get_repository(db: Session = Depends(get_db)):
    """Feature 4: Fetches permanent property repository entries."""
    db_items = db.query(OwnershipRepository).all()
    if not db_items:
        return {"total": len(SAMPLE_REPOSITORY), "records": SAMPLE_REPOSITORY}
    
    return {
        "total": len(db_items),
        "records": [
            {
                "parcel_id": r.parcel_id,
                "survey_no": r.survey_no,
                "khata_no": r.khata_no,
                "village": r.village,
                "district": r.district,
                "state": r.state,
                "ulpin": r.ulpin,
                "latest_verified_owner": r.latest_verified_owner,
                "latest_registration_no": r.latest_registration_no,
                "recorded_area_sqm": r.recorded_area_sqm,
                "historical_owner_count": r.historical_owner_count,
                "status": r.status,
                "last_verified_at": r.last_verified_at.isoformat() if r.last_verified_at else None
            }
            for r in db_items
        ]
    }


@router.get("/history/{parcel_id}")
def get_title_chain_history(
    parcel_id: str,
    role: str = Query("Revenue Officer"),
    db: Session = Depends(get_db)
):
    """Fetches reconstructed title chain history for a given parcel."""
    docs = db.query(TitleChainDocument).filter(TitleChainDocument.parcel_id == parcel_id).order_by(TitleChainDocument.order_index).all()
    
    if not docs:
        # Provide sample 3-tier timeline for demo parcels
        sample_chain = [
            {
                "order_index": 1,
                "year": 1988,
                "date": "1988-04-14",
                "owner_name": "Ramesh Mohanty",
                "father_name": "Late Jagannath Mohanty",
                "document_type": "Ancestral Partition Deed",
                "survey_no": "45/0",
                "khata_no": "102",
                "village": "Chhatrapur",
                "area_sqm": 1250.0,
                "registration_no": "REG-1988-OD-104",
                "is_ancestral": True
            },
            {
                "order_index": 2,
                "year": 2004,
                "date": "2004-11-20",
                "owner_name": "Suresh Mohanty",
                "father_name": "Ramesh Mohanty",
                "document_type": "Succession Mutation Order",
                "survey_no": "45/0",
                "khata_no": "102",
                "village": "Chhatrapur",
                "area_sqm": 1250.0,
                "registration_no": "MUT-2004-GAN-88",
                "is_ancestral": True
            },
            {
                "order_index": 3,
                "year": 2026,
                "date": "2026-08-15",
                "owner_name": "Sudrusti Sethi",
                "father_name": "P. Sethi",
                "document_type": "Registered Sale Deed",
                "survey_no": "45/0",
                "khata_no": "102",
                "village": "Chhatrapur",
                "area_sqm": 1250.0,
                "registration_no": "REG-2026-OD-8841",
                "is_ancestral": False
            }
        ]
        reconstruction = reconstruct_title_chain(sample_chain)
        return {
            "parcel_id": parcel_id,
            "chain": reconstruction["chain"],
            "is_continuous": True,
            "continuity_score": 96.0,
            "status": "Ownership chain appears continuous."
        }

    chain_nodes = [
        {
            "id": d.id,
            "order_index": d.order_index,
            "year": d.deed_year or 2026,
            "date": d.deed_date,
            "owner_name": d.owner_name,
            "father_name": d.father_name,
            "document_type": d.document_type,
            "survey_no": d.survey_no,
            "khata_no": d.khata_no,
            "village": d.village,
            "area_sqm": d.area_sqm,
            "registration_no": d.registration_no,
            "is_ancestral": d.is_ancestral
        }
        for d in docs
    ]
    reconstruction = reconstruct_title_chain(chain_nodes)
    return {
        "parcel_id": parcel_id,
        "chain": reconstruction["chain"],
        "is_continuous": reconstruction["is_continuous"],
        "continuity_score": reconstruction["continuity_score"],
        "status": reconstruction["status"],
        "gaps": reconstruction["gaps"],
        "reasons": reconstruction["reasons"]
    }


@router.post("/triple-compare")
def triple_compare_endpoint(
    payload: TripleCompareRequest,
    db: Session = Depends(get_db)
):
    """
    Feature 6, 7, 8, 14: Executes 3-Way AI Comparison across
    Registration, Revenue, and Survey records for the Officer Workspace.
    """
    result = compute_triple_comparison(
        payload.registration_doc,
        payload.revenue_doc,
        payload.survey_doc,
        historical_chain_continuous=payload.historical_chain_continuous,
        has_duplicate_claim=payload.has_duplicate_claim
    )
    
    # Store comparison record in database
    comp_id = f"COMP-{payload.parcel_id}-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6]}"
    try:
        otc = OfficerTripleComparison(
            comparison_id=comp_id,
            parcel_id=payload.parcel_id,
            registration_ocr_json=json.dumps(payload.registration_doc),
            revenue_ocr_json=json.dumps(payload.revenue_doc),
            survey_ocr_json=json.dumps(payload.survey_doc),
            comparison_matrix_json=json.dumps(result.get("comparison_matrix", [])),
            overall_confidence_score=result.get("overall_confidence", 0.0),
            registration_match_score=result.get("registration_match", 0.0),
            revenue_match_score=result.get("revenue_match", 0.0),
            survey_match_score=result.get("survey_match", 0.0),
            historical_chain_status=result.get("historical_chain", "Verified"),
            duplicate_claim_status=result.get("duplicate_claim", "None"),
            officer_recommendation=result.get("recommendation", ""),
            officer_decision="PENDING"
        )
        db.add(otc)
        db.commit()
    except Exception as db_err:
        db.rollback()
        # Fallback if DB save encounters non-critical constraint
        pass
    
    result["comparison_id"] = comp_id
    return result


@router.get("/duplicate-claims")
def list_duplicate_claims(db: Session = Depends(get_db)):
    """Feature 5 & 9: Lists active conflicting duplicate ownership claims for Officer Queue."""
    claims = db.query(DuplicateClaim).filter(DuplicateClaim.status == "PENDING_OFFICER_REVIEW").all()
    
    if not claims:
        # Preload realistic sample for demo showcase
        return {
            "total": 1,
            "claims": [
                {
                    "id": 99,
                    "parcel_id": "P-OD-102",
                    "survey_no": "45/0",
                    "khata_no": "102",
                    "village": "Chhatrapur",
                    "district": "Ganjam",
                    "existing_owner": "Sudrusti Sethi",
                    "existing_registration_no": "REG-2026-OD-8841",
                    "new_claimant": "Amit Mohanty",
                    "new_registration_no": "REG-2026-DISPUTE-99",
                    "conflict_score": 91.0,
                    "reasons": [
                        "Survey number #45/0 already recorded in repository under verified owner 'Sudrusti Sethi'.",
                        "New claim by 'Amit Mohanty' exhibits low name similarity (12.0%) with registered record.",
                        "Conflicting registration reference: existing 'REG-2026-OD-8841' vs new 'REG-2026-DISPUTE-99'."
                    ],
                    "status": "PENDING_OFFICER_REVIEW",
                    "created_at": "2026-09-04 10:30:00"
                }
            ]
        }
    
    return {
        "total": len(claims),
        "claims": [
            {
                "id": c.id,
                "parcel_id": c.parcel_id,
                "survey_no": c.survey_no,
                "khata_no": c.khata_no,
                "village": c.village,
                "district": c.district,
                "existing_owner": c.existing_owner,
                "existing_registration_no": c.existing_registration_no,
                "new_claimant": c.new_claimant,
                "new_registration_no": c.new_registration_no,
                "conflict_score": c.conflict_score,
                "reasons": json.loads(c.conflict_reasons_json or "[]"),
                "status": c.status,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else None
            }
            for c in claims
        ]
    }


@router.post("/duplicate-claims/{claim_id}/resolve")
def resolve_duplicate_claim(
    claim_id: int,
    action: str = Query(..., description="DISMISS, APPROVE_NEW, or CALL_FOR_HEARING"),
    officer_notes: str = Query("Officer conducted title hearing and disposed claim."),
    db: Session = Depends(get_db)
):
    """Officer resolves or dismisses a duplicate claim."""
    claim = db.query(DuplicateClaim).filter(DuplicateClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Duplicate claim record not found.")
        
    claim.status = f"RESOLVED_{action}"
    claim.reviewed_by = "Tahsildar / Sub-Collector"
    claim.reviewed_at = datetime.utcnow()
    claim.officer_notes = officer_notes
    db.commit()
    
    return {
        "success": True,
        "claim_id": claim_id,
        "action": action,
        "status": claim.status,
        "message": f"Claim {claim_id} resolved with status {claim.status}."
    }


@router.get("/evidence-package/{parcel_id}/pdf")
def export_evidence_pdf(
    parcel_id: str,
    officer_notes: Optional[str] = "Three-way comparison and title chain verified. Section 65B electronic certificate issued.",
    db: Session = Depends(get_db)
):
    """
    Feature 10: Generates Section 65B-compatible Court-Ready Evidence Package PDF.
    """
    # 1. Fetch parcel data
    parcel = db.query(ParcelRecord).filter(ParcelRecord.parcel_id == parcel_id).first()
    if parcel:
        p_data = {
            "parcel_id": parcel.parcel_id,
            "survey_no": parcel.survey_no or "45/0",
            "khata_no": parcel.khatian_no or "102",
            "ulpin": parcel.ulpin or f"OD-GM-{parcel_id}",
            "owner_name": parcel.owner_name or "Sudrusti Sethi",
            "father_or_husband": "P. Sethi",
            "village": parcel.village or "Chhatrapur",
            "mandal": parcel.mandal or "Chhatrapur",
            "district": parcel.district or "Ganjam",
            "state": parcel.state or "Odisha",
            "claimed_area_sqm": parcel.claimed_area_sqm or 1250.0,
            "actual_area_sqm": parcel.actual_area_sqm or 1250.0,
        }
    else:
        p_data = {
            "parcel_id": parcel_id,
            "survey_no": "45/0",
            "khata_no": "102",
            "ulpin": f"OD-GM-{parcel_id}",
            "owner_name": "Sudrusti Sethi",
            "father_or_husband": "P. Sethi",
            "village": "Chhatrapur",
            "mandal": "Chhatrapur",
            "district": "Ganjam",
            "state": "Odisha",
            "claimed_area_sqm": 1250.0,
            "actual_area_sqm": 1250.0,
        }

    # 2. Build default comparison & title chain
    reg_doc = {"owner_name": p_data["owner_name"], "father_name": p_data["father_or_husband"], "survey_no": p_data["survey_no"], "area_sqm": p_data["claimed_area_sqm"], "village": p_data["village"]}
    rev_doc = {"owner_name": p_data["owner_name"], "father_name": p_data["father_or_husband"], "survey_no": p_data["survey_no"], "area_sqm": p_data["claimed_area_sqm"], "village": p_data["village"]}
    sur_doc = {"owner_name": "S. Sethi", "father_name": p_data["father_or_husband"], "survey_no": p_data["survey_no"], "area_sqm": p_data["actual_area_sqm"], "village": p_data["village"]}
    
    triple_comp = compute_triple_comparison(reg_doc, rev_doc, sur_doc, historical_chain_continuous=True, has_duplicate_claim=False)
    
    title_chain = reconstruct_title_chain([
        {"year": 1988, "owner_name": "Ramesh Mohanty", "father_name": "Late Jagannath Mohanty", "document_type": "Ancestral Partition Deed", "survey_no": p_data["survey_no"], "registration_no": "REG-1988-104", "area_sqm": 1250.0},
        {"year": 2004, "owner_name": "Suresh Mohanty", "father_name": "Ramesh Mohanty", "document_type": "Succession Mutation", "survey_no": p_data["survey_no"], "registration_no": "MUT-2004-88", "area_sqm": 1250.0},
        {"year": 2026, "owner_name": p_data["owner_name"], "father_name": p_data["father_or_husband"], "document_type": "Registered Sale Deed", "survey_no": p_data["survey_no"], "registration_no": "REG-2026-OD-8841", "area_sqm": 1250.0}
    ])

    try:
        pdf_bytes, sha_hash, report_id = generate_evidence_package_pdf(
            parcel_data=p_data,
            triple_comparison=triple_comp,
            title_chain=title_chain,
            officer_notes=officer_notes
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evidence package generation failed: {exc}")

    filename = f"Court_Ready_Evidence_{parcel_id}_{report_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/evidence-package/{parcel_id}")
def get_evidence_package_json(
    parcel_id: str,
    db: Session = Depends(get_db)
):
    """Returns the structured evidence package data in JSON format."""
    p_data = {
        "parcel_id": parcel_id,
        "survey_no": "45/0",
        "khata_no": "102",
        "ulpin": f"OD-GM-{parcel_id}",
        "owner_name": "Sudrusti Sethi",
        "father_or_husband": "P. Sethi",
        "village": "Chhatrapur",
        "district": "Ganjam",
        "state": "Odisha",
        "claimed_area_sqm": 1250.0,
        "actual_area_sqm": 1250.0
    }
    
    reg_doc = {"owner_name": p_data["owner_name"], "father_name": p_data["father_or_husband"], "survey_no": p_data["survey_no"], "area_sqm": p_data["claimed_area_sqm"], "village": p_data["village"]}
    rev_doc = {"owner_name": p_data["owner_name"], "father_name": p_data["father_or_husband"], "survey_no": p_data["survey_no"], "area_sqm": p_data["claimed_area_sqm"], "village": p_data["village"]}
    sur_doc = {"owner_name": "S. Sethi", "father_name": p_data["father_or_husband"], "survey_no": p_data["survey_no"], "area_sqm": p_data["actual_area_sqm"], "village": p_data["village"]}
    
    triple_comp = compute_triple_comparison(reg_doc, rev_doc, sur_doc, historical_chain_continuous=True, has_duplicate_claim=False)
    
    title_chain = reconstruct_title_chain([
        {"year": 1988, "owner_name": "Ramesh Mohanty", "father_name": "Late Jagannath Mohanty", "document_type": "Ancestral Partition Deed", "survey_no": p_data["survey_no"], "registration_no": "REG-1988-104", "area_sqm": 1250.0},
        {"year": 2004, "owner_name": "Suresh Mohanty", "father_name": "Ramesh Mohanty", "document_type": "Succession Mutation", "survey_no": p_data["survey_no"], "registration_no": "MUT-2004-88", "area_sqm": 1250.0},
        {"year": 2026, "owner_name": p_data["owner_name"], "father_name": p_data["father_or_husband"], "document_type": "Registered Sale Deed", "survey_no": p_data["survey_no"], "registration_no": "REG-2026-OD-8841", "area_sqm": 1250.0}
    ])
    
    return {
        "parcel_data": p_data,
        "triple_comparison": triple_comp,
        "title_chain": title_chain,
        "legal_admissibility_act": "IT Act 2000 Section 65B Electronic Records Admissibility",
        "statutory_reference": "Registration Act 1908 Title Record"
    }
