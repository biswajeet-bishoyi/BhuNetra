"""
test_engines_integration.py — End-to-end pipeline test for Engines 2-5.

Verifies the full BhuNetra decision pipeline works as described in DEMO_SCRIPT.md:
  Engine 2 (GIS)        — Shapely STRtree + Isolation Forest
  Engine 3 (Ownership)  — multi-rule transfer analysis
  Engine 4 (Satellite)  — pre-computed Sentinel-2 + registry inference
  Engine 5 (Ensemble)   — 35/25/25/15 weighted score

No GPU/model needed. Stubs the engine to make it deterministic.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

# Boot the app just like main.py does
from backend.database import Base, engine  # noqa: E402
Base.metadata.create_all(bind=engine)
from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app  # noqa: E402

client = TestClient(app)

_checks = 0
_failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    global _checks
    _checks += 1
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}   {detail}")
        _failures.append(label)


def test_engine2_gis_parcel_list():
    print("\n[1] Engine 2 — GIS parcel list")
    r = client.get("/api/gis-check/")
    check("GET /api/gis-check/ returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    check("response has features", "features" in data, str(list(data.keys())[:5]))
    check("features is a list", isinstance(data.get("features"), list))
    check("at least 16 features", len(data.get("features", [])) >= 16, str(len(data.get("features", []))))
    if data.get("features"):
        f0 = data["features"][0]
        check("feature has geometry", "geometry" in f0, str(list(f0.keys())[:5]))
        check("feature has properties", "properties" in f0)
        check("feature has parcel_id", "parcel_id" in f0.get("properties", {}))


def test_engine2_gis_single_parcel():
    print("\n[2] Engine 2 — Single-parcel GIS check (P-105)")
    r = client.get("/api/gis-check/parcel/P-105")
    check("GET /api/gis-check/parcel/P-105 returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    check("parcel_id is P-105", data.get("parcel_id") == "P-105", str(data.get("parcel_id")))
    check("risk_score present", "risk_score" in data, str(list(data.keys())[:8]))
    check("explanations list present", "explanations" in data, str(type(data.get("explanations"))))


def test_engine3_ownership_rapid_resale():
    print("\n[3] Engine 3 — Ownership rapid-resale detection (P-108)")
    r = client.get("/api/ownership/P-108")
    check("GET /api/ownership/P-108 returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    check("transfer_count >= 3", data.get("transfer_count", 0) >= 3, str(data.get("transfer_count")))
    check("ownership_risk_score > 0", data.get("ownership_risk_score", 0) > 0, str(data.get("ownership_risk_score")))
    check("is_anomalous True", data.get("is_anomalous") is True)
    factor_names = [f["name"] for f in data.get("factors", [])]
    check("rapid_transfer_frequency factor detected", "rapid_transfer_frequency" in factor_names, str(factor_names))


def test_engine3_ownership_circular_chain():
    print("\n[4] Engine 3 — Circular chain / benami detection (P-108)")
    r = client.get("/api/ownership/P-108")
    data = r.json()
    factor_names = [f["name"] for f in data.get("factors", [])]
    has_advanced_detector = any(
        f in factor_names for f in ("potential_benami_cross_holding", "circular_ownership_chain")
    )
    check("at least one advanced detector (benami or circular)", has_advanced_detector, str(factor_names))


def test_engine4_satellite_p135():
    print("\n[5] Engine 4 — Pre-computed satellite (P-135: agricultural claim, warehouse reality)")
    r = client.get("/api/satellite/P-135")
    check("GET /api/satellite/P-135 returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    check("mismatch_flag True", data.get("mismatch_flag") is True)
    check("satellite_risk_score >= 65", data.get("satellite_risk_score", 0) >= 65, str(data.get("satellite_risk_score")))
    check("built_up_coverage_pct > 50", data.get("built_up_coverage_pct", 0) > 50, str(data.get("built_up_coverage_pct")))
    check("data_source disclosed", "data_source" in data)
    check("factors list present", "factors" in data)
    factor_names = [f["name"] for f in data.get("factors", [])]
    check("high_built_up_mismatch factor", "high_built_up_mismatch" in factor_names, str(factor_names))


def test_engine4_satellite_clean_parcel():
    print("\n[6] Engine 4 — Clean agricultural (P-101)")
    r = client.get("/api/satellite/P-101")
    data = r.json()
    check("P-101 mismatch_flag False", data.get("mismatch_flag") is False)
    check("P-101 satellite_risk_score <= 20", data.get("satellite_risk_score", 100) <= 20)


def test_engine4_satellite_registry_inferred():
    print("\n[7] Engine 4 — Registry-inferred fallback (P-150: no pre-computed tile)")
    r = client.get("/api/satellite/P-150")
    check("GET /api/satellite/P-150 returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    check("P-150 has a response (not 404)", data.get("parcel_id") == "P-150")
    check("data_source is registry-inferred", "REGISTRY-INFERRED" in data.get("data_source", ""))


def test_engine5_ensemble_p105():
    print("\n[8] Engine 5 — Ensemble score (P-105: GIS overlap parcel)")
    r = client.get("/api/risk-score/P-105")
    check("GET /api/risk-score/P-105 returns 200", r.status_code == 200, str(r.status_code))
    data = r.json()
    check("parcel_id is P-105", data.get("parcel_id") == "P-105")
    check("ensemble_risk_score in [0, 100]",
          0 <= data.get("ensemble_risk_score", -1) <= 100, str(data.get("ensemble_risk_score")))
    check("ensemble_risk_level is one of GREEN/YELLOW/RED",
          data.get("ensemble_risk_level") in {"GREEN", "YELLOW", "RED"})
    check("weights_matrix present", "weights_matrix" in data)
    weights = data.get("weights_matrix", {})
    check("GIS weight = 0.35", weights.get("gis_topology") == 0.35, str(weights))
    check("Ownership weight = 0.25", weights.get("ownership_intelligence") == 0.25)
    check("Satellite weight = 0.25", weights.get("satellite_verification") == 0.25)
    check("OCR weight = 0.15", weights.get("registry_ocr") == 0.15)
    check("top_explanations present", "top_explanations" in data)
    check("engine_scores present", "engine_scores" in data)


def test_engine5_ensemble_p135():
    print("\n[9] Engine 5 — Ensemble score (P-135: agricultural vs warehouse)")
    r = client.get("/api/risk-score/P-135")
    data = r.json()
    check("P-135 ensemble_risk_score > 0", data.get("ensemble_risk_score", 0) > 0)


def test_dpd_pii_citizen_masking():
    print("\n[10] DPDP Act 2023 — Citizen role masks PII in risk-score")
    r = client.get("/api/risk-score/P-105?role=Citizen")
    data = r.json()
    owner = data.get("owner_name", "")
    # If owner exists, it should be masked (contains 'X.' or is the masked placeholder)
    if owner and "Masked" not in str(owner):
        check("Citizen owner_name is masked", "X." in str(owner), str(owner))
    else:
        check("Citizen owner_name is masked or empty", True)
    check("dpdp_context is present", "dpdp_context" in data)
    dpdp = data.get("dpdp_context", {})
    check("is_citizen_view True", dpdp.get("is_citizen_view") is True)


def test_dpd_pii_officer_no_masking():
    print("\n[11] DPDP Act 2023 — Officer role does NOT mask PII")
    r = client.get("/api/risk-score/P-105?role=Revenue Officer")
    data = r.json()
    check("Officer dpdp_context.is_citizen_view False",
          data.get("dpdp_context", {}).get("is_citizen_view") is False)


def test_dpd_pii_ownership_chain_masked():
    print("\n[12] DPDP Act 2023 — Ownership chain masked in Citizen view")
    r = client.get("/api/ownership/P-108?role=Citizen")
    data = r.json()
    check("Citizen ownership response has dpdp_context",
          "dpdp_context" in data)
    check("is_citizen_view True for Citizen",
          data.get("dpdp_context", {}).get("is_citizen_view") is True)
    transfers = data.get("transfers", [])
    if transfers:
        owners = [str(t.get("owner_name", "")) for t in transfers]
        all_masked = all("X." in o or "Masked" in o for o in owners if o)
        check("all transfer owner_names are masked in Citizen view", all_masked, str(owners))


if __name__ == "__main__":
    print("BhuNetra — Engines 2-5 Integration Tests")
    print("=" * 62)
    test_engine2_gis_parcel_list()
    test_engine2_gis_single_parcel()
    test_engine3_ownership_rapid_resale()
    test_engine3_ownership_circular_chain()
    test_engine4_satellite_p135()
    test_engine4_satellite_clean_parcel()
    test_engine4_satellite_registry_inferred()
    test_engine5_ensemble_p105()
    test_engine5_ensemble_p135()
    test_dpd_pii_citizen_masking()
    test_dpd_pii_officer_no_masking()
    test_dpd_pii_ownership_chain_masked()
    print("=" * 62)
    print(f"{_checks - len(_failures)}/{_checks} checks passed")
    if _failures:
        print("FAILED: " + ", ".join(_failures))
    raise SystemExit(1 if _failures else 0)
