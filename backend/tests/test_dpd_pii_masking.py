"""
test_dpd_pii_masking.py — DPDP Act 2023 masking verification.

Proves the PII masking utility correctly handles all documented name patterns.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from utils.dpdp import mask_pii_fields, mask_pii_fields_list, _mask_name, pii_summary  # noqa: E402

_checks = 0
_failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    global _checks
    _checks += 1
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}   {detail}")
        _failures.append(label)


def test_mask_name_two_parts():
    print("\n[1] Two-part names")
    check("'Kalyan Reddy' -> 'Kalyan X.'",
          _mask_name("Kalyan Reddy") == "Kalyan X.")
    check("'Prasad Sharma' -> 'Prasad X.'",
          _mask_name("Prasad Sharma") == "Prasad X.")
    check("'Ravi Kumar' -> 'Ravi X.'",
          _mask_name("Ravi Kumar") == "Ravi X.")


def test_mask_name_single_part():
    print("\n[2] Single-part names")
    check("'Ram' → 'Ram (Masked per DPDP Act 2023)'",
          _mask_name("Ram") == "Ram (Masked per DPDP Act 2023)")


def test_mask_name_empty():
    print("\n[3] Empty and null values")
    check("'' → '(Masked per DPDP Act 2023)'", _mask_name("") == "(Masked per DPDP Act 2023)")
    check("None → '(Masked per DPDP Act 2023)'", _mask_name(None) == "(Masked per DPDP Act 2023)")


def test_mask_pii_fields_citizen():
    print("\n[4] mask_pii_fields: Citizen role")
    data = {
        "parcel_id": "P-105",
        "owner_name": "Kalyan Reddy",
        "father_or_husband": "Ravi Reddy",
        "village": "Shamshabad",
        "claimed_area_sqm": 15075.63,
    }
    masked = mask_pii_fields(data, "Citizen")
    check("owner_name masked for Citizen", masked["owner_name"] == "Kalyan X.", masked["owner_name"])
    check("father_or_husband masked for Citizen", masked["father_or_husband"] == "Ravi X.", masked["father_or_husband"])
    check("parcel_id NOT masked", masked["parcel_id"] == "P-105")
    check("village NOT masked", masked["village"] == "Shamshabad")
    check("claimed_area_sqm NOT masked", masked["claimed_area_sqm"] == 15075.63)


def test_mask_pii_fields_officer():
    print("\n[5] mask_pii_fields: Officer role (no masking)")
    data = {"owner_name": "Kalyan Reddy", "village": "Shamshabad"}
    clean = mask_pii_fields(data, "Revenue Officer")
    check("owner_name NOT masked for Officer", clean["owner_name"] == "Kalyan Reddy")
    check("village NOT masked for Officer", clean["village"] == "Shamshabad")


def test_mask_pii_fields_collector():
    print("\n[6] mask_pii_fields: Collector role (no masking)")
    data = {"owner_name": "Kalyan Reddy"}
    clean = mask_pii_fields(data, "District Collector")
    check("owner_name NOT masked for Collector", clean["owner_name"] == "Kalyan Reddy")


def test_mask_pii_fields_no_role():
    print("\n[7] mask_pii_fields: no role (no masking)")
    data = {"owner_name": "Kalyan Reddy"}
    clean = mask_pii_fields(data, None)
    check("owner_name NOT masked when role is None", clean["owner_name"] == "Kalyan Reddy")


def test_mask_pii_fields_case_insensitive():
    print("\n[8] mask_pii_fields: case-insensitive role")
    data = {"owner_name": "Kalyan Reddy"}
    masked = mask_pii_fields(data, "CITIZEN")
    check("'CITIZEN' triggers masking", masked["owner_name"] == "Kalyan X.")
    clean = mask_pii_fields(data, "citizen")
    check("'citizen' triggers masking", clean["owner_name"] == "Kalyan X.")


def test_mask_pii_fields_list():
    print("\n[9] mask_pii_fields_list: batch masking")
    records = [
        {"owner_name": "Kalyan Reddy", "village": "Shamshabad"},
        {"owner_name": "Prasad Sharma", "village": "Mamidipally"},
    ]
    masked = mask_pii_fields_list(records, "Citizen")
    check("first record owner masked", masked[0]["owner_name"] == "Kalyan X.")
    check("first record village not masked", masked[0]["village"] == "Shamshabad")
    check("second record owner masked", masked[1]["owner_name"] == "Prasad X.")
    check("second record village not masked", masked[1]["village"] == "Mamidipally")


def test_pii_summary():
    print("\n[10] pii_summary: context disclosure")
    data = {"owner_name": "Kalyan Reddy", "village": "Shamshabad"}
    ctx = pii_summary(data, "Citizen")
    check("citizen view flagged", ctx["is_citizen_view"] is True)
    check("owner_name listed as masked", "owner_name" in ctx["masked_pii_fields"])
    check("village NOT listed as masked", "village" not in ctx["masked_pii_fields"])
    check("masking_active True for Citizen", ctx["masking_active"] is True)

    ctx2 = pii_summary(data, "Revenue Officer")
    check("officer view flagged", ctx2["is_citizen_view"] is False)
    check("masking_active False for Officer", ctx2["masking_active"] is False)


if __name__ == "__main__":
    print("BhuNetra DPDP Act 2023 — PII masking tests")
    print("=" * 62)
    test_mask_name_two_parts()
    test_mask_name_single_part()
    test_mask_name_empty()
    test_mask_pii_fields_citizen()
    test_mask_pii_fields_officer()
    test_mask_pii_fields_collector()
    test_mask_pii_fields_no_role()
    test_mask_pii_fields_case_insensitive()
    test_mask_pii_fields_list()
    test_pii_summary()
    print("=" * 62)
    print(f"{_checks - len(_failures)}/{_checks} checks passed")
    if _failures:
        print("FAILED: " + ", ".join(_failures))
    raise SystemExit(1 if _failures else 0)
