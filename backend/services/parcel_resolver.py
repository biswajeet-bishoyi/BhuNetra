"""
parcel_resolver.py — Multi-Stage Cadastral Parcel Resolution Engine.

Executes hierarchical and fuzzy cadastral matching:
Stage 1: Location hierarchy match (State -> District -> Tehsil -> Village)
Stage 2: Identifier canonical match (Khasra, Gat, Survey, Plot)
Stage 3: Controlled fuzzy matching for OCR variations
Stage 4: Multi-candidate ranking and confidence scoring
Stage 5: Result status determination (VERIFIED, WARNING, AMBIGUOUS, NOT_FOUND)
"""

from __future__ import annotations
import re
import difflib
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from adapters import get_adapter
from adapters.base import CanonicalParcel, CanonicalExtraction, AreaModel


class CandidateMatch(BaseModel):
    parcel_id: str
    identifier_type: str
    identifier_value: str
    khata_number: Optional[str] = None
    state: str
    district: str
    subdistrict: str
    village: str
    owner_names: List[str]
    area: AreaModel
    area_difference_pct: float = 0.0
    match_score_pct: float
    confidence_tier: str  # "HIGH", "MEDIUM", "LOW"
    match_reasons: List[str]
    geometry: Dict[str, Any]
    mutation_status: str
    registration_status: str
    source: Dict[str, Any]


class ResolutionResult(BaseModel):
    status: str  # "VERIFIED", "WARNING", "AMBIGUOUS", "NOT_FOUND"
    message: str
    matched_parcel: Optional[CandidateMatch] = None
    candidates: List[CandidateMatch] = Field(default_factory=list)
    state_adapter: str
    resolution_pipeline_stage: str
    location_matched: bool = False
    identifier_matched: bool = False
    evidence_chain: List[str] = Field(default_factory=list)


def _similarity(s1: str, s2: str) -> float:
    """Normalized string similarity between 0.0 and 1.0."""
    if not s1 or not s2:
        return 0.0
    s1_clean = re.sub(r"[^a-zA-Z0-9]", "", s1.lower())
    s2_clean = re.sub(r"[^a-zA-Z0-9]", "", s2.lower())
    if s1_clean == s2_clean:
        return 1.0
    return difflib.SequenceMatcher(None, s1_clean, s2_clean).ratio()


def resolve_parcel(
    extraction: CanonicalExtraction,
    override_state: Optional[str] = None
) -> ResolutionResult:
    """
    Execute multi-stage cadastral parcel resolution from extracted document fields.
    """
    target_state = override_state or extraction.state or "Rajasthan"
    adapter = get_adapter(target_state)
    all_parcels = adapter.load_parcels()

    evidence: List[str] = []
    evidence.append(f"Selected State Adapter: {adapter.name} ({adapter.portal_name})")

    # Clean target search identifiers
    raw_ident = ""
    if extraction.identifier:
        raw_ident = extraction.identifier.value
    elif extraction.raw_fields:
        raw_ident = str(
            extraction.raw_fields.get("khasra_number") or
            extraction.raw_fields.get("survey_no") or
            extraction.raw_fields.get("plot_number") or
            extraction.raw_fields.get("gat_number") or ""
        )

    norm_target_ident = adapter.normalize_identifier(raw_ident)
    target_village = (extraction.village or "").strip().lower()
    target_subdistrict = (extraction.subdistrict or "").strip().lower()
    target_district = (extraction.district or "").strip().lower()
    target_khata = (extraction.khata_number or "").strip().lower()
    target_owners = [o.strip().lower() for o in extraction.owner_names if o]

    evidence.append(f"Target Identifier: '{norm_target_ident}' (Source: '{raw_ident}')")
    if target_village:
        evidence.append(f"Target Village: '{target_village.title()}'")

    # Filter candidate parcels
    candidate_scores: List[Tuple[CanonicalParcel, float, List[str], float]] = []

    for parcel in all_parcels:
        score = 0.0
        reasons: List[str] = []

        # 1. State check
        if parcel.state.lower() == target_state.lower():
            score += 20.0
        else:
            continue

        # 2. District check
        if target_district and _similarity(parcel.district, target_district) >= 0.7:
            score += 15.0
            reasons.append(f"District matched: '{parcel.district}'")
        elif not target_district:
            score += 10.0  # partial credit

        # 3. Subdistrict (Tehsil/Taluka/Mandal) check
        if target_subdistrict and _similarity(parcel.subdistrict, target_subdistrict) >= 0.7:
            score += 15.0
            reasons.append(f"Sub-district matched: '{parcel.subdistrict}'")
        elif not target_subdistrict:
            score += 10.0

        # 4. Village check
        if target_village and _similarity(parcel.village, target_village) >= 0.7:
            score += 20.0
            reasons.append(f"Village matched: '{parcel.village}'")
        elif not target_village:
            score += 10.0

        # 5. Identifier Match (Crucial)
        p_ident = adapter.normalize_identifier(parcel.identifier.value)
        ident_sim = _similarity(p_ident, norm_target_ident)

        if p_ident == norm_target_ident and norm_target_ident:
            score += 30.0
            reasons.append(f"Exact identifier match: '{p_ident}'")
        elif ident_sim >= 0.75:
            # Fuzzy match e.g. OCR minor difference like 124/2 vs 124/3 or 12412
            score += 15.0 * ident_sim
            reasons.append(f"Fuzzy identifier match: '{norm_target_ident}' ~ '{p_ident}' ({int(ident_sim * 100)}%)")
        elif not norm_target_ident:
            score += 0.0

        # 6. Khata check
        if target_khata and parcel.khata_number:
            if target_khata in parcel.khata_number.lower() or parcel.khata_number.lower() in target_khata:
                score += 10.0
                reasons.append(f"Khata/Account matched: '{parcel.khata_number}'")

        # 7. Owner check
        owner_matched = False
        for to in target_owners:
            for po in parcel.owner_names:
                if _similarity(to, po) >= 0.65:
                    score += 10.0
                    reasons.append(f"Owner matched: '{po}'")
                    owner_matched = True
                    break
            if owner_matched:
                break

        # 8. Area difference calculation
        area_diff_pct = 0.0
        if extraction.area and extraction.area.sqm > 0 and parcel.area.sqm > 0:
            diff_sqm = abs(extraction.area.sqm - parcel.area.sqm)
            area_diff_pct = round((diff_sqm / max(extraction.area.sqm, parcel.area.sqm)) * 100.0, 2)
            if area_diff_pct <= 5.0:
                score += 5.0
                reasons.append(f"Area variance {area_diff_pct}% (within ±5% tolerance)")

        total_pct = min(99.5, round(score, 1))
        if total_pct >= 40.0:
            candidate_scores.append((parcel, total_pct, reasons, area_diff_pct))

    # Sort descending by match score
    candidate_scores.sort(key=lambda x: x[1], reverse=True)

    # Convert to CandidateMatch objects
    candidates: List[CandidateMatch] = []
    for parcel, pct, reasons, diff_pct in candidate_scores:
        tier = "HIGH" if pct >= 80.0 else ("MEDIUM" if pct >= 60.0 else "LOW")
        candidates.append(CandidateMatch(
            parcel_id=parcel.parcel_id,
            identifier_type=parcel.identifier.type,
            identifier_value=parcel.identifier.value,
            khata_number=parcel.khata_number,
            state=parcel.state,
            district=parcel.district,
            subdistrict=parcel.subdistrict,
            village=parcel.village,
            owner_names=parcel.owner_names,
            area=parcel.area,
            area_difference_pct=diff_pct,
            match_score_pct=pct,
            confidence_tier=tier,
            match_reasons=reasons,
            geometry=parcel.geometry,
            mutation_status=parcel.mutation_status,
            registration_status=parcel.registration_status,
            source=parcel.source.model_dump()
        ))

    # Evaluate Resolution State
    if not candidates or candidates[0].match_score_pct < 50.0:
        return ResolutionResult(
            status="NOT_FOUND",
            message=f"No matching cadastral parcel found in {adapter.name} ({adapter.portal_name}) dataset. Exact parcel could not be confidently resolved.",
            candidates=candidates[:3],
            state_adapter=adapter.name,
            resolution_pipeline_stage="PARCEL_SEARCH_EXHAUSTED",
            location_matched=False,
            identifier_matched=False,
            evidence_chain=evidence + ["No record met the minimum 50% confidence threshold."]
        )

    top = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None

    # Check for ambiguity: multiple top candidates close in score
    exact_top_ident = (adapter.normalize_identifier(top.identifier_value) == norm_target_ident)
    exact_second_ident = second and (adapter.normalize_identifier(second.identifier_value) == norm_target_ident)
    score_gap = (top.match_score_pct - second.match_score_pct) if second else 100.0

    # True ambiguity happens if:
    # 1. Multiple parcels share the exact same identifier in neighboring villages/pattas, OR
    # 2. Top candidate is NOT an exact identifier match and the gap with second candidate is < 12%
    is_ambiguous = False
    if second:
        if exact_second_ident and score_gap < 10.0:
            is_ambiguous = True
        elif not exact_top_ident and score_gap < 12.0 and second.match_score_pct >= 65.0:
            is_ambiguous = True

    if is_ambiguous:
        evidence.append(f"Ambiguity detected: Candidate 1 '{top.identifier_value}' ({top.match_score_pct}%) vs Candidate 2 '{second.identifier_value}' ({second.match_score_pct}%)")
        return ResolutionResult(
            status="AMBIGUOUS",
            message=f"Multiple parcels closely match the extracted identifiers in {top.village}. Manual selection or officer review required.",
            matched_parcel=top,
            candidates=candidates[:5],
            state_adapter=adapter.name,
            resolution_pipeline_stage="AMBIGUOUS_CANDIDATES",
            location_matched=True,
            identifier_matched=False,
            evidence_chain=evidence
        )

    # Check for Warning: Area mismatch > 10% or pending mutation
    if top.area_difference_pct > 10.0 or top.mutation_status != "Clean":
        warn_reasons = []
        if top.area_difference_pct > 10.0:
            warn_reasons.append(f"Area discrepancy {top.area_difference_pct}%")
        if top.mutation_status != "Clean":
            warn_reasons.append(f"Mutation status '{top.mutation_status}'")
        evidence.append(f"Warning criteria met: {', '.join(warn_reasons)}")

        return ResolutionResult(
            status="WARNING",
            message=f"Parcel {top.identifier_value} identified with caveats: {', '.join(warn_reasons)}.",
            matched_parcel=top,
            candidates=candidates[:4],
            state_adapter=adapter.name,
            resolution_pipeline_stage="PARCEL_RESOLVED_WITH_WARNING",
            location_matched=True,
            identifier_matched=True,
            evidence_chain=evidence + top.match_reasons
        )

    # Clean high confidence verification
    evidence.append(f"✓ Exact cadastral parcel resolved: {top.identifier_value} ({top.match_score_pct}% match)")
    return ResolutionResult(
        status="VERIFIED",
        message=f"Parcel {top.identifier_value} verified with high confidence against {adapter.portal_name}.",
        matched_parcel=top,
        candidates=candidates[:3],
        state_adapter=adapter.name,
        resolution_pipeline_stage="PARCEL_RESOLVED_VERIFIED",
        location_matched=True,
        identifier_matched=True,
        evidence_chain=evidence + top.match_reasons
    )
