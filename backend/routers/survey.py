"""
routers/survey.py — Real-Time Survey, Cadastral FMB Layer & Settlement Officer Endpoints
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from services import survey_service

router = APIRouter(prefix="/survey", tags=["Survey Cadastre & Settlement Workflow"])


class GeoreferenceRequest(BaseModel):
    points: list[dict]
    reference_system: str = "EPSG:4326"
    parcel_id: str | None = None


class CaseProgressRequest(BaseModel):
    notes: str | None = None


@router.get("/fmb-layer/{parcel_id}")
def get_fmb_layer(parcel_id: str):
    """Retrieve GeoJSON vector FMB (Field Measurement Book) cadastral layer."""
    layer = survey_service.get_fmb_cadastral_overlay(parcel_id)
    return {"success": True, "data": layer}


@router.post("/georeference")
def georeference_survey_points(req: GeoreferenceRequest):
    """Geo-reference local Ground Control Points (GCPs) to standard GIS coordinates."""
    res = survey_service.georeference_coordinates(req.points, req.reference_system)
    return {"success": True, "data": res}


@router.get("/settlement-cases")
def get_settlement_cases():
    """List all ongoing Settlement Officer boundary and sub-division dispute cases."""
    cases = survey_service.list_settlement_cases()
    return {"success": True, "data": cases}


@router.post("/settlement-cases/{case_id}/progress")
def progress_case(case_id: str, req: CaseProgressRequest):
    """Advance a settlement dispute case to its next procedural phase."""
    try:
        updated = survey_service.progress_settlement_case(case_id, req.notes)
        return {"success": True, "data": updated}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
