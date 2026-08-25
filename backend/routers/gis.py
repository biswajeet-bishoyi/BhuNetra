from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import geopandas as gpd
import pandas as pd
import numpy as np
import json
import os
from database import get_db
from models import ParcelRecord
from ml_models import GISAnomalyEngine

router = APIRouter(prefix="/gis-check", tags=["Engine 2 - GIS Validation"])
gis_engine = GISAnomalyEngine()

@router.get("/")
def get_all_parcels_gis_status(db: Session = Depends(get_db)):
    """
    Fetch all cadastral parcels with their spatial geometries and GIS anomaly flags.
    Runs in-memory via GeoPandas/Shapely with STRtree spatial index.
    Zero SQLite C-extension dependencies.
    """
    geojson_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic", "parcels.geojson")
    if not os.path.exists(geojson_path):
        raise HTTPException(status_code=404, detail="Synthetic parcel GeoJSON file not found. Run generate_synthetic_data.py first.")

    gdf = gpd.read_file(geojson_path)
    features_df = gis_engine.extract_spatial_features(gdf)
    predictions = gis_engine.predict_and_explain(features_df)
    
    pred_map = {p["parcel_id"]: p for p in predictions}

    features_list = []
    for idx, row in gdf.iterrows():
        pid = row["parcel_id"]
        pred = pred_map.get(pid, {})
        
        prop = {}
        for k, v in row.items():
            if k == "geometry":
                continue
            if pd.isna(v):
                prop[k] = None
            elif hasattr(v, "item"):
                prop[k] = v.item()
            else:
                prop[k] = v
            
        prop["gis_risk_score"] = float(pred.get("risk_score", 0.0))
        prop["gis_is_anomalous"] = bool(pred.get("is_anomalous", False))
        prop["gis_explanations"] = pred.get("explanations", [])
        prop["gis_features"] = pred.get("features", {})

        features_list.append({
            "type": "Feature",
            "properties": prop,
            "geometry": row.geometry.__geo_interface__
        })

    return {
        "type": "FeatureCollection",
        "features": features_list,
        "spatial_architecture": "In-memory GeoPandas/Shapely STRtree processing (Zero SpatiaLite extension required)",
        "production_upgrade_path": "PostGIS"
    }

@router.get("/parcel/{parcel_id}")
def check_single_parcel_gis(parcel_id: str, db: Session = Depends(get_db)):
    """Evaluate topology, boundary overlaps, gaps, and area deviation for a single parcel in memory."""
    geojson_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic", "parcels.geojson")
    gdf = gpd.read_file(geojson_path)
    
    target = gdf[gdf["parcel_id"] == parcel_id]
    if target.empty:
        raise HTTPException(status_code=404, detail=f"Parcel {parcel_id} not found.")

    features_df = gis_engine.extract_spatial_features(gdf)
    predictions = gis_engine.predict_and_explain(features_df)

    pred = next((p for p in predictions if p["parcel_id"] == parcel_id), {})
    return pred
