"""
generic.py — Generic / Pan-India State Land Administration Adapter.

Provides resilient fallback support for any Indian state (e.g. Odisha, Delhi,
Uttar Pradesh, Bihar, Karnataka) using standardized DILRMP land-record fields.
"""

from typing import Any, Dict, List
from adapters.base import StateAdapter, CanonicalParcel, CanonicalIdentifier, AreaModel


class GenericStateAdapter(StateAdapter):
    def __init__(self, state_name: str = "Odisha"):
        is_odisha = "odisha" in state_name.lower()
        super().__init__(
            name="Odisha" if is_odisha else state_name,
            state_code="OD" if is_odisha else "GEN",
            portal_name="Bhulekh Odisha (e-Pauti)" if is_odisha else f"{state_name} Land Records Portal",
            authority="Department of Revenue & Disaster Management, Govt. of Odisha" if is_odisha else "State Revenue Department",
            location_hierarchy=["state", "district", "subdistrict", "village"],
            primary_identifier_type="plot_number" if is_odisha else "khasra_number",
            identifier_synonyms=["plot", "plot_no", "khasra", "khasra_no", "survey", "survey_no", "dag", "dag_no"],
            account_synonyms=["khata", "khata_number", "khata_no", "khatian", "jamabandi"],
            unit_to_sqm_table={
                "decimal": 40.4686,
                "decimals": 40.4686,
                "acre": 4046.86,
                "hectare": 10000.0,
                "sq ft": 0.092903,
                "sq yd": 0.836127,
                "sq m": 1.0,
                "sqm": 1.0,
                "bigha": 2500.0,
                "guntha": 101.17
            }
        )

    def get_supported_locations(self) -> Dict[str, Any]:
        return {
            "state": self.name,
            "districts": {
                "Khordha": {
                    "subdistricts": {
                        "Bhubaneswar Tahasil": ["Chandrasekharpur", "Patia", "Nayapalli", "Khandagiri"]
                    }
                },
                "South Delhi": {
                    "subdistricts": {
                        "Saket": ["Sangam Vihar", "Deoli"]
                    }
                }
            }
        }

    def load_parcels(self) -> List[CanonicalParcel]:
        src = self.get_source_metadata(is_demo=True)
        # Center coordinates around Chandrasekharpur, Bhubaneswar, Khordha (20.3242° N, 85.8152° E)
        odisha_parcels = [
            {
                "parcel_id": "P-OD-142",
                "plot": "142/892",
                "khata": "248/12",
                "village": "Chandrasekharpur",
                "subdistrict": "Bhubaneswar Tahasil",
                "district": "Khordha",
                "state": "Odisha",
                "owners": ["Bijay Kumar Mohapatra"],
                "father_or_husband": "Rabindra Mohapatra",
                "area_val": 10.0,
                "area_unit": "decimals",
                "area_sqm": 404.68,
                "coords": [
                    [85.81480, 20.32390],
                    [85.81560, 20.32395],
                    [85.81555, 20.32470],
                    [85.81475, 20.32465],
                    [85.81480, 20.32390]
                ],
                "boundaries": {
                    "north": "Municipal Sub-Road",
                    "south": "Plot No. 142/891",
                    "east": "Plot No. 142/893",
                    "west": "BDA Green Buffer Zone"
                },
                "mutation": "Clean",
                "registration": "Registered",
                "court": "Clean"
            },
            {
                "parcel_id": "P-OD-141",
                "plot": "142/891",
                "khata": "248/10",
                "village": "Chandrasekharpur",
                "subdistrict": "Bhubaneswar Tahasil",
                "district": "Khordha",
                "state": "Odisha",
                "owners": ["Pradeep Nayak"],
                "father_or_husband": "Harekrushna Nayak",
                "area_val": 8.5,
                "area_unit": "decimals",
                "area_sqm": 343.98,
                "coords": [
                    [85.81480, 20.32310],
                    [85.81560, 20.32315],
                    [85.81560, 20.32395],
                    [85.81480, 20.32390],
                    [85.81480, 20.32310]
                ],
                "boundaries": {
                    "north": "Plot No. 142/892 (Bijay Kumar Mohapatra)",
                    "south": "Village Pond Catchment",
                    "east": "Vacant Plot",
                    "west": "BDA Green Buffer Zone"
                },
                "mutation": "Clean",
                "registration": "Registered",
                "court": "Clean"
            },
            {
                "parcel_id": "P-4661",
                "plot": "46/61",
                "khata": "KH-461",
                "village": "Sangam Vihar",
                "subdistrict": "South Delhi",
                "district": "South Delhi",
                "state": "Delhi",
                "owners": ["Mohan Lal (POA: Bachu Singh)"],
                "father_or_husband": "Asha Ram",
                "area_val": 32.0,
                "area_unit": "sq yds",
                "area_sqm": 26.75,
                "coords": [
                    [77.24750, 28.50110],
                    [77.24775, 28.50110],
                    [77.24775, 28.50130],
                    [77.24750, 28.50130],
                    [77.24750, 28.50110]
                ],
                "boundaries": {
                    "north": "Gali No. 4 (15ft Road)",
                    "south": "Plot 46/62",
                    "east": "Property of K. Sharma",
                    "west": "Drainage Line"
                },
                "mutation": "Pending",
                "registration": "Registered",
                "court": "Clean"
            }
        ]

        result = []
        for p in odisha_parcels:
            c_ident = CanonicalIdentifier(
                type="plot_number" if p["state"] == "Odisha" else "khasra_number",
                value=self.normalize_identifier(p["plot"]),
                source_type="Plot / Khasra Number",
                source_value=p["plot"]
            )
            area_m = AreaModel(value=p["area_val"], unit=p["area_unit"], sqm=p["area_sqm"])
            result.append(CanonicalParcel(
                parcel_id=p["parcel_id"],
                state=p["state"],
                district=p["district"],
                subdistrict=p["subdistrict"],
                village=p["village"],
                identifier=c_ident,
                khata_number=p["khata"],
                owner_names=p["owners"],
                father_or_husband=p.get("father_or_husband"),
                area=area_m,
                geometry={"type": "Polygon", "coordinates": [p["coords"]]},
                boundaries=p["boundaries"],
                land_use="Homestead / Gharabari / Residential",
                mutation_status=p["mutation"],
                registration_status=p["registration"],
                revenue_court_status=p["court"],
                source=src
            ))
        return result
