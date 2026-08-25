from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import os
from database import get_db

router = APIRouter(prefix="/revenue-court", tags=["Revenue Court Status Management"])

class RevenueCourtUpdateRequest(BaseModel):
    parcel_id: str
    court_status: str # Clean, Stay Order, Mutation Pending, Court Case
    case_reference_no: str = ""
    updated_by: str = "Revenue Officer Rampur"

VALID_STATUSES = ["Clean", "Stay Order", "Mutation Pending", "Court Case"]

@router.post("/update")
def update_revenue_court_status(req: RevenueCourtUpdateRequest, db: Session = Depends(get_db)):
    """Update Revenue Court status field for a parcel."""
    if req.court_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid court status. Must be one of {VALID_STATUSES}")

    geojson_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic", "parcels.geojson")
    with open(geojson_path, "r") as f:
        data = json.load(f)

    updated = False
    for feat in data["features"]:
        if feat["properties"]["parcel_id"] == req.parcel_id:
            feat["properties"]["revenue_court_status"] = req.court_status
            updated = True
            break

    if updated:
        with open(geojson_path, "w") as f:
            json.dump(data, f, indent=2)

    return {
        "status": "SUCCESS",
        "parcel_id": req.parcel_id,
        "revenue_court_status": req.court_status,
        "case_reference_no": req.case_reference_no,
        "updated_by": req.updated_by,
        "message": f"Revenue Court status for parcel {req.parcel_id} updated to {req.court_status}"
    }
