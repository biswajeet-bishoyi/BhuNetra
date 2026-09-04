"""
tamil_nadu.py — Tamil Nadu State Land Administration Adapter (Anyror / Patta Chitta Portal).

Implements Tamil Nadu specific land records hierarchy and bilingual Tamil/English vocabulary:
State (Tamil Nadu) -> District (Kanchipuram / Chennai / Coimbatore) -> Taluk (வட்டம்) -> Village (கிராமம்)
Primary Identifier: Survey Number / Sub-division (புல எண் / உட்பிரிவு எண்)
Account Reference: Patta Number (பட்டா எண் / சிட்டா)
"""

from typing import Any, Dict, List
from adapters.base import StateAdapter, CanonicalParcel, CanonicalIdentifier, AreaModel


class TamilNaduAdapter(StateAdapter):
    def __init__(self):
        super().__init__(
            name="Tamil Nadu",
            state_code="TN",
            portal_name="Anyror / Patta Chitta Portal (e-Services of Land Records)",
            authority="Department of Survey and Settlement, Revenue Administration, Govt. of Tamil Nadu",
            location_hierarchy=["state", "district", "taluk", "village"],
            primary_identifier_type="survey_number",
            identifier_synonyms=[
                "survey", "survey_no", "survey number", "sy_no", "sub_division",
                "புல எண்", "உட்பிரிவு", "புல எண் / உட்பிரிவு", "புல எண் மற்றும் உட்பிரிவு"
            ],
            account_synonyms=[
                "patta", "patta_no", "patta number", "chitta", "chitta_no",
                "பட்டா", "பட்டா எண்", "சிட்டா", "சிட்டா எண்"
            ],
            unit_to_sqm_table={
                "cent": 40.4686,
                "cents": 40.4686,
                "சென்ட்": 40.4686,
                "acre": 4046.86,
                "acres": 4046.86,
                "ஏக்கர்": 4046.86,
                "ground": 222.96,
                "grounds": 222.96,
                "கிரவுண்ட்": 222.96,
                "kuzi": 13.38,
                "குழி": 13.38,
                "hectare": 10000.0,
                "ஹெக்டேர்": 10000.0,
                "are": 100.0,
                "ஆர்": 100.0,
                "sq ft": 0.092903,
                "சதுர அடி": 0.092903,
                "sq m": 1.0,
                "sqm": 1.0,
                "சதுர மீட்டர்": 1.0
            }
        )

    def get_supported_locations(self) -> Dict[str, Any]:
        return {
            "state": "Tamil Nadu",
            "districts": {
                "Kanchipuram": {
                    "taluks": {
                        "Sriperumbudur": ["Sriperumbudur", "Irungattukottai", "Nemili", "Mambakkam"],
                        "Walajabad": ["Walajabad", "Uthiramerur"]
                    }
                },
                "Chennai": {
                    "taluks": {
                        "Guindy": ["Velachery", "Adyar", "Guindy", "Alandur"],
                        "Mylapore": ["Mylapore", "Triplicane", "T. Nagar"]
                    }
                },
                "Chengalpattu": {
                    "taluks": {
                        "Tambaram": ["Tambaram", "Pallavaram", "Chromepet", "Vandalur"]
                    }
                },
                "Coimbatore": {
                    "taluks": {
                        "Coimbatore South": ["Madukkarai", "Perur"],
                        "Pollachi": ["Pollachi", "Anaimalai"]
                    }
                }
            }
        }

    def load_parcels(self) -> List[CanonicalParcel]:
        src = self.get_source_metadata(is_demo=True)
        # Sample canonical Tamil Nadu cadastral parcels
        tn_parcels = [
            {
                "parcel_id": "P-TN-101",
                "survey_no": "42/1A",
                "patta_no": "1042",
                "ulpin": "33-04210-1042-2026",
                "owner_name": "Murugan Swaminathan",
                "father_or_husband": "Swaminathan Pillai",
                "village": "Sriperumbudur",
                "taluk": "Sriperumbudur",
                "district": "Kanchipuram",
                "state": "Tamil Nadu",
                "area_cents": 20.0,
                "claimed_area_sqm": 809.37,
                "land_use_claim": "Nanjai (Wet Agricultural)",
                "lat": 12.9699,
                "lng": 79.9482
            },
            {
                "parcel_id": "P-TN-102",
                "survey_no": "89/2B",
                "patta_no": "2380",
                "ulpin": "33-08920-2380-2026",
                "owner_name": "Kavitha Rajendran",
                "father_or_husband": "Rajendran Sundaram",
                "village": "Velachery",
                "taluk": "Guindy",
                "district": "Chennai",
                "state": "Tamil Nadu",
                "area_cents": 5.51,
                "claimed_area_sqm": 222.96,
                "land_use_claim": "Residential / Natham",
                "lat": 12.9815,
                "lng": 80.2180
            }
        ]

        parcels: List[CanonicalParcel] = []
        for d in tn_parcels:
            parcels.append(
                CanonicalParcel(
                    parcel_id=d["parcel_id"],
                    state=d["state"],
                    district=d["district"],
                    subdistrict=d["taluk"],
                    village=d["village"],
                    identifier=CanonicalIdentifier(type="survey_number", value=d["survey_no"], is_primary=True),
                    khata_number=d.get("patta_no"),
                    owner_names=[d["owner_name"]],
                    area=AreaModel(
                        value=d["claimed_area_sqm"],
                        unit="sqm",
                        sqm_value=d["claimed_area_sqm"]
                    ),
                    land_use=d["land_use_claim"],
                    geometry={
                        "type": "Point",
                        "coordinates": [d["lng"], d["lat"]]
                    },
                    source=src
                )
            )
        return parcels
