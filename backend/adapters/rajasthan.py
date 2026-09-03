"""
rajasthan.py — Rajasthan State Land Administration Adapter (Apna Khata / E-Dharti).

Implements Rajasthan specific land records hierarchy:
State (Rajasthan) -> District (Bhilwara) -> Tehsil (Mandalgarh) -> Village (Mandalgarh Rural / ABC Village)
Primary Identifier: Khasra Number
Account Reference: Khata Number
"""

from typing import Any, Dict, List
from adapters.base import StateAdapter, CanonicalParcel, CanonicalIdentifier, AreaModel


class RajasthanAdapter(StateAdapter):
    def __init__(self):
        super().__init__(
            name="Rajasthan",
            state_code="RJ",
            portal_name="Apna Khata (E-Dharti)",
            authority="Board of Revenue, Government of Rajasthan",
            location_hierarchy=["state", "district", "tehsil", "village"],
            primary_identifier_type="khasra_number",
            identifier_synonyms=["khasra", "khasra_no", "khasra number", "khasra no."],
            account_synonyms=["khata", "khata_number", "khatauni", "khewat"],
            unit_to_sqm_table={
                "hectare": 10000.0,
                "ha": 10000.0,
                "bigha": 2500.0,
                "biswa": 125.0,
                "sq ft": 0.092903,
                "sq yd": 0.836127,
                "acre": 4046.86
            }
        )

    def get_supported_locations(self) -> Dict[str, Any]:
        return {
            "state": "Rajasthan",
            "districts": {
                "Bhilwara": {
                    "tehsils": {
                        "Mandalgarh": ["Mandalgarh Rural", "ABC Village", "Kasya", "Jhalra"],
                        "Kotri": ["Kotri Rural", "Sardargarh"]
                    }
                },
                "Jaipur": {
                    "tehsils": {
                        "Sanganer": ["Sanganer Rural", "Sitapura"],
                        "Amer": ["Amer Rural", "Kukas"]
                    }
                }
            }
        }

    def load_parcels(self) -> List[CanonicalParcel]:
        # Center coordinates around Mandalgarh, Bhilwara District (25.215° N, 75.095° E)
        src = self.get_source_metadata(is_demo=True)
        parcels_data = [
            {
                "parcel_id": "RJ-124-2",
                "khasra": "124/2",
                "khata": "57",
                "village": "ABC Village",
                "tehsil": "Mandalgarh",
                "district": "Bhilwara",
                "owners": ["Ramcharan Sharma"],
                "father_or_husband": "Shankar Lal Sharma",
                "area_val": 0.84,
                "area_unit": "hectare",
                "area_sqm": 8400.0,
                "coords": [
                    [75.09450, 25.21480],
                    [75.09545, 25.21485],
                    [75.09540, 25.21575],
                    [75.09445, 25.21570],
                    [75.09450, 25.21480]
                ],
                "boundaries": {
                    "north": "Road / Rasta",
                    "south": "Khasra 124/1 (Rameshwar Lal)",
                    "east": "Irrigation Canal / Nahar",
                    "west": "Khasra 125/1 (Suresh Chandra)"
                },
                "mutation": "Clean",
                "registration": "Registered",
                "court": "Clean"
            },
            {
                "parcel_id": "RJ-124-1",
                "khasra": "124/1",
                "khata": "57",
                "village": "ABC Village",
                "tehsil": "Mandalgarh",
                "district": "Bhilwara",
                "owners": ["Rameshwar Lal Gurjar"],
                "father_or_husband": "Deva Gurjar",
                "area_val": 0.45,
                "area_unit": "hectare",
                "area_sqm": 4500.0,
                "coords": [
                    [75.09455, 25.21390],
                    [75.09550, 25.21395],
                    [75.09545, 25.21485],
                    [75.09450, 25.21480],
                    [75.09455, 25.21390]
                ],
                "boundaries": {
                    "north": "Khasra 124/2 (Ramcharan Sharma)",
                    "south": "Village Boundary",
                    "east": "Irrigation Canal",
                    "west": "Khasra 125/2"
                },
                "mutation": "Clean",
                "registration": "Registered",
                "court": "Clean"
            },
            {
                "parcel_id": "RJ-124-3",
                "khasra": "124/3",
                "khata": "58",
                "village": "ABC Village",
                "tehsil": "Mandalgarh",
                "district": "Bhilwara",
                "owners": ["Mohan Lal Jat"],
                "father_or_husband": "Kalu Jat",
                "area_val": 0.81,
                "area_unit": "hectare",
                "area_sqm": 8100.0,
                "coords": [
                    [75.09545, 25.21485],
                    [75.09640, 25.21490],
                    [75.09635, 25.21580],
                    [75.09540, 25.21575],
                    [75.09545, 25.21485]
                ],
                "boundaries": {
                    "north": "Road / Rasta",
                    "south": "Drainage Nala",
                    "east": "Khasra 123",
                    "west": "Khasra 124/2"
                },
                "mutation": "Pending",
                "registration": "Registered",
                "court": "Clean"
            },
            {
                "parcel_id": "RJ-125-1",
                "khasra": "125/1",
                "khata": "59",
                "village": "ABC Village",
                "tehsil": "Mandalgarh",
                "district": "Bhilwara",
                "owners": ["Suresh Chandra Meena"],
                "father_or_husband": "Bhairu Meena",
                "area_val": 0.92,
                "area_unit": "hectare",
                "area_sqm": 9200.0,
                "coords": [
                    [75.09350, 25.21475],
                    [75.09445, 25.21480],
                    [75.09440, 25.21570],
                    [75.09345, 25.21565],
                    [75.09350, 25.21475]
                ],
                "boundaries": {
                    "north": "Road / Rasta",
                    "south": "Khasra 125/2",
                    "east": "Khasra 124/2",
                    "west": "Panchayat Pasture Land"
                },
                "mutation": "Clean",
                "registration": "Registered",
                "court": "Clean"
            }
        ]

        result = []
        for p in parcels_data:
            c_ident = CanonicalIdentifier(
                type="khasra_number",
                value=self.normalize_identifier(p["khasra"]),
                source_type="Khasra Number",
                source_value=p["khasra"]
            )
            area_m = AreaModel(value=p["area_val"], unit=p["area_unit"], sqm=p["area_sqm"])
            result.append(CanonicalParcel(
                parcel_id=p["parcel_id"],
                state="Rajasthan",
                district=p["district"],
                subdistrict=p["tehsil"],
                village=p["village"],
                identifier=c_ident,
                khata_number=p["khata"],
                owner_names=p["owners"],
                father_or_husband=p.get("father_or_husband"),
                area=area_m,
                geometry={"type": "Polygon", "coordinates": [p["coords"]]},
                boundaries=p["boundaries"],
                land_use="Agricultural",
                mutation_status=p["mutation"],
                registration_status=p["registration"],
                revenue_court_status=p["court"],
                source=src
            ))
        return result
