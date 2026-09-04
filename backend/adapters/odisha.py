"""
adapters/odisha.py — Odisha Land Administration Adapter (Bhulekh / RoR).

State: Odisha (OD)
Statutory Portal: https://bhulekh.ori.nic.in/RoRView.aspx
Department: Revenue & Disaster Management Department, Govt of Odisha
Primary Identifier: Khata Number / Khatian No. (ଖାତା ନଂ) + Plot No. (ପ୍ଲଟ୍ ନଂ)
Primary Unit: Acres & Decimals (1 Acre = 100 Decimals = 4046.86 sq.m)
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from adapters.base import StateAdapter, CanonicalParcel, CanonicalIdentifier, AreaModel


class OdishaAdapter(StateAdapter):
    """Adapter for Odisha Bhulekh & Land Records (RoR)."""

    def __init__(self):
        super().__init__(
            name="Odisha",
            state_code="OD",
            portal_name="Odisha Bhulekh (RoR)",
            authority="Department of Revenue & Disaster Management, Government of Odisha",
            location_hierarchy=["state", "district", "tahasil", "ri_circle", "village"],
            primary_identifier_type="khata_plot_number",
            identifier_synonyms=["plot", "plot_no", "plot number", "chaka", "chaka_no"],
            account_synonyms=["khata", "khata_no", "khatian", "khatian_no"],
            unit_to_sqm_table={
                "decimal": 40.4686,
                "decimals": 40.4686,
                "acre": 4046.86,
                "acres": 4046.86,
                "hectare": 10000.0,
                "ha": 10000.0,
                "sq ft": 0.092903,
                "sq yd": 0.836127,
                "sqm": 1.0
            }
        )

    def get_supported_locations(self) -> Dict[str, Any]:
        return {
            "state": "Odisha",
            "districts": {
                "Khordha": {
                    "tahasils": {
                        "Bhubaneswar": ["Patia", "Chandrasekharpur", "Nayapalli", "Mancheswar"],
                        "Jatani": ["Jatani Rural", "Kantabad", "Khurda Road"]
                    }
                },
                "Cuttack": {
                    "tahasils": {
                        "Cuttack Sadar": ["Choudwar", "Bidanasi", "Madhupatna"],
                        "Salepur": ["Salepur Rural", "Nischintakoili"]
                    }
                },
                "Puri": {
                    "tahasils": {
                        "Puri Sadar": ["Baliguali", "Sipasarubali"],
                        "Pipili": ["Pipili Rural", "Dhauli Fringe"]
                    }
                }
            }
        }

    def parse_area_to_sqm(self, raw_area: Any) -> float:
        """Convert Acres or Decimals to square metres."""
        if isinstance(raw_area, (int, float)):
            return float(raw_area)

        text = str(raw_area).lower().strip()
        dec_match = re.search(r"([\d\.]+)\s*(?:dec|decimal|decimals|ଡେସିମିଲି)", text)
        if dec_match:
            decimals = float(dec_match.group(1))
            return round(decimals * 40.4686, 2)

        acre_match = re.search(r"([\d\.]+)\s*(?:ac|acre|acres|ଏକର)", text)
        if acre_match:
            acres = float(acre_match.group(1))
            return round(acres * 4046.856, 2)

        num_match = re.search(r"[\d\.]+", text)
        if num_match:
            return float(num_match.group(0))
        return 0.0

    def parse_document_fields(self, extracted_json: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize extracted deed attributes into standard Odisha schema."""
        khata = extracted_json.get("khatian_no") or extracted_json.get("khata_no") or extracted_json.get("khasra_no")
        plot = extracted_json.get("survey_no") or extracted_json.get("plot_no") or extracted_json.get("khasra_no")

        return {
            "state": "Odisha",
            "state_code": "OD",
            "khata_no": khata,
            "plot_no": plot,
            "tenant_name": extracted_json.get("owner_name"),
            "guardian_name": extracted_json.get("father_or_husband"),
            "village": extracted_json.get("village") or "Patia",
            "tahasil": extracted_json.get("mandal") or "Bhubaneswar",
            "district": extracted_json.get("district") or "Khordha",
            "kissam": extracted_json.get("land_type") or "Gharabari (Homestead)",
            "tenancy_status": "ସ୍ଥିତିବାନ (Rayati Sthitiban)",
            "deed_no": extracted_json.get("deed_registration_no"),
            "area_sqm": self.parse_area_to_sqm(extracted_json.get("claimed_extent") or extracted_json.get("claimed_area_sqm"))
        }

    def load_parcels(self) -> List[CanonicalParcel]:
        """Return Odisha synthetic canonical baseline parcels."""
        src = self.get_source_metadata(is_demo=True)
        return [
            CanonicalParcel(
                parcel_id="OD-102-GJM",
                state="Odisha",
                district="Ganjam",
                subdistrict="Chhatrapur Tahasil",
                village="Chhatrapur",
                primary_identifier=CanonicalIdentifier(
                    id_type="khata_plot_number",
                    value="102",
                    label="Plot 102 (Khata No. 102)"
                ),
                account_reference="Khata No. 102",
                owner_name="Sudrusti Sethi (ସୁଦୃଷ୍ଟି ସେଠୀ)",
                father_or_husband_name="Narahari Sethi (ସ୍ଵା: ନରହରି ସେଠୀ)",
                land_type="Raiyati (ରୟତି)",
                area=AreaModel(
                    sqm=4046.86,
                    original_value=1.000,
                    original_unit="acre",
                    formatted="1.000 Acre (100 Decimals)"
                ),
                centroid=[19.3550, 84.9920],
                polygon=[
                    [84.9910, 19.3555],
                    [84.9930, 19.3555],
                    [84.9930, 19.3545],
                    [84.9910, 19.3545],
                    [84.9910, 19.3555]
                ],
                gis_status="CLEAN",
                revenue_court_status="Clean Record",
                source=src,
                extra_attributes={
                    "kissam": "Raiyati (ରୟତି)",
                    "tenancy_status": "ସ୍ଥିତିବାନ (Rayati Sthitiban)",
                    "statutory_portal": "https://bhulekh.ori.nic.in/RoRView.aspx"
                }
            ),
            CanonicalParcel(
                parcel_id="OD-1024-2",
                state="Odisha",
                district="Khordha",
                subdistrict="Bhubaneswar",
                village="Patia",
                primary_identifier=CanonicalIdentifier(
                    id_type="khata_plot_number",
                    value="1024/2",
                    label="Plot 1024/2 (Khata 145/12)"
                ),
                account_reference="Khata 145/12",
                owner_name="Bishnu Charan Das",
                father_or_husband_name="Gopal Charan Das",
                land_type="Gharabari (Homestead)",
                area=AreaModel(
                    sqm=607.03,
                    original_value=15.0,
                    original_unit="decimal",
                    formatted="15 Decimals (0.150 Acres)"
                ),
                centroid=[20.3536, 85.8250],
                polygon=[
                    [85.8245, 20.3541],
                    [85.8255, 20.3541],
                    [85.8255, 20.3532],
                    [85.8245, 20.3532],
                    [85.8245, 20.3541]
                ],
                gis_status="CLEAN",
                revenue_court_status="Clean Record",
                source=src,
                extra_attributes={
                    "kissam": "Gharabari (Homestead)",
                    "tenancy_status": "ସ୍ଥିତିବାନ (Rayati Sthitiban)",
                    "statutory_portal": "https://bhulekh.ori.nic.in/RoRView.aspx"
                }
            )
        ]
