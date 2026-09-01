"""
test_documents_lifecycle.py — Phase 3 state machine verification.

Proves the document lifecycle enforces valid transitions and rejects illegal ones,
without needing the FastAPI server or the OCR engine.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from models import Document  # noqa: E402

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


def test_initial_state():
    print("\n[1] Initial state")
    d = Document(source_filename="scan_P-101.png")
    check("default status is UPLOADED", d.status == "UPLOADED", d.status)
    check("source filename recorded", d.source_filename == "scan_P-101.png")
    check("extraction passes starts at 0", d.extraction_passes == 0)
    check("extraction confidence starts at 0.0", d.extraction_confidence == 0.0)


def test_valid_transitions():
    print("\n[2] Valid transitions")
    d = Document(source_filename="x.png", status="UPLOADED")
    check("UPLOADED can transition to EXTRACTED", d.can_transition_to("EXTRACTED"))
    check("UPLOADED can transition to NEEDS_REVIEW", d.can_transition_to("NEEDS_REVIEW"))
    check("UPLOADED CANNOT go to VERIFIED directly", not d.can_transition_to("VERIFIED"))
    check("UPLOADED CANNOT go to APPROVED directly", not d.can_transition_to("APPROVED"))

    d.status = "EXTRACTED"
    check("EXTRACTED can go to NEEDS_REVIEW", d.can_transition_to("NEEDS_REVIEW"))
    check("EXTRACTED can go to VERIFIED", d.can_transition_to("VERIFIED"))
    check("EXTRACTED CANNOT go directly to APPROVED", not d.can_transition_to("APPROVED"))

    d.status = "NEEDS_REVIEW"
    check("NEEDS_REVIEW can go to VERIFIED", d.can_transition_to("VERIFIED"))
    check("NEEDS_REVIEW can go to REJECTED", d.can_transition_to("REJECTED"))
    check("NEEDS_REVIEW CANNOT go back to UPLOADED", not d.can_transition_to("UPLOADED"))

    d.status = "VERIFIED"
    check("VERIFIED can go to APPROVED", d.can_transition_to("APPROVED"))
    check("VERIFIED CANNOT go back to NEEDS_REVIEW", not d.can_transition_to("NEEDS_REVIEW"))
    check("VERIFIED CANNOT go to REJECTED", not d.can_transition_to("REJECTED"))

    d.status = "APPROVED"
    check("APPROVED is terminal (no transitions)", d.valid_transitions()["APPROVED"] == set())
    d.status = "REJECTED"
    check("REJECTED is terminal (no transitions)", d.valid_transitions()["REJECTED"] == set())


def test_transition_method_enforces_state_machine():
    print("\n[3] transition_to() blocks illegal moves")
    d = Document(source_filename="x.png", status="UPLOADED")
    d.transition_to("EXTRACTED")
    check("UPLOADED -> EXTRACTED succeeds", d.status == "EXTRACTED")

    d.transition_to("VERIFIED")
    check("EXTRACTED -> VERIFIED succeeds", d.status == "VERIFIED")

    d.transition_to("APPROVED")
    check("VERIFIED -> APPROVED succeeds", d.status == "APPROVED")

    try:
        d.transition_to("NEEDS_REVIEW")
        check("APPROVED -> NEEDS_REVIEW should be rejected", False)
    except ValueError:
        check("APPROVED -> NEEDS_REVIEW is rejected with ValueError", True)

    check("approved state is still APPROVED after rejected transition", d.status == "APPROVED")


def test_full_happy_path():
    print("\n[4] Full UPLOADED -> APPROVED happy path")
    d = Document(source_filename="scan.png")
    d.transition_to("EXTRACTED")
    d.transition_to("VERIFIED")
    d.transition_to("APPROVED")
    check("ends in APPROVED", d.status == "APPROVED")


def test_review_branch_rejected():
    print("\n[5] NEEDS_REVIEW -> REJECTED branch")
    d = Document(source_filename="scan.png", status="NEEDS_REVIEW")
    d.transition_to("REJECTED")
    check("ends in REJECTED", d.status == "REJECTED")
    try:
        d.transition_to("APPROVED")
        check("REJECTED -> APPROVED should be rejected", False)
    except ValueError:
        check("REJECTED is terminal; APPROVED rejected", True)


def test_columns_present():
    print("\n[6] Required columns for state persistence")
    cols = {c.name for c in Document.__table__.columns}
    required = [
        "id", "source_filename", "file_hash", "status", "parcel_id",
        "parcel_id_hint", "extraction_result", "extracted_fields",
        "extraction_confidence", "low_confidence_fields", "extraction_timestamp",
        "reviewed_by", "reviewed_at", "review_reason", "officer_corrections",
        "blockchain_hash", "blockchain_timestamp",
    ]
    for r in required:
        check(f"column '{r}' present", r in cols, str(cols))


if __name__ == "__main__":
    print("BhuNetra Phase 3 — Document lifecycle state machine")
    print("=" * 62)
    test_initial_state()
    test_valid_transitions()
    test_transition_method_enforces_state_machine()
    test_full_happy_path()
    test_review_branch_rejected()
    test_columns_present()
    print("=" * 62)
    print(f"{_checks - len(_failures)}/{_checks} checks passed")
    if _failures:
        print("FAILED: " + ", ".join(_failures))
    raise SystemExit(1 if _failures else 0)
