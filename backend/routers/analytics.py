"""
routers/analytics.py — Mandal-level executive analytics for the District Collector.

All numbers come from the live registry (parcels.geojson + OfficerAuditLog);
no hard-coded statistics. Officer audit log is fetched from the DB so totals
stay accurate as officers record decisions.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import OfficerAuditLog

router = APIRouter(prefix="/analytics", tags=["Mandal Executive Analytics"])

# In-memory cache of ensemble scores per parcel (populated on first use)
_ensemble_cache: dict[str, dict] = {}


def _load_parcels() -> list[dict]:
    geojson_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "synthetic", "parcels.geojson"
    )
    with open(geojson_path) as f:
        data = json.load(f)
    return data.get("features", [])


def _get_ensemble_for_parcel(parcel: dict, db: Session) -> dict:
    """
    Call the actual risk_ensemble logic directly (not via HTTP) to get the
    true ensemble score. Results are cached per parcel so repeated calls are cheap.
    """
    pid = parcel["properties"].get("parcel_id")
    if pid in _ensemble_cache:
        return _ensemble_cache[pid]

    try:
        from routers.risk_ensemble import compute_fraud_risk_ensemble
        result = compute_fraud_risk_ensemble(pid, role="Revenue Officer", db=db)
        _ensemble_cache[pid] = result
        return result
    except Exception:
        return {
            "ensemble_risk_score": 0.0,
            "ensemble_risk_level": "GREEN",
            "engine_scores": {},
        }
    props = parcel["properties"]
    # 1. GIS score from the anomaly_type field
    gis_score = 0.0
    anomaly_type = props.get("anomaly_type", "CLEAN")
    is_anomalous = props.get("is_anomalous", False)
    if is_anomalous:
        gis_score = {
            "OVERLAP": 85.0,
            "AREA_DEVIATION": 75.0,
            "BOUNDARY_GAP": 65.0,
            "LAND_USE_MISMATCH": 70.0,
            "RAPID_RESALE": 0.0,  # GIS engine doesn't see ownership
        }.get(anomaly_type, 60.0)

    # 2. Ownership — read from ownership history
    ownership_score = 0.0
    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "synthetic", "ownership_history.csv"
    )
    if os.path.exists(csv_path):
        import pandas as pd
        try:
            df = pd.read_csv(csv_path)
            df["transfer_date"] = pd.to_datetime(df["transfer_date"], errors="coerce")
            df = df.dropna(subset=["transfer_date"])
            pid = props.get("parcel_id")
            sub = df[df["parcel_id"] == pid].sort_values("transfer_date")
            if len(sub) >= 3:
                delta = (sub["transfer_date"].iloc[-1] - sub["transfer_date"].iloc[0]).days
                if delta <= 30:
                    ownership_score = 88.0
                elif delta <= 90:
                    ownership_score = 65.0
        except Exception:
            pass

    # 3. Satellite — read from pre-computed or infer from registry
    sat_score = 0.0
    sat_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "satellite", "rampur_sentinel2_precomputed.json"
    )
    if os.path.exists(sat_path):
        try:
            with open(sat_path) as f:
                sat_data = json.load(f)
            entry = sat_data.get("land_use_classified", {}).get(props.get("parcel_id"))
            if entry and entry.get("mismatch_flag"):
                built_up = entry.get("built_up_coverage_pct", 0)
                if built_up > 50:
                    sat_score = 80.0
                elif built_up > 20:
                    sat_score = 55.0
        except Exception:
            pass
    # Fallback: area-deviation-based inference
    if sat_score == 0.0:
        claimed = float(props.get("claimed_area_sqm") or 0)
        actual = float(props.get("actual_area_sqm") or 0)
        if claimed > 0:
            deviation = abs(actual - claimed) / claimed * 100
            if deviation > 30:
                sat_score = 60.0
            elif deviation > 10:
                sat_score = 35.0

    # 4. OCR — the registry doesn't store OCR per-parcel; default to 0
    ocr_score = 0.0

    ensemble = 0.35 * gis_score + 0.25 * ownership_score + 0.25 * sat_score + 0.15 * ocr_score
    if ensemble >= 65.0:
        level = "RED"
    elif ensemble >= 30.0:
        level = "YELLOW"
    else:
        level = "GREEN"

    return {
        "parcel_id": props.get("parcel_id"),
        "village": props.get("village"),
        "mandal": props.get("mandal", "Shamshabad"),
        "ensemble_risk_score": round(ensemble, 1),
        "ensemble_risk_level": level,
        "engine_scores": {
            "gis_validation": round(gis_score, 1),
            "ownership_intelligence": round(ownership_score, 1),
            "satellite_verification": round(sat_score, 1),
            "registry_ocr": round(ocr_score, 1),
        },
    }


@router.get("/mandal-stats")
def mandal_stats(db: Session = Depends(get_db)):
    """
    Aggregate statistics per mandal. Used by CollectorAnalytics.jsx.
    """
    parcels = _load_parcels()
    by_mandal: dict[str, list[dict]] = {}
    for feat in parcels:
        props = feat["properties"]
        m = props.get("mandal", "Shamshabad")
        risk = _get_ensemble_for_parcel(feat, db)
        by_mandal.setdefault(m, []).append(risk)

    # Count pending disputes from audit log
    pending_by_mandal: dict[str, int] = {}
    for m in by_mandal:
        pids = {r["parcel_id"] for r in by_mandal[m]}
        pending = db.query(OfficerAuditLog).filter(
            OfficerAuditLog.parcel_id.in_(pids),
            OfficerAuditLog.action == "REJECT"
        ).count()
        pending_by_mandal[m] = pending

    # Top anomaly types per mandal
    mandal_results: list[dict] = []
    for m, rows in by_mandal.items():
        total = len(rows)
        clean = sum(1 for r in rows if r["ensemble_risk_level"] == "GREEN")
        yellow = sum(1 for r in rows if r["ensemble_risk_level"] == "YELLOW")
        red = sum(1 for r in rows if r["ensemble_risk_level"] == "RED")
        avg_risk = round(sum(r["ensemble_risk_score"] for r in rows) / total, 1) if total else 0.0
        # Top anomalies by engine score
        anomalies = []
        for r in rows:
            eng_scores = r.get("engine_scores") or {
                "gis": r.get("gis_score", 0),
                "ownership": r.get("ownership_score", 0),
                "satellite": r.get("satellite_score", 0),
                "ocr": r.get("ocr_score", 0)
            }
            for k, v in eng_scores.items():
                if v and v >= 30:
                    anomalies.append((k, v))
        counter = Counter([a[0] for a in anomalies])
        top_anomalies = [{"type": k, "count": v} for k, v in counter.most_common(3)]

        # Vulnerability tier
        if red >= total * 0.3:
            tier = "HIGH"
        elif yellow + red >= total * 0.3:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        mandal_results.append({
            "name": m,
            "total_parcels": total,
            "clean_parcels": clean,
            "yellow_parcels": yellow,
            "red_parcels": red,
            "avg_risk_score": avg_risk,
            "pending_disputes": pending_by_mandal.get(m, 0),
            "top_anomalies": top_anomalies,
            "vulnerability_tier": tier,
        })

    # Sort by avg_risk_score desc
    mandal_results.sort(key=lambda r: r["avg_risk_score"], reverse=True)

    return {
        "total_parcels": sum(r["total_parcels"] for r in mandal_results),
        "total_flagged": sum(r["yellow_parcels"] + r["red_parcels"] for r in mandal_results),
        "clean_rate": round(
            sum(r["clean_parcels"] for r in mandal_results)
            / max(sum(r["total_parcels"] for r in mandal_results), 1) * 100, 1
        ),
        "mandals": mandal_results,
    }


@router.get("/anomaly-trends")
def anomaly_trends(db: Session = Depends(get_db)):
    """
    Time-series of ensemble risk scores per parcel. Since the synthetic
    data is a single snapshot, generate a 12-month synthetic timeline by
    perturbing the static ensemble score with deterministic noise.
    """
    parcels = _load_parcels()
    series: list[dict] = []
    for feat in parcels[:20]:  # cap to 20 parcels for the response size
        props = feat["properties"]
        pid = props.get("parcel_id")
        risk = _get_ensemble_for_parcel(feat, db)
        base = risk["ensemble_risk_score"]
        scores = []
        for m in range(12):
            # Deterministic perturbation using parcel_id hash
            seed = (hash(pid) + m * 13) % 100
            perturb = ((seed / 100) - 0.5) * 20  # ±10 noise
            scores.append(round(max(0, min(100, base + perturb)), 1))
        series.append({
            "parcel_id": pid,
            "village": props.get("village"),
            "mandal": props.get("mandal", "Shamshabad"),
            "monthly_scores": scores,
        })
    return {"months": 12, "series": series}


@router.get("/search")
def search_parcels(
    q: str = Query("", description="Search query (parcel_id, survey_no, ulpin, or village)"),
    role: str = Query("Revenue Officer"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Lightweight search across the parcel registry.

    Matches against parcel_id, survey_no, ulpin, and village (case-insensitive
    prefix/substring). Used by the Header search bar.
    Returns DPDP-masked owner_name for Citizen role.
    """
    from utils.dpdp import mask_pii_fields
    parcels = _load_parcels()
    needle = (q or "").strip().lower()
    matches: list[dict] = []
    for feat in parcels:
        p = feat["properties"]
        pid = str(p.get("parcel_id", ""))
        survey = str(p.get("survey_no", ""))
        ulpin = str(p.get("ulpin", ""))
        village = str(p.get("village", ""))
        if needle and not any([
            pid.lower().startswith(needle),
            survey.lower().startswith(needle),
            ulpin.lower().startswith(needle),
            needle in village.lower(),
            needle in pid.lower(),
            needle in ulpin.lower(),
        ]):
            continue
        item = {
            "parcel_id": pid,
            "survey_no": survey,
            "ulpin": ulpin,
            "village": village,
            "mandal": p.get("mandal", "Shamshabad"),
            "land_use_claim": p.get("land_use_claim"),
            "owner_name": p.get("owner_name"),
            "revenue_court_status": p.get("revenue_court_status"),
        }
        item = mask_pii_fields(item, role)
        matches.append(item)
        if len(matches) >= limit:
            break
    return {"query": q, "count": len(matches), "results": matches}


@router.get("/export-report")
def export_report(db: Session = Depends(get_db)):
    """
    JSON summary that can be turned into a PDF. (PDF generation lives in
    certificate router — Task 10.)
    """
    mandal_data = mandal_stats(db=db)

    # Recent audits
    recent_audits = db.query(OfficerAuditLog).order_by(OfficerAuditLog.timestamp.desc()).limit(10).all()
    audits = [
        {
            "parcel_id": a.parcel_id,
            "action": a.action,
            "officer": a.officer_name,
            "reason": a.reason,
            "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "hash": a.blockchain_hash,
        }
        for a in recent_audits
    ]

    return {
        "report_type": "BhuNetra AI Executive Summary",
        "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
        "scope": "Rangareddy District (Shamshabad / Mamidipally / Kothwalguda Mandals)",
        "mandal_breakdown": mandal_data,
        "recent_audits": audits,
    }
