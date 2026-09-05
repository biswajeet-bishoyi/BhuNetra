import re
import json
import difflib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

def normalize_name(name: str) -> str:
    """Normalize Indian names removing titles and extra spaces."""
    if not name:
        return ""
    clean = re.sub(r'(?i)\b(sri|shri|smt|smti|late|mr|mrs|dr|pattadar|khatedar)\b', '', name)
    clean = re.sub(r'[^a-zA-Z\s]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip().lower()
    return clean

def fuzzy_name_match(name1: str, name2: str) -> Tuple[float, str]:
    """
    Fuzzy match names taking into account initials, abbreviations,
    spelling variations (e.g., 'Rahul Mohanty' vs 'R. Mohanty' vs 'Rahul M.').
    """
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    
    if not n1 or not n2:
        return 0.0, "Missing name data"
    
    if n1 == n2:
        return 1.0, "Exact full name match"
    
    parts1 = n1.split()
    parts2 = n2.split()
    
    # Check initial & word-level matching
    if len(parts1) >= 2 and len(parts2) >= 2:
        last1 = parts1[-1]
        last2 = parts2[-1]
        first1 = parts1[0]
        first2 = parts2[0]
        
        # Surnames match
        if last1 == last2:
            if first1 == first2:
                return 0.98, "First and last names match"
            # Initial check
            if (len(first1) == 1 and first2.startswith(first1)) or (len(first2) == 1 and first1.startswith(first2)):
                return 0.92, f"Initial '{first1[0].upper()}' matches full name '{first2 if len(first1)==1 else first1}' with identical surname"
            
            # Evaluate first name similarity
            first_sim = difflib.SequenceMatcher(None, first1, first2).ratio()
            if first_sim >= 0.75:
                return round(0.5 + first_sim * 0.45, 2), "Surname identical and first name phonetically/spelling similar"
            else:
                return round(first_sim * 0.4 + 0.15, 2), f"Different first names ('{first1.capitalize()}' vs '{first2.capitalize()}') sharing same surname"
    
    ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
    if ratio >= 0.85:
        return round(ratio, 2), "High string similarity match"
    elif ratio >= 0.70:
        return round(ratio, 2), "Partial name similarity"
    else:
        return round(ratio, 2), "Names differ"


def fuzzy_survey_match(s1: str, s2: str) -> Tuple[bool, float, str]:
    """Compare survey / khasra numbers accommodating sub-division slashes (45/1 vs 45/1A)."""
    if not s1 or not s2:
        return False, 0.0, "Missing survey number"
    
    clean1 = str(s1).strip().upper().replace(" ", "")
    clean2 = str(s2).strip().upper().replace(" ", "")
    
    if clean1 == clean2:
        return True, 1.0, "Exact survey number match"
    
    # Base survey match (e.g. 45/1 vs 45/1A or 45 vs 45/0)
    base1 = clean1.split('/')[0]
    base2 = clean2.split('/')[0]
    
    if base1 == base2:
        return True, 0.85, f"Sub-division match on base survey #{base1}"
    
    return False, 0.0, f"Survey number mismatch ({clean1} vs {clean2})"


def reconstruct_title_chain(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Reconstructs chronological title chain from a list of uploaded property documents.
    Detects continuity, broken links, missing transfers, area shifts, and suspicious jumps.
    """
    if not documents:
        return {
            "status": "EMPTY",
            "chain": [],
            "continuity_score": 0.0,
            "is_continuous": False,
            "reasons": ["No title documents provided."],
            "timeline": []
        }
    
    # Sort documents by date / year
    def get_doc_year(d):
        if d.get("deed_year"):
            try:
                return int(d["deed_year"])
            except:
                pass
        if d.get("deed_date"):
            try:
                return int(str(d["deed_date"])[:4])
            except:
                pass
        return 2026 # Default latest
    
    sorted_docs = sorted(documents, key=get_doc_year)
    
    chain_nodes = []
    gaps = []
    reasons = []
    continuity_score = 100.0
    
    for i, doc in enumerate(sorted_docs):
        year = get_doc_year(doc)
        owner = doc.get("owner_name") or "Unknown Party"
        father = doc.get("father_name") or doc.get("father_or_husband") or ""
        doc_type = doc.get("document_type") or ("Sale Deed" if i == len(sorted_docs)-1 else "Ancestral Record")
        survey = doc.get("survey_no") or doc.get("khasra_no") or ""
        area = float(doc.get("area_sqm") or doc.get("claimed_area_sqm") or 0.0)
        
        node = {
            "order_index": i + 1,
            "year": year,
            "date": doc.get("deed_date") or f"{year}-01-01",
            "owner_name": owner,
            "father_name": father,
            "document_type": doc_type,
            "survey_no": survey,
            "khata_no": doc.get("khata_no") or doc.get("khatian_no") or "",
            "village": doc.get("village") or "",
            "area_sqm": area,
            "registration_no": doc.get("registration_no") or doc.get("deed_registration_no") or f"REG-{year}-{i+101}",
            "is_ancestral": bool(doc.get("is_ancestral", i < len(sorted_docs) - 1))
        }
        chain_nodes.append(node)
    
    # Analyze transitions between consecutive nodes
    for i in range(len(chain_nodes) - 1):
        prev_node = chain_nodes[i]
        curr_node = chain_nodes[i + 1]
        
        time_gap = curr_node["year"] - prev_node["year"]
        
        # 1. Check time gap
        if time_gap > 35:
            continuity_score -= 20.0
            gap_msg = f"Large unrecorded time gap of {time_gap} years between {prev_node['year']} ({prev_node['owner_name']}) and {curr_node['year']} ({curr_node['owner_name']})."
            gaps.append(gap_msg)
            reasons.append(gap_msg)
        elif time_gap < 0:
            continuity_score -= 30.0
            gap_msg = f"Chronological anomaly: {curr_node['document_type']} ({curr_node['year']}) predates {prev_node['document_type']} ({prev_node['year']})."
            gaps.append(gap_msg)
            reasons.append(gap_msg)
        
        # 2. Check Lineage / Transfer link (Father name matching previous owner or legal transfer)
        prev_owner = prev_node["owner_name"]
        curr_father = curr_node["father_name"]
        curr_owner = curr_node["owner_name"]
        
        if curr_father:
            match_score, match_desc = fuzzy_name_match(prev_owner, curr_father)
            if match_score >= 0.85:
                reasons.append(f"Clear genealogical succession verified: {curr_owner} is heir/son of {prev_owner} ({match_desc}).")
            else:
                # Check direct purchase / transfer
                reasons.append(f"Title transfer from {prev_owner} to {curr_owner} via {curr_node['document_type']} ({curr_node['year']}).")
        else:
            reasons.append(f"Title transfer from {prev_owner} to {curr_owner} via {curr_node['document_type']} ({curr_node['year']}).")
            
        # 3. Check Area Consistency
        if prev_node["area_sqm"] > 0 and curr_node["area_sqm"] > 0:
            area_diff = abs(curr_node["area_sqm"] - prev_node["area_sqm"])
            diff_ratio = area_diff / prev_node["area_sqm"]
            if diff_ratio > 0.25:
                continuity_score -= 15.0
                reasons.append(f"Area extent changed by {round(diff_ratio*100, 1)}% ({prev_node['area_sqm']} sqm → {curr_node['area_sqm']} sqm) without documented partition.")
        
        # 4. Check Survey Number Consistency
        if prev_node["survey_no"] and curr_node["survey_no"]:
            s_match, s_score, s_desc = fuzzy_survey_match(prev_node["survey_no"], curr_node["survey_no"])
            if not s_match:
                continuity_score -= 25.0
                reasons.append(f"Survey number mismatch across chain: #{prev_node['survey_no']} in {prev_node['year']} vs #{curr_node['survey_no']} in {curr_node['year']}.")
    
    continuity_score = max(0.0, min(100.0, continuity_score))
    is_continuous = len(gaps) == 0 and continuity_score >= 70.0
    
    status_text = "Ownership chain appears continuous." if is_continuous else "Ownership chain incomplete or exhibits unverified gaps."
    
    return {
        "status": status_text,
        "is_continuous": is_continuous,
        "continuity_score": round(continuity_score, 1),
        "total_documents": len(chain_nodes),
        "chain": chain_nodes,
        "gaps": gaps,
        "reasons": reasons,
        "timeline_summary": [
            f"{n['year']} {n['document_type']} ({n['owner_name']})" for n in chain_nodes
        ]
    }


def check_duplicate_claim(
    new_claim: Dict[str, Any],
    existing_repo: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Compares a new deed upload against the permanent property repository.
    If matching Survey No, Khata, Village, or ULPIN is found with a conflicting owner,
    computes conflict score and generates an alert.
    """
    new_survey = str(new_claim.get("survey_no") or new_claim.get("khasra_no") or "").strip()
    new_khata = str(new_claim.get("khata_no") or new_claim.get("khatian_no") or "").strip()
    new_village = str(new_claim.get("village") or "").strip().lower()
    new_owner = str(new_claim.get("owner_name") or "").strip()
    new_reg = str(new_claim.get("registration_no") or new_claim.get("deed_registration_no") or "").strip()
    
    if not new_survey or not new_owner:
        return None
    
    for record in existing_repo:
        rec_survey = str(record.get("survey_no") or "").strip()
        rec_village = str(record.get("village") or "").strip().lower()
        rec_owner = str(record.get("latest_verified_owner") or record.get("owner_name") or "").strip()
        
        # Check if same parcel
        s_match, s_score, _ = fuzzy_survey_match(new_survey, rec_survey)
        v_match = (not new_village or not rec_village or new_village == rec_village or difflib.SequenceMatcher(None, new_village, rec_village).ratio() > 0.8)
        
        if s_match and v_match:
            # Check owner identity
            name_sim, desc = fuzzy_name_match(new_owner, rec_owner)
            
            # If owners clearly differ (< 0.65 similarity)
            if name_sim < 0.65:
                conflict_score = round(95.0 - (name_sim * 20.0), 1)
                reasons = [
                    f"Survey number #{new_survey} already recorded in repository under verified owner '{rec_owner}'.",
                    f"New claim by '{new_owner}' exhibits low name similarity ({round(name_sim*100, 1)}%) with registered record.",
                    f"Conflicting registration reference: existing '{record.get('latest_registration_no', 'N/A')}' vs new '{new_reg}'."
                ]
                
                return {
                    "is_conflict": True,
                    "parcel_id": record.get("parcel_id") or f"P-CONF-{new_survey}",
                    "survey_no": new_survey,
                    "khata_no": new_khata or record.get("khata_no"),
                    "village": record.get("village") or new_village.capitalize(),
                    "existing_owner": rec_owner,
                    "existing_registration_no": record.get("latest_registration_no") or record.get("survey_no"),
                    "new_claimant": new_owner,
                    "new_registration_no": new_reg,
                    "conflict_score": conflict_score,
                    "reasons": reasons,
                    "recommendation": "High-risk duplicate claim detected. Route to Revenue Officer for manual title hearing."
                }
                
    return None
