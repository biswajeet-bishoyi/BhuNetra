import math
import difflib
from typing import Dict, Any, List, Tuple
from services.title_chain_service import fuzzy_name_match, fuzzy_survey_match, normalize_name

def evaluate_field_match(
    field_name: str,
    val_reg: Any,
    val_rev: Any,
    val_sur: Any
) -> Dict[str, Any]:
    """
    Compares a specific field across Registration, Revenue, and Survey records.
    Assigns match level: EXACT_MATCH (green), MINOR_MISMATCH (yellow), CONFLICT (red).
    """
    s_reg = str(val_reg or "").strip()
    s_rev = str(val_rev or "").strip()
    s_sur = str(val_sur or "").strip()
    
    # 1. Owner Name & Father Name Fuzzy Evaluation
    if field_name in ["owner_name", "father_name"]:
        sim_reg_rev, desc_reg_rev = fuzzy_name_match(s_reg, s_rev)
        sim_reg_sur, desc_reg_sur = fuzzy_name_match(s_reg, s_sur)
        sim_rev_sur, _ = fuzzy_name_match(s_rev, s_sur)
        
        avg_sim = (sim_reg_rev + sim_reg_sur + sim_rev_sur) / 3.0 if (s_sur and s_rev and s_reg) else max(sim_reg_rev, sim_reg_sur)
        
        if avg_sim >= 0.90:
            status = "EXACT_MATCH"
            color = "green"
            notes = "Full alignment across all sources with consistent spelling."
        elif avg_sim >= 0.70:
            status = "MINOR_MISMATCH"
            color = "yellow"
            notes = f"Phonetic or initial abbreviation variant ({desc_reg_rev} / {desc_reg_sur})."
        else:
            status = "CONFLICT"
            color = "red"
            notes = f"Discrepancy in party identity: Registration '{s_reg}' vs Revenue '{s_rev}' vs Survey '{s_sur}'."
            
        return {
            "field": field_name,
            "label": "Owner Name" if field_name == "owner_name" else "Father / Husband Name",
            "registration": s_reg or "—",
            "revenue": s_rev or "—",
            "survey": s_sur or "—",
            "match_pct": round(avg_sim * 100, 1),
            "status": status,
            "color": color,
            "notes": notes
        }

    # 2. Survey / Khasra Number Evaluation
    elif field_name == "survey_no":
        m1, score1, desc1 = fuzzy_survey_match(s_reg, s_rev)
        m2, score2, desc2 = fuzzy_survey_match(s_reg, s_sur)
        
        avg_score = (score1 + score2) / 2.0
        if avg_score >= 0.95:
            status = "EXACT_MATCH"
            color = "green"
            notes = "Survey and khasra numbers identical in all 3 documents."
        elif avg_score >= 0.75:
            status = "MINOR_MISMATCH"
            color = "yellow"
            notes = f"Sub-division indicator variation: {desc1}"
        else:
            status = "CONFLICT"
            color = "red"
            notes = f"Survey mismatch: Reg #{s_reg} vs Revenue #{s_rev} vs Survey #{s_sur}."
            
        return {
            "field": field_name,
            "label": "Survey / Khasra No.",
            "registration": s_reg or "—",
            "revenue": s_rev or "—",
            "survey": s_sur or "—",
            "match_pct": round(avg_score * 100, 1),
            "status": status,
            "color": color,
            "notes": notes
        }

    # 3. Area Extent Evaluation
    elif field_name in ["area_sqm", "claimed_area_sqm"]:
        try:
            a_reg = float(val_reg or 0.0)
            a_rev = float(val_rev or 0.0)
            a_sur = float(val_sur or 0.0)
        except (ValueError, TypeError):
            a_reg, a_rev, a_sur = 0.0, 0.0, 0.0
            
        areas = [a for a in [a_reg, a_rev, a_sur] if a > 0]
        if not areas:
            avg_diff_pct = 0.0
            match_pct = 100.0
            status = "EXACT_MATCH"
            color = "green"
            notes = "No numeric discrepancies found."
        else:
            max_a = max(areas)
            min_a = min(areas)
            diff_ratio = (max_a - min_a) / max_a if max_a > 0 else 0.0
            match_pct = max(0.0, 100.0 - (diff_ratio * 100.0))
            
            if diff_ratio <= 0.05:
                status = "EXACT_MATCH"
                color = "green"
                notes = f"Area extents match within statutory ±5% tolerance ({round(diff_ratio*100, 1)}% variance)."
            elif diff_ratio <= 0.15:
                status = "MINOR_MISMATCH"
                color = "yellow"
                notes = f"Minor area variance of {round(diff_ratio*100, 1)}% between cadastral survey and registered extent."
            else:
                status = "CONFLICT"
                color = "red"
                notes = f"Major boundary or area conflict: {round(diff_ratio*100, 1)}% difference ({min_a} sqm vs {max_a} sqm)."
                
        return {
            "field": "area_sqm",
            "label": "Recorded Extent (sq.m)",
            "registration": f"{a_reg:,.1f}" if a_reg else "—",
            "revenue": f"{a_rev:,.1f}" if a_rev else "—",
            "survey": f"{a_sur:,.1f}" if a_sur else "—",
            "match_pct": round(match_pct, 1),
            "status": status,
            "color": color,
            "notes": notes
        }

    # 4. Village & Location Evaluation
    else:
        n_reg = normalize_name(s_reg)
        n_rev = normalize_name(s_rev)
        n_sur = normalize_name(s_sur)
        
        sim = difflib.SequenceMatcher(None, n_reg, n_rev).ratio()
        if n_sur:
            sim = (sim + difflib.SequenceMatcher(None, n_reg, n_sur).ratio()) / 2.0
            
        if sim >= 0.90:
            status = "EXACT_MATCH"
            color = "green"
            notes = "Administrative jurisdiction and village name align."
        elif sim >= 0.70:
            status = "MINOR_MISMATCH"
            color = "yellow"
            notes = "Slight phonetic spelling variation in village name."
        else:
            status = "CONFLICT"
            color = "red"
            notes = f"Village mismatch: '{s_reg}' vs '{s_rev}'."
            
        return {
            "field": field_name,
            "label": "Village / Tehsil",
            "registration": s_reg or "—",
            "revenue": s_rev or "—",
            "survey": s_sur or "—",
            "match_pct": round(sim * 100, 1),
            "status": status,
            "color": color,
            "notes": notes
        }


def compute_triple_comparison(
    registration_doc: Dict[str, Any],
    revenue_doc: Dict[str, Any],
    survey_doc: Dict[str, Any],
    historical_chain_continuous: bool = True,
    has_duplicate_claim: bool = False
) -> Dict[str, Any]:
    """
    Executes Feature 7 (Three-Way AI Comparison) & Feature 8 (Ownership Confidence Engine).
    
    Weights:
    - Registration Document: 35%
    - Revenue Record (RoR): 25%
    - Survey Cadastral Report: 25%
    - Historical Title Chain: 15%
    """
    matrix = []
    
    # 1. Owner Name
    m_owner = evaluate_field_match("owner_name", registration_doc.get("owner_name"), revenue_doc.get("owner_name"), survey_doc.get("owner_name"))
    matrix.append(m_owner)
    
    # 2. Father Name
    m_father = evaluate_field_match("father_name", registration_doc.get("father_or_husband") or registration_doc.get("father_name"), revenue_doc.get("father_or_husband") or revenue_doc.get("father_name"), survey_doc.get("father_or_husband") or survey_doc.get("father_name"))
    matrix.append(m_father)
    
    # 3. Survey Number
    m_survey = evaluate_field_match("survey_no", registration_doc.get("survey_no") or registration_doc.get("khasra_no"), revenue_doc.get("survey_no") or revenue_doc.get("khasra_no"), survey_doc.get("survey_no") or survey_doc.get("khasra_no"))
    matrix.append(m_survey)
    
    # 4. Area
    m_area = evaluate_field_match("area_sqm", registration_doc.get("claimed_area_sqm") or registration_doc.get("area_sqm"), revenue_doc.get("claimed_area_sqm") or revenue_doc.get("area_sqm"), survey_doc.get("claimed_area_sqm") or survey_doc.get("area_sqm"))
    matrix.append(m_area)
    
    # 5. Village
    m_village = evaluate_field_match("village", registration_doc.get("village"), revenue_doc.get("village"), survey_doc.get("village"))
    matrix.append(m_village)
    
    # Calculate source scores
    # Registration match score based on internal completeness & alignment with Revenue
    reg_score = (m_owner["match_pct"] * 0.4) + (m_survey["match_pct"] * 0.3) + (m_area["match_pct"] * 0.3)
    rev_score = (m_owner["match_pct"] * 0.35) + (m_father["match_pct"] * 0.25) + (m_survey["match_pct"] * 0.2) + (m_village["match_pct"] * 0.2)
    sur_score = (m_survey["match_pct"] * 0.4) + (m_area["match_pct"] * 0.4) + (m_owner["match_pct"] * 0.2)
    chain_score = 100.0 if historical_chain_continuous else 40.0
    
    # Weighted Ownership Confidence Assessment
    # Weights: 35% Registration, 25% Revenue, 25% Survey, 15% Title Chain
    raw_confidence = (reg_score * 0.35) + (rev_score * 0.25) + (sur_score * 0.25) + (chain_score * 0.15)
    
    # Penalty for duplicate claim
    if has_duplicate_claim:
        raw_confidence = min(raw_confidence * 0.5, 45.0)
        
    overall_confidence = max(5.0, min(99.4, round(raw_confidence, 1)))
    
    # Generate Evidence Explanations & Officer Recommendation
    evidence_points = []
    if m_owner["match_pct"] >= 90:
        evidence_points.append("Registered owner name matches Revenue and Survey records.")
    elif m_owner["match_pct"] >= 70:
        evidence_points.append(f"Owner name has slight abbreviation/phonetic variant: {m_owner['notes']}")
    else:
        evidence_points.append(f"Warning: Discrepancy in recorded owner identity between documents.")
        
    if m_survey["match_pct"] >= 90:
        evidence_points.append("Survey / Khasra number is identical across all three records.")
    else:
        evidence_points.append(f"Notice: {m_survey['notes']}")
        
    if m_area["match_pct"] >= 90:
        evidence_points.append("Measured plot extent aligns within statutory error margins.")
    else:
        evidence_points.append(f"Boundary Notice: {m_area['notes']}")
        
    if historical_chain_continuous:
        evidence_points.append("Historical title chain is intact with verified predecessor lineage.")
    else:
        evidence_points.append("Historical ownership chain exhibits unverified transfers or time gaps.")
        
    if has_duplicate_claim:
        evidence_points.append("CRITICAL: Conflicting duplicate ownership claim detected on this survey number.")
        recommendation = "Reject automated clearance. Issue formal notice under Section 144/Revenue Code for field inquiry."
        decision_tag = "HEARING_REQUIRED"
    elif overall_confidence >= 85.0:
        recommendation = "Title evidence strongly supported across Registration, Revenue, and Survey records. Proceed with standard verification."
        decision_tag = "READY_FOR_APPROVAL"
    elif overall_confidence >= 65.0:
        recommendation = "Moderate confidence. Minor spelling or area discrepancies detected. Officer manual review advised."
        decision_tag = "OFFICER_REVIEW_ADVISED"
    else:
        recommendation = "Low ownership confidence. Significant conflicts between registered deed and revenue records. Call for hearing."
        decision_tag = "CALL_FOR_HEARING"
        
    return {
        "overall_confidence": overall_confidence,
        "registration_match": round(reg_score, 1),
        "revenue_match": round(rev_score, 1),
        "survey_match": round(sur_score, 1),
        "historical_chain": "Verified" if historical_chain_continuous else "Incomplete",
        "duplicate_claim": "Detected" if has_duplicate_claim else "None",
        "weights": {
            "registration": "35%",
            "revenue_record": "25%",
            "survey_report": "25%",
            "historical_chain": "15%"
        },
        "comparison_matrix": matrix,
        "evidence_points": evidence_points,
        "recommendation": recommendation,
        "decision_tag": decision_tag,
        "legal_position": "AI-assisted ownership confidence assessment for Revenue Officer decision support (IT Act 2000 Section 65B); statutory title remains governed by the Registration Act 1908."
    }
