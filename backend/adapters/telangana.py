"""
telangana.py — Telangana State Land Administration Adapter (Dharani Portal).

Implements Telangana specific land records hierarchy:
State (Telangana) -> District (Rangareddy) -> Mandal (Shamshabad) -> Village (Shamshabad / Mamidipally)
Primary Identifier: Survey Number / Sub-division
Account Reference: Khatian / Pattadar Passbook
"""

import os
import json
from typing import Any, Dict, List
from adapters.base import StateAdapter, CanonicalParcel, CanonicalIdentifier, AreaModel


class TelanganaAdapter(StateAdapter):
    def __init__(self):
        super().__init__(
            name="Telangana",
            state_code="TS",
            portal_name="Dharani Portal",
            authority="Chief Commissioner of Land Administration (CCLA), Government of Telangana",
            location_hierarchy=["state", "district", "mandal", "village"],
            primary_identifier_type="survey_number",
            identifier_synonyms=["survey", "survey_no", "survey number", "sy_no", "sub_division"],
            account_synonyms=["khatian", "khatian_no", "passbook", "khata"],
            unit_to_sqm_table={
                "acre": 4046.86,
                "ac": 4046.86,
                "gunta": 101.17,
                "guntas": 101.17,
                "sq m": 1.0,
                "sqm": 1.0,
                "sq ft": 0.092903,
                "sq yd": 0.836127,
                "hectare": 10000.0
            }
        )

    def get_supported_locations(self) -> Dict[str, Any]:
        return {
            "state": "Telangana",
            "districts": {
                "Rangareddy": {
                    "mandals": {
                        "Shamshabad": ["Shamshabad", "Mamidipally", "Kothwalguda", "Gaganpahad"],
                        "Rajendranagar": ["Attapur", "Budvel"]
                    }
                },
                "Medchal-Malkajgiri": {
                    "mandals": {
                        "Kukatpally": ["Kukatpally", "Hydernagar"]
                    }
                }
            }
        }

    def load_parcels(self) -> List[CanonicalParcel]:
        src = self.get_source_metadata(is_demo=True)
        geojson_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic", "parcels.geojson")
        
        if not os.path.exists(geojson_path):
            return []

        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        parcels: List[CanonicalParcel] = []
        for feat in data.get("features", []):
            prop = feat.get("properties", {})
            geom = feat.get("geometry", {})
            pid = prop.get("parcel_id", "P-UNKNOWN")
            sy_no = str(prop.get("survey_no", ""))
            
            c_ident = CanonicalIdentifier(
                type="survey_number",
                value=self.normalize_identifier(sy_no),
                source_type="Survey Number",
                source_value=sy_no
            )

            claimed = float(prop.get("claimed_area_sqm") or 0.0)
            area_m = AreaModel(
                value=round(claimed / 4046.86, 3),
                unit="acres",
                sqm=claimed
            )

            p = CanonicalParcel(
                parcel_id=pid,
                state="Telangana",
                district=prop.get("district", "Rangareddy"),
                subdistrict=prop.get("mandal", "Shamshabad"),
                village=prop.get("village", "Shamshabad"),
                identifier=c_ident,
                khata_number=prop.get("khatian_no"),
                owner_names=[prop.get("owner_name", "Pattadar")],
                father_or_husband=prop.get("father_or_husband"),
                area=area_m,
                geometry=geom,
                boundaries={
                    "north": "Survey Road / Boundary",
                    "south": "Adjacent Survey Plot",
                    "east": "Survey Field Boundary",
                    "west": "Adjacent Registered Parcel"
                },
                land_use=prop.get("land_use_claim", "Agricultural"),
                mutation_status="Clean" if not prop.get("is_anomalous") else "Pending",
                registration_status="Registered",
                revenue_court_status=prop.get("revenue_court_status", "Clean"),
                source=src
            )
            parcels.append(p)

        return parcels
