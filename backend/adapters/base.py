"""
base.py — StateAdapter Base Architecture & Canonical Data Models.

Defines the contract for state-specific land-record adapters across India,
canonicalizing location hierarchies, survey/khasra/gat terminology,
state-specific land measurement units, and source attribution.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
import re
import math


class AreaModel(BaseModel):
    value: float
    unit: str
    sqm: float = 0.0
    tolerance_pct: float = 5.0


class CanonicalIdentifier(BaseModel):
    type: str  # e.g. "khasra_number", "survey_number", "gat_number", "plot_number"
    value: str
    source_type: str = ""  # e.g. "Khasra Number", "Survey / Sub-division"
    source_value: str = ""


class SourceMetadata(BaseModel):
    type: str  # "OFFICIAL_DATASET", "DEMO_DATASET", "LIVE_OFFICIAL", "USER_PROVIDED"
    name: str
    authority: str
    last_updated: str = "2026-03-01"
    disclaimer: str = "Official dataset schema. Demonstration dataset used for SIH 2026 evaluation."


class CanonicalParcel(BaseModel):
    parcel_id: str
    state: str
    district: str
    subdistrict: str  # tehsil / taluka / mandal
    village: str
    identifier: CanonicalIdentifier
    khata_number: Optional[str] = None
    khatoni_number: Optional[str] = None
    owner_names: List[str] = Field(default_factory=list)
    father_or_husband: Optional[str] = None
    area: AreaModel
    geometry: Dict[str, Any]  # GeoJSON Polygon
    boundaries: Dict[str, str] = Field(default_factory=dict)  # north, south, east, west
    land_use: str = "Agricultural"
    record_status: str = "Active"
    registration_status: str = "Registered"
    mutation_status: str = "Clean"  # "Clean", "Pending", "Disputed"
    revenue_court_status: str = "Clean"  # "Clean", "Stay Order", "Court Case"
    source: SourceMetadata


class CanonicalExtraction(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None  # tehsil/taluka/mandal
    village: Optional[str] = None
    identifier: Optional[CanonicalIdentifier] = None
    khata_number: Optional[str] = None
    khatoni_number: Optional[str] = None
    owner_names: List[str] = Field(default_factory=list)
    father_or_husband: Optional[str] = None
    area: Optional[AreaModel] = None
    document_type: str = "sale_deed"
    registration_number: Optional[str] = None
    registration_date: Optional[str] = None
    boundaries: Dict[str, str] = Field(default_factory=dict)
    confidence: Dict[str, float] = Field(default_factory=dict)
    raw_fields: Dict[str, Any] = Field(default_factory=dict)


class StateAdapter(ABC):
    """Abstract base class for all State Land Administration Adapters."""

    def __init__(
        self,
        name: str,
        state_code: str,
        portal_name: str,
        authority: str,
        location_hierarchy: List[str],
        primary_identifier_type: str,
        identifier_synonyms: List[str],
        account_synonyms: List[str],
        unit_to_sqm_table: Dict[str, float],
    ):
        self.name = name
        self.state_code = state_code
        self.portal_name = portal_name
        self.authority = authority
        self.location_hierarchy = location_hierarchy
        self.primary_identifier_type = primary_identifier_type
        self.identifier_synonyms = [s.lower() for s in identifier_synonyms]
        self.account_synonyms = [s.lower() for s in account_synonyms]
        self.unit_to_sqm_table = unit_to_sqm_table

    def get_source_metadata(self, is_demo: bool = True) -> SourceMetadata:
        return SourceMetadata(
            type="DEMO_DATASET" if is_demo else "OFFICIAL_DATASET",
            name=f"{self.portal_name} ({self.name} Land Records)",
            authority=self.authority,
            last_updated="2026-03-01",
            disclaimer="State cadastral demo dataset for SIH 2026 verification."
        )

    def normalize_identifier(self, raw_value: str) -> str:
        """Strip prefixes like 'Khasra No.', 'Gat No.', 'Survey No.', spaces, and clean slashes."""
        if not raw_value:
            return ""
        clean = re.sub(r"(?i)\b(khasra|gat|survey|plot|dag|chaka|cts|hissa|no|num|number|\.)\b", "", raw_value)
        clean = clean.replace(" ", "").strip("-").strip("/").strip()
        # Normalize slashes: e.g. 124 / 2 -> 124/2
        clean = re.sub(r"\s*/\s*", "/", clean)
        return clean or raw_value.strip()

    def normalize_area(self, value: float, unit_str: str) -> AreaModel:
        """Convert a localized unit (bigha, guntha, acre, decimal, hectare) to square meters."""
        unit_clean = unit_str.lower().strip().replace(".", "")
        sqm_factor = 1.0
        for known_unit, factor in self.unit_to_sqm_table.items():
            if known_unit in unit_clean:
                sqm_factor = factor
                break
        else:
            # Fallback general units
            if "hectare" in unit_clean or "ha" in unit_clean:
                sqm_factor = 10000.0
            elif "acre" in unit_clean or "ac" in unit_clean:
                sqm_factor = 4046.86
            elif "sq ft" in unit_clean or "sqft" in unit_clean:
                sqm_factor = 0.092903
            elif "sq yd" in unit_clean or "sqyd" in unit_clean or "sq yds" in unit_clean:
                sqm_factor = 0.836127

        total_sqm = round(value * sqm_factor, 2)
        return AreaModel(value=value, unit=unit_str, sqm=total_sqm)

    def compare_areas(self, doc_area: AreaModel, gis_area_sqm: float, tolerance_pct: float = 5.0) -> Tuple[bool, float, str]:
        """Compare document area with GIS area using state-aware conversion and tolerance."""
        if doc_area.sqm <= 0 or gis_area_sqm <= 0:
            return False, 100.0, "Missing or invalid area measurement"

        diff_sqm = abs(doc_area.sqm - gis_area_sqm)
        pct_diff = round((diff_sqm / max(doc_area.sqm, gis_area_sqm)) * 100.0, 2)
        is_consistent = pct_diff <= tolerance_pct

        if is_consistent:
            msg = f"Area consistent: Document {doc_area.value} {doc_area.unit} ({doc_area.sqm} sqm) vs GIS ({gis_area_sqm} sqm), variance {pct_diff}% (within ±{tolerance_pct}% tolerance)."
        else:
            msg = f"Area discrepancy flagged: Document claims {doc_area.value} {doc_area.unit} ({doc_area.sqm} sqm) but GIS cadastre measures {gis_area_sqm} sqm (variance {pct_diff}% exceeds ±{tolerance_pct}% tolerance)."

        return is_consistent, pct_diff, msg

    @abstractmethod
    def get_supported_locations(self) -> Dict[str, Any]:
        """Return districts, tehsils/talukas, and villages supported by this adapter."""
        pass

    @abstractmethod
    def load_parcels(self) -> List[CanonicalParcel]:
        """Load all cadastral parcels for this state."""
        pass
