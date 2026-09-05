"""
routers/ml_vision.py — Endpoints for Indic NLP, YOLO Sketch Extraction & Satellite Crop Classification
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import ml_vision_service

router = APIRouter(prefix="/ml", tags=["ML Vision & Satellite AI"])


class IndicNLPRequest(BaseModel):
    raw_text: str
    script_hint: str = "auto"


class CropClassifyRequest(BaseModel):
    ndvi: float = 0.65
    ndbi: float = -0.22


@router.post("/indic-nlp")
def analyze_indic_text(req: IndicNLPRequest):
    """Analyze multilingual text using IndicBERT NLP models."""
    res = ml_vision_service.analyze_indic_script_nlp(req.raw_text, req.script_hint)
    return {"success": True, "data": res}


@router.post("/sketch-to-polygon")
def extract_sketch_polygon():
    """Extract plot polygon boundaries from deed sketch insets via YOLOv8 model."""
    res = ml_vision_service.extract_plot_boundaries_from_sketch(b"")
    return {"success": True, "data": res}


@router.post("/crop-classify")
def classify_crop_vs_builtup(req: CropClassifyRequest):
    """Classify satellite multispectral indices into crop vs built-up encroachment."""
    res = ml_vision_service.classify_satellite_crop_vs_builtup(req.ndvi, req.ndbi)
    return {"success": True, "data": res}
