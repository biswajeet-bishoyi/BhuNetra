from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
import os
import json
import geopandas as gpd

from utils.dpdp import pii_summary

router = APIRouter(prefix="/satellite", tags=["Engine 4 - Satellite Verification"])

# Thresholds for inferred built-up detection (when no Sentinel-2 tile is pre-loaded)
_AREA_DEVIATION_BUILT_UP_THRESHOLD = 10.0   # % area deviation suggesting structure
_BUILT_UP_NDVI_THRESHOLD = 0.35              # NDVI below this suggests non-vegetation


def _load_parcel_land_use(parcel_id: str) -> dict:
    """Read a parcel's land_use_claim from the GeoJSON registry or uploaded parcels."""
    try:
        from services import uploaded_parcels
    except ImportError:
        from backend.services import uploaded_parcels
    up = uploaded_parcels.get_uploaded_parcel(parcel_id)
    if up:
        prop = up["properties"]
        return {
            "claimed_use": str(prop.get("land_use_claim", "Residential")),
            "claimed_area_sqm": float(prop.get("claimed_area_sqm") or 26.75),
            "actual_area_sqm": float(prop.get("actual_area_sqm") or 26.75),
        }

    geojson_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "synthetic", "parcels.geojson"
    )
    if not os.path.exists(geojson_path):
        return {}
    gdf = gpd.read_file(geojson_path)
    match = gdf[gdf["parcel_id"] == parcel_id]
    if match.empty:
        return {}
    row = match.iloc[0]
    return {
        "claimed_use": str(row.get("land_use_claim", "")) or "Agricultural",
        "claimed_area_sqm": float(row.get("claimed_area_sqm") or 0),
        "actual_area_sqm": float(row.get("actual_area_sqm") or 0),
    }


def _classify_from_precomputed(parcel_id: str) -> dict | None:
    """Return pre-computed Sentinel-2 classification for a known parcel, or None."""
    sat_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "satellite", "rampur_sentinel2_precomputed.json"
    )
    if not os.path.exists(sat_path):
        return None
    with open(sat_path) as f:
        sat_data = json.load(f)
    classified = sat_data.get("land_use_classified", {}).get(parcel_id)
    if not classified:
        return None
    return {
        **classified,
        "source": "Sentinel-2 L2A pre-computed tile",
        "acquisition_date": sat_data.get("acquisition_date", "2026-06-15"),
    }


def _infer_satellite_from_parcel(parcel_id: str) -> dict:
    """
    Infer satellite-classification signals when no Sentinel-2 tile exists for this parcel.

    Uses two proxy signals derivable from the registry alone:
      1. Area deviation from GIS cadastre: large % deviation can indicate a built structure
         on agricultural land (building doesn't change the polygon, just fills it).
      2. Land-use claim: Agricultural vs Commercial/Residential affects baseline NDVI expectation.

    This is honest — it labels itself as "REGISTRY-INFERRED" so there is no false
    claim of satellite imagery when none exists.
    """
    parcel = _load_parcel_land_use(parcel_id)
    claimed_use = parcel.get("claimed_use", "Agricultural")
    claimed = parcel.get("claimed_area_sqm", 0) or 0
    actual = parcel.get("actual_area_sqm", 0) or 0

    deviation_pct = 0.0
    if claimed > 0:
        deviation_pct = round(abs(actual - claimed) / claimed * 100, 2)

    # Infer built-up coverage from area deviation
    inferred_built_up = min(deviation_pct * 3, 99.9)  # proxy heuristic
    inferred_ndvi = max(0.0, _BUILT_UP_NDVI_THRESHOLD * 2 - inferred_built_up / 50)

    if claimed_use == "Agricultural" and inferred_built_up > 20:
        detected_use = "Commercial/Built-up (registry-inferred)"
        mismatch = True
        explanation = (
            f"Registry-inferred: {deviation_pct}% area deviation from cadastre suggests "
            f"built structure fill on {claimed_use} land. Satellite verification recommended."
        )
    elif claimed_use == "Commercial" and inferred_built_up < 10:
        detected_use = "Agricultural (registry-inferred)"
        mismatch = True
        explanation = (
            f"Registry-inferred: {deviation_pct}% area deviation suggests {claimed_use} "
            f"claim may not match physical built-up extent."
        )
    elif claimed_use == "Residential" and inferred_built_up > 30:
        detected_use = "Commercial (registry-inferred)"
        mismatch = True
        explanation = (
            f"Registry-inferred: {deviation_pct}% area deviation may indicate "
            f"commercial expansion beyond residential scope."
        )
    else:
        detected_use = f"{claimed_use} (registry-inferred)"
        mismatch = False
        explanation = (
            f"Registry-inferred: No satellite tile available. "
            f"{claimed_use} claim with {deviation_pct}% area deviation shows no strong "
            f"built-up signal. Satellite imagery recommended for field verification."
        )

    return {
        "claimed_use": claimed_use,
        "satellite_detected_use": detected_use,
        "built_up_coverage_pct": round(inferred_built_up, 1),
        "vegetation_ndvi": round(inferred_ndvi, 2),
        "confidence_score": 0.5,
        "mismatch_flag": mismatch,
        "explanation": explanation,
        "area_deviation_pct": deviation_pct,
        "source": "REGISTRY-INFERRED (no Sentinel-2 tile)",
        "acquisition_date": "N/A",
    }


@router.get("/preview-image")
def get_preview_image():
    img_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "satellite", "rampur_satellite_preview.png"
    )
    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/png")
    return {"error": "Preview image not found"}


@router.get("/{parcel_id}")
def verify_satellite_land_use(
    parcel_id: str,
    role: str = Query("Revenue Officer", description="Requesting role for DPDP masking"),
):
    """
    Engine 4: Compare registry land-use claim against Sentinel-2 satellite scene.

    Returns Sentinel-2 data when a tile is pre-loaded; otherwise falls back to
    REGISTRY-INFERRED classification using area deviation as a built-up proxy signal.
    The source is always disclosed so officers know the confidence level.

    Response shape now includes a `factors` list for SHAP-style Engine-5 attribution.
    """
    # Try pre-computed Sentinel-2 tile first
    precomputed = _classify_from_precomputed(parcel_id)

    if precomputed:
        satellite_detected_use = precomputed["satellite_detected_use"]
        mismatch_flag = precomputed["mismatch_flag"]
        explanation = precomputed["explanation"]
        built_up = precomputed["built_up_coverage_pct"]
        ndvi = precomputed["vegetation_ndvi"]
        source = precomputed["source"]
        acquisition_date = precomputed["acquisition_date"]
        confidence = precomputed["confidence_score"]
    else:
        inferred = _infer_satellite_from_parcel(parcel_id)
        satellite_detected_use = inferred["satellite_detected_use"]
        mismatch_flag = inferred["mismatch_flag"]
        explanation = inferred["explanation"]
        built_up = inferred["built_up_coverage_pct"]
        ndvi = inferred["vegetation_ndvi"]
        source = inferred["source"]
        acquisition_date = inferred["acquisition_date"]
        confidence = inferred["confidence_score"]

    # Compute SHAP-style factors (Engine 5 attribution)
    factors: list[dict] = []
    if mismatch_flag:
        if built_up > 50:
            factors.append({
                "name": "high_built_up_mismatch",
                "severity": "critical",
                "score": 80.0,
                "weight_in_25pct": 1.0,
                "evidence": {
                    "claimed_use": precomputed["claimed_use"] if precomputed else "Agricultural",
                    "satellite_detected_use": satellite_detected_use,
                    "built_up_coverage_pct": built_up,
                    "vegetation_ndvi": ndvi,
                },
            })
        elif built_up > 20:
            factors.append({
                "name": "moderate_built_up_mismatch",
                "severity": "elevated",
                "score": 55.0,
                "weight_in_25pct": 1.0,
                "evidence": {
                    "claimed_use": precomputed["claimed_use"] if precomputed else "Agricultural",
                    "satellite_detected_use": satellite_detected_use,
                    "built_up_coverage_pct": built_up,
                    "vegetation_ndvi": ndvi,
                },
            })
    else:
        factors.append({
            "name": "land_use_confirmed",
            "severity": "clean",
            "score": 5.0,
            "weight_in_25pct": 1.0,
            "evidence": {
                "claimed_use": precomputed["claimed_use"] if precomputed else "Agricultural",
                "satellite_detected_use": satellite_detected_use,
                "built_up_coverage_pct": built_up,
                "vegetation_ndvi": ndvi,
            },
        })

    # Aggregate satellite score from factors
    satellite_risk_score = max((f["score"] * f["weight_in_25pct"] for f in factors), default=5.0)

    response = {
        "parcel_id": parcel_id,
        "satellite_source": "Sentinel-2 L2A" if precomputed else "REGISTRY-INFERRED",
        "data_source": source,
        "acquisition_date": acquisition_date,
        "claimed_use": precomputed["claimed_use"] if precomputed else "Agricultural",
        "satellite_detected_use": satellite_detected_use,
        "built_up_coverage_pct": built_up,
        "vegetation_ndvi": ndvi,
        "mismatch_flag": mismatch_flag,
        "confidence_score": confidence,
        "satellite_risk_score": round(satellite_risk_score, 1),
        "explanation": explanation,
        "factors": factors,
        "preview_image": "/api/satellite/preview-image",
        "engine_tag": (
            "RULE-STUB / MOCK (pre-downloaded Sentinel-2 scene + registry inference)"
            if not precomputed else
            "RULE-STUB / MOCK (pre-downloaded Sentinel-2 scene)"
        ),
        "dpdp_context": pii_summary({}, role),
    }

    return response
