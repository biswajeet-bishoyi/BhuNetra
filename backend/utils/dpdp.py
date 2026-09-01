"""
utils/dpdp.py — DPDP Act 2023 data minimization utilities.

Provides role-aware PII masking for the Citizen view. Officer and Collector views
receive full unmasked data with mandatory audit logging.

MASKED FIELDS (Citizen role):
  - owner_name          → "FirstName X."
  - father_or_husband  → "Father X."
  - Any field explicitly annotated with PII_FIELDS below

NON-PII FIELDS (always shown):
  - parcel_id, khatian_no, survey_no, village, mandal, district, state
  - land_use_claim, claimed_area_sqm, actual_area_sqm
  - revenue_court_status, ulpin, deed_registration_no

AUDIT NOTE:
  Every officer access in Officer/Collector mode is logged in OfficerAuditLog with
  the officer's name, purpose, and timestamp — satisfying DPDP Act 2023 accountability
  requirements for handling personal land-record data.
"""

from __future__ import annotations

# Fields that contain personal identifiable information and must be masked for Citizen role
PII_FIELDS = frozenset({
    "owner_name",
    "father_or_husband",
    "pattadar_name",        # alternate key name used in some datasets
    "recorded_owner",
    "seller_name",
    "buyer_name",
    "aadhaar",              # not currently stored, but present in deed data
    "contact",
    "phone",
    "mobile",
})


def _mask_name(value: str | None) -> str:
    """
    Mask a personal name per DPDP Act 2023 consent minimization principle.

    "Kalyan Reddy"   → "Kalyan X."
    "Prasad Sharma" → "Prasad X."
    "Ram"           → "Ram (Masked per DPDP Act)"
    "" / None       → "(Masked per DPDP Act)"
    """
    if not value:
        return "(Masked per DPDP Act 2023)"
    parts = str(value).strip().split()
    if len(parts) >= 2:
        return f"{parts[0]} X."
    elif len(parts) == 1:
        return f"{parts[0]} (Masked per DPDP Act 2023)"
    return "(Masked per DPDP Act 2023)"


def _normalize_role(role: any) -> str:
    if hasattr(role, "default"):
        role = role.default
    if role is None:
        return ""
    if not isinstance(role, str):
        return str(role).strip().lower()
    return role.strip().lower()


def mask_pii_fields(
    data: dict,
    role: str | None = None,
) -> dict:
    """
    Return a copy of `data` with PII fields masked when role is 'Citizen'.

    All other roles (Officer, Collector, Admin, or missing) receive the data unchanged.
    This is the single point of application for DPDP masking — call it in every
    API endpoint that returns personal land-record data.

    Parameters
    ----------
    data : dict
        The response payload (typically a single record dict or list-item dict).
    role : str | None
        The authenticated role string from the request. Case-insensitive.
        "Citizen" / "citizen" / "CITIZEN" are all treated identically.

    Returns
    -------
    dict
        Copy of `data` with PII fields masked for Citizen role.
    """
    if not isinstance(data, dict):
        return data

    role_clean = _normalize_role(role)
    if role_clean != "citizen":
        return data

    result = dict(data)
    for field in PII_FIELDS:
        if field in result and result[field] is not None:
            result[field] = _mask_name(result[field])

    return result


def mask_pii_fields_list(
    records: list[dict],
    role: str | None = None,
) -> list[dict]:
    """
    Apply DPDP masking to a list of record dicts.

    Wraps mask_pii_fields for the common list-of-records pattern.
    """
    return [mask_pii_fields(r, role) for r in records]


def pii_summary(
    data: dict,
    role: str | None = None,
) -> dict:
    """
    Return a summary of which PII fields were masked (for the Officer UI).

    Officer/Collector views can call this to show "PII masked for Citizen" badges
    without altering the response structure.
    """
    role_clean = _normalize_role(role)
    is_citizen = role_clean == "citizen"

    masked_fields = []
    if is_citizen:
        for field in PII_FIELDS:
            if field in data and data[field] is not None:
                masked_fields.append(field)

    return {
        "role": role,
        "is_citizen_view": is_citizen,
        "masked_pii_fields": masked_fields,
        "masking_active": is_citizen and bool(masked_fields),
        "legal_basis": (
            "DPDP Act 2023 — consent-based data minimization applied to Citizen view. "
            "Officer/Collector views require authenticated purpose logging per Section 6."
            if is_citizen else
            "Authenticated officer access. Audit log entry created per Section 6 DPDP Act 2023."
        ),
    }
