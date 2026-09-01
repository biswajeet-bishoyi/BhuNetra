"""
routers/mutations.py — Mutation request management.

Officers draw a new polygon via Leaflet.draw on the map and POST the
geometry here. The request is stored in the mutation_requests table for
later review and approval.
"""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import MutationRequest

router = APIRouter(prefix="/mutations", tags=["Parcel Mutation Requests"])


class MutationCreate(BaseModel):
    parcel_id: str | None = None
    requested_by: str
    reason: str
    geometry: dict  # GeoJSON Polygon geometry


class MutationReviewRequest(BaseModel):
    action: str  # APPROVE, REJECT
    reviewed_by: str
    notes: str = ""


@router.post("/new")
def create_mutation_request(req: MutationCreate, db: Session = Depends(get_db)):
    """
    Submit a new mutation request with the drawn polygon geometry.
    The geometry is stored as GeoJSON text (no spatialite required).
    """
    if not req.geometry or req.geometry.get("type") != "Polygon":
        raise HTTPException(status_code=400, detail="geometry must be a valid GeoJSON Polygon.")

    if not req.reason or len(req.reason.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="reason must be at least 5 characters (Sec 65B audit trail)."
        )

    mr = MutationRequest(
        parcel_id=req.parcel_id,
        requested_by=req.requested_by,
        reason=req.reason.strip(),
        geometry_geojson=json.dumps(req.geometry),
        status="PENDING",
        created_at=datetime.utcnow(),
    )
    db.add(mr)
    db.commit()
    db.refresh(mr)

    return {
        "status": "CREATED",
        "mutation_id": mr.id,
        "parcel_id": mr.parcel_id,
        "requested_by": mr.requested_by,
        "created_at": mr.created_at.isoformat(),
        "message": f"Mutation request {mr.id} created and queued for review.",
    }


@router.get("/")
def list_mutation_requests(
    status: str | None = None,
    parcel_id: str | None = None,
    db: Session = Depends(get_db),
):
    """List all mutation requests, optionally filtered by status / parcel."""
    q = db.query(MutationRequest)
    if status:
        q = q.filter(MutationRequest.status == status.upper())
    if parcel_id:
        q = q.filter(MutationRequest.parcel_id == parcel_id)
    rows = q.order_by(MutationRequest.created_at.desc()).all()
    return {
        "total": len(rows),
        "requests": [
            {
                "id": r.id,
                "parcel_id": r.parcel_id,
                "requested_by": r.requested_by,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "reviewed_by": r.reviewed_by,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "review_notes": r.review_notes,
                "geometry": json.loads(r.geometry_geojson) if r.geometry_geojson else None,
            }
            for r in rows
        ],
    }


@router.get("/{mutation_id}")
def get_mutation_request(mutation_id: int, db: Session = Depends(get_db)):
    r = db.query(MutationRequest).filter(MutationRequest.id == mutation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Mutation request {mutation_id} not found.")
    return {
        "id": r.id,
        "parcel_id": r.parcel_id,
        "requested_by": r.requested_by,
        "reason": r.reason,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "reviewed_by": r.reviewed_by,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        "review_notes": r.review_notes,
        "geometry": json.loads(r.geometry_geojson) if r.geometry_geojson else None,
    }


@router.post("/{mutation_id}/review")
def review_mutation(mutation_id: int, req: MutationReviewRequest, db: Session = Depends(get_db)):
    """Approve or reject a pending mutation request."""
    r = db.query(MutationRequest).filter(MutationRequest.id == mutation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Mutation request {mutation_id} not found.")
    if r.status != "PENDING":
        raise HTTPException(status_code=409, detail=f"Cannot review a request in status {r.status}.")
    if req.action.upper() not in {"APPROVE", "REJECT"}:
        raise HTTPException(status_code=400, detail="action must be APPROVE or REJECT.")

    r.status = "APPROVED" if req.action.upper() == "APPROVE" else "REJECTED"
    r.reviewed_by = req.reviewed_by
    r.reviewed_at = datetime.utcnow()
    r.review_notes = req.notes.strip() if req.notes else None
    db.commit()
    db.refresh(r)

    return {
        "status": r.status,
        "mutation_id": r.id,
        "reviewed_by": r.reviewed_by,
        "reviewed_at": r.reviewed_at.isoformat(),
        "message": f"Mutation request {r.id} {r.status}.",
    }
