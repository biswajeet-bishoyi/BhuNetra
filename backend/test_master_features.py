import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from services.title_chain_service import normalize_name, fuzzy_name_match, fuzzy_survey_match, reconstruct_title_chain, check_duplicate_claim
from services.triple_comparison_service import compute_triple_comparison
from services.evidence_package_service import generate_evidence_package_pdf

def test_fuzzy_name_matching():
    print("Testing Fuzzy Name Matching...")
    # Exact
    score1, desc1 = fuzzy_name_match("Rahul Mohanty", "Rahul Mohanty")
    assert score1 >= 0.95, f"Expected >= 0.95, got {score1}"
    
    # Abbreviation / Initial
    score2, desc2 = fuzzy_name_match("Rahul Mohanty", "R. Mohanty")
    assert score2 >= 0.85, f"Expected >= 0.85, got {score2}"
    
    # Honorifics
    score3, desc3 = fuzzy_name_match("Shri Ramesh Chandra Sharma", "Ramesh Chandra Sharma")
    assert score3 >= 0.90, f"Expected >= 0.90, got {score3}"
    
    # Different names
    score4, desc4 = fuzzy_name_match("Rahul Mohanty", "Amit Mohanty")
    assert score4 < 0.65, f"Expected < 0.65, got {score4}"
    print(f"[PASS] Name matching passed: (R. Mohanty vs Rahul Mohanty -> {score2}, Amit vs Rahul -> {score4})")


def test_title_chain_reconstruction():
    print("Testing Title Chain Reconstruction...")
    docs = [
        {"year": 1988, "owner_name": "Ramesh Mohanty", "father_name": "Late Jagannath Mohanty", "document_type": "Ancestral Partition Deed", "survey_no": "45/0", "registration_no": "REG-1988-104", "area_sqm": 1250.0},
        {"year": 2004, "owner_name": "Suresh Mohanty", "father_name": "Ramesh Mohanty", "document_type": "Succession Mutation", "survey_no": "45/0", "registration_no": "MUT-2004-88", "area_sqm": 1250.0},
        {"year": 2026, "owner_name": "Sudrusti Sethi", "father_name": "P. Sethi", "document_type": "Registered Sale Deed", "survey_no": "45/0", "registration_no": "REG-2026-OD-8841", "area_sqm": 1250.0}
    ]
    res = reconstruct_title_chain(docs)
    assert res["is_continuous"] == True, "Expected continuous chain"
    assert res["continuity_score"] >= 80.0, f"Expected >= 80, got {res['continuity_score']}"
    assert len(res["chain"]) == 3, f"Expected 3 nodes, got {len(res['chain'])}"
    print(f"[PASS] Title chain reconstruction passed: Score {res['continuity_score']}%, Status: {res['status']}")


def test_duplicate_claim_detection():
    print("Testing Duplicate Claim Detection...")
    existing_repo = [
        {
            "parcel_id": "P-OD-102",
            "survey_no": "45/0",
            "khata_no": "102",
            "village": "Chhatrapur",
            "latest_verified_owner": "Sudrusti Sethi",
            "latest_registration_no": "REG-2026-OD-8841"
        }
    ]
    
    # Conflicting upload by Amit Mohanty on same survey #45/0
    new_claim = {
        "survey_no": "45/0",
        "khata_no": "102",
        "village": "Chhatrapur",
        "owner_name": "Amit Mohanty",
        "registration_no": "REG-2026-DISPUTE-99"
    }
    
    alert = check_duplicate_claim(new_claim, existing_repo)
    assert alert is not None, "Expected conflict alert"
    assert alert["is_conflict"] == True
    assert alert["conflict_score"] >= 85.0
    print(f"[PASS] Duplicate claim detected successfully: {alert['conflict_score']}% conflict on Survey #{alert['survey_no']}")


def test_triple_comparison():
    print("Testing 3-Way AI Comparison Matrix & Ownership Confidence...")
    reg_doc = {"owner_name": "Sudrusti Sethi", "father_name": "P. Sethi", "survey_no": "45/0", "area_sqm": "1250", "village": "Chhatrapur"}
    rev_doc = {"owner_name": "Sudrusti Sethi", "father_name": "P. Sethi", "survey_no": "45/0", "area_sqm": "1250", "village": "Chhatrapur"}
    sur_doc = {"owner_name": "S. Sethi", "father_name": "P. Sethi", "survey_no": "45/0", "area_sqm": "1248", "village": "Chhatrapur"}
    
    res = compute_triple_comparison(reg_doc, rev_doc, sur_doc, historical_chain_continuous=True, has_duplicate_claim=False)
    assert res["overall_confidence"] >= 90.0, f"Expected >= 90.0, got {res['overall_confidence']}"
    assert len(res["comparison_matrix"]) == 5, f"Expected 5 fields, got {len(res['comparison_matrix'])}"
    print(f"[PASS] Triple comparison passed: Confidence {res['overall_confidence']}%, Recommendation: {res['recommendation']}")


def test_pdf_evidence_generation():
    print("Testing Section 65B Court-Ready Evidence PDF generation...")
    p_data = {
        "parcel_id": "P-OD-102",
        "survey_no": "45/0",
        "khata_no": "102",
        "ulpin": "OD-GM-450",
        "owner_name": "Sudrusti Sethi",
        "father_or_husband": "P. Sethi",
        "village": "Chhatrapur",
        "district": "Ganjam",
        "state": "Odisha",
        "claimed_area_sqm": 1250.0,
        "actual_area_sqm": 1248.0
    }
    
    triple_comp = {
        "overall_confidence": 94.2,
        "recommendation": "Title evidence strongly supported across Registration, Revenue, and Survey records.",
        "duplicate_claim": "None",
        "historical_chain": "Verified",
        "comparison_matrix": [
            {"field": "owner_name", "label": "Owner Name", "registration": "Sudrusti Sethi", "revenue": "Sudrusti Sethi", "survey": "S. Sethi", "match_pct": 98.0, "status": "EXACT_MATCH", "notes": "Full alignment"},
            {"field": "survey_no", "label": "Survey No.", "registration": "45/0", "revenue": "45/0", "survey": "45/0", "match_pct": 100.0, "status": "EXACT_MATCH", "notes": "Identical"}
        ]
    }
    
    title_chain = {
        "chain": [
            {"year": 1988, "date": "1988-04-14", "document_type": "Partition Deed", "owner_name": "Ramesh Mohanty", "father_name": "Late J. Mohanty", "registration_no": "REG-1988-104", "survey_no": "45/0"},
            {"year": 2026, "date": "2026-08-15", "document_type": "Sale Deed", "owner_name": "Sudrusti Sethi", "father_name": "P. Sethi", "registration_no": "REG-2026-OD-8841", "survey_no": "45/0"}
        ]
    }
    
    pdf_bytes, sha_hash, report_id = generate_evidence_package_pdf(
        parcel_data=p_data,
        triple_comparison=triple_comp,
        title_chain=title_chain,
        officer_name="Tahsildar Chhatrapur",
        officer_notes="Evidence verified with DILRMP digitized cadastre."
    )
    
    assert len(pdf_bytes) > 2000, "PDF bytes should be generated"
    assert sha_hash.startswith("0x"), "SHA-256 hash must be generated"
    assert "BHUNETRA-EVD-65B" in report_id, "Report ID must have standard prefix"
    print(f"[PASS] PDF Evidence generation passed: {len(pdf_bytes)} bytes, SHA-256: {sha_hash[:18]}...")


if __name__ == "__main__":
    print("==================================================")
    print("BhuNetra AI — Master Features Automated Test Suite")
    print("==================================================")
    test_fuzzy_name_matching()
    test_title_chain_reconstruction()
    test_duplicate_claim_detection()
    test_triple_comparison()
    test_pdf_evidence_generation()
    print("==================================================")
    print("ALL 5 CORE FEATURE TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")
