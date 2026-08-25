from fastapi import APIRouter
from fastapi.responses import FileResponse
import os
import json

router = APIRouter(prefix="/satellite", tags=["Engine 4 - Satellite Verification"])

@router.get("/preview-image")
def get_preview_image():
    img_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "satellite", "rampur_satellite_preview.png")
    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/png")
    return {"error": "Image not found"}


@router.get("/{parcel_id}")
def verify_satellite_land_use(parcel_id: str):
    """
    Engine 4: Compare registry land-use claim against pre-loaded Sentinel-2 satellite imagery.
    Tag: RULE-STUB / MOCK (pre-computed village satellite scene cross-check).
    """
    sat_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "satellite", "rampur_sentinel2_precomputed.json")
    if os.path.exists(sat_path):
        with open(sat_path, "r") as f:
            sat_data = json.load(f)
    else:
        sat_data = {"land_use_classified": {}}

    classified = sat_data.get("land_use_classified", {}).get(parcel_id, None)

    if classified:
        return {
            "parcel_id": parcel_id,
            "satellite_source": sat_data.get("satellite_source", "Sentinel-2 L2A"),
            "acquisition_date": sat_data.get("acquisition_date", "2026-06-15"),
            "claimed_use": classified["claimed_use"],
            "satellite_detected_use": classified["satellite_detected_use"],
            "built_up_coverage_pct": classified["built_up_coverage_pct"],
            "vegetation_ndvi": classified["vegetation_ndvi"],
            "mismatch_flag": classified["mismatch_flag"],
            "satellite_risk_score": 85.0 if classified["mismatch_flag"] else 10.0,
            "explanation": classified["explanation"],
            "preview_image": "/api/satellite/preview-image",
            "engine_tag": "RULE-STUB / MOCK (pre-downloaded village scene)"
        }

    # Default fallback for clean parcels
    return {
        "parcel_id": parcel_id,
        "satellite_source": "Sentinel-2 L2A",
        "acquisition_date": "2026-06-15",
        "claimed_use": "Agricultural",
        "satellite_detected_use": "Agricultural",
        "built_up_coverage_pct": 3.2,
        "vegetation_ndvi": 0.65,
        "mismatch_flag": False,
        "satellite_risk_score": 5.0,
        "explanation": "Satellite NDVI canopy index (0.65) confirms active agricultural land cover matching RoR claim.",
        "preview_image": "/api/satellite/preview-image",
        "engine_tag": "RULE-STUB / MOCK (pre-downloaded village scene)"
    }
