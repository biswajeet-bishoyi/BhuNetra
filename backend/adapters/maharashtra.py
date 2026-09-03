"""
maharashtra.py — Maharashtra State Land Administration Adapter (Mahabhulekh / 7-12 Utara).

Implements Maharashtra specific land records hierarchy:
State (Maharashtra) -> District (Pune) -> Taluka (Haveli) -> Village (Wagholi / Haveli Rural)
Primary Identifier: Gat Number / CTS Number / Survey Number
Account Reference: Khata Number (from 7/12 Extract)
"""

from typing import Any, Dict, List
from adapters.base import StateAdapter, CanonicalParcel, CanonicalIdentifier, AreaModel


class MaharashtraAdapter(StateAdapter):
    def __init__(self):
        super().__init__(
            name="Maharashtra",
            state_code="MH",
            portal_name="Mahabhulekh (7/12 Utara)",
            authority="Revenue & Forest Department, Government of Maharashtra",
            location_hierarchy=["state", "district", "taluka", "village"],
            primary_identifier_type="gat_number",
            identifier_synonyms=["gat", "gat_no", "gat number", "cts", "cts_no", "survey", "survey_no"],
            account_synonyms=["khata", "khata_number", "khata_no", "saat_baara", "7/12"],
            unit_to_sqm_table={
                "hectare": 10000.0,
                "ha": 10000.0,
                "guntha": 101.17,
                "sq ft": 0.092903,
                "sq yd": 0.836127,
                "acre": 4046.86
            }
        )

    def get_supported_locations(self) -> Dict[str, Any]:
        return {
            "state": "Maharashtra",
            "districts": {
                "Pune": {
                    "talukas": {
                        "Haveli": ["Wagholi", "Hadapsar", "Loni Kalbhor", "Manjri"],
                        "Mulshi": ["Pirangut", "Paud", "Hinjawadi"]
                    }
                },
                "Thane": {
                    "talukas": {
                        "Kalyan": ["Dombivli Rural", "Titwala"],
                        "Thane": ["Bhayandar", "Majiwada"]
                    }
                }
            }
        }

    def load_parcels(self) -> List[CanonicalParcel]:
        # Center coordinates around Haveli Taluka, Pune District (18.578° N, 73.985° E)
        src = self.get_source_metadata(is_demo=True)
        parcels_data = [
            {
                "parcel_id": "MH-123",
                "gat": "123",
                "khata": "412",
                "village": "Wagholi",
                "taluka": "Haveli",
                "district": "Pune",
                "owners": ["Dnyaneshwar Patil"],
                "father_or_husband": "Tukaram Patil",
                "area_val": 0.40,
                "area_unit": "hectare",
                "area_sqm": 4000.0,
                "coords": [
                    [73.98450, 18.57780],
                    [73.98540, 18.57785],
                    [73.98535, 18.57865],
                    [73.98445, 18.57860],
                    [73.98450, 18.57780]
                ],
                "boundaries": {
                    "north": "Gat No. 124 (Anusaya Jadhav)",
                    "south": "Village Approach Road",
                    "east": "Gat No. 122 (Vilas Shinde)",
                    "west": "Gat No. 121 (Rajesh More)"
                },
                "mutation": "Clean",
                "registration": "Registered",
                "court": "Clean"
            },
            {
                "parcel_id": "MH-122",
                "gat": "122",
                "khata": "415",
                "village": "Wagholi",
                "taluka": "Haveli",
                "district": "Pune",
                "owners": ["Vilas Shinde"],
                "father_or_husband": "Baburao Shinde",
                "area_val": 0.35,
                "area_unit": "hectare",
                "area_sqm": 3500.0,
                "coords": [
                    [73.98540, 18.57785],
                    [73.98625, 18.57790],
                    [73.98620, 18.57870],
                    [73.98535, 18.57865],
                    [73.98540, 18.57785]
                ],
                "boundaries": {
                    "north": "Drainage Nala",
                    "south": "Village Approach Road",
                    "east": "Gat No. 120",
                    "west": "Gat No. 123 (Dnyaneshwar Patil)"
                },
                "mutation": "Clean",
                "registration": "Registered",
                "court": "Clean"
            },
            {
                "parcel_id": "MH-124",
                "gat": "124",
                "khata": "420",
                "village": "Wagholi",
                "taluka": "Haveli",
                "district": "Pune",
                "owners": ["Anusaya Jadhav"],
                "father_or_husband": "Maruti Jadhav",
                "area_val": 0.50,
                "area_unit": "hectare",
                "area_sqm": 5000.0,
                "coords": [
                    [73.98445, 18.57860],
                    [73.98535, 18.57865],
                    [73.98530, 18.57950],
                    [73.98440, 18.57945],
                    [73.98445, 18.57860]
                ],
                "boundaries": {
                    "north": "Gat No. 125",
                    "south": "Gat No. 123 (Dnyaneshwar Patil)",
                    "east": "Drainage Nala",
                    "west": "Zilla Parishad School Road"
                },
                "mutation": "Pending",
                "registration": "Registered",
                "court": "Clean"
            }
        ]

        result = []
        for p in parcels_data:
            c_ident = CanonicalIdentifier(
                type="gat_number",
                value=self.normalize_identifier(p["gat"]),
                source_type="Gat Number",
                source_value=p["gat"]
            )
            area_m = AreaModel(value=p["area_val"], unit=p["area_unit"], sqm=p["area_sqm"])
            result.append(CanonicalParcel(
                parcel_id=p["parcel_id"],
                state="Maharashtra",
                district=p["district"],
                subdistrict=p["taluka"],
                village=p["village"],
                identifier=c_ident,
                khata_number=p["khata"],
                owner_names=p["owners"],
                father_or_husband=p.get("father_or_husband"),
                area=area_m,
                geometry={"type": "Polygon", "coordinates": [p["coords"]]},
                boundaries=p["boundaries"],
                land_use="Agricultural / Non-Agricultural",
                mutation_status=p["mutation"],
                registration_status=p["registration"],
                revenue_court_status=p["court"],
                source=src
            ))
        return result
