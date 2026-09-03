"""
adapters/__init__.py — Registry and Factory for Indian State Land Administration Adapters.
"""

from typing import Any, Dict, List, Optional
from adapters.base import StateAdapter, CanonicalParcel
from adapters.rajasthan import RajasthanAdapter
from adapters.maharashtra import MaharashtraAdapter
from adapters.telangana import TelanganaAdapter
from adapters.tamil_nadu import TamilNaduAdapter
from adapters.generic import GenericStateAdapter

_ADAPTER_INSTANCES: Dict[str, StateAdapter] = {
    "rajasthan": RajasthanAdapter(),
    "maharashtra": MaharashtraAdapter(),
    "telangana": TelanganaAdapter(),
    "tamil nadu": TamilNaduAdapter(),
    "odisha": GenericStateAdapter("Odisha"),
    "delhi": GenericStateAdapter("Delhi"),
}

_STATE_ALIAS_MAP: Dict[str, str] = {
    "rj": "rajasthan",
    "raj": "rajasthan",
    "rajasthan": "rajasthan",
    "bhilwara": "rajasthan",
    "mandalgarh": "rajasthan",

    "mh": "maharashtra",
    "maha": "maharashtra",
    "maharashtra": "maharashtra",
    "pune": "maharashtra",
    "haveli": "maharashtra",

    "ts": "telangana",
    "telangana": "telangana",
    "hyderabad": "telangana",
    "shamshabad": "telangana",
    "rangareddy": "telangana",

    "tn": "tamil nadu",
    "tamil": "tamil nadu",
    "tamil nadu": "tamil nadu",
    "tamilnadu": "tamil nadu",
    "chennai": "tamil nadu",
    "kanchipuram": "tamil nadu",
    "coimbatore": "tamil nadu",
    "madurai": "tamil nadu",
    "sriperumbudur": "tamil nadu",
    "patta": "tamil nadu",
    "chitta": "tamil nadu",

    "od": "odisha",
    "orissa": "odisha",
    "odisha": "odisha",
    "khordha": "odisha",
    "khurda": "odisha",
    "bhubaneswar": "odisha",

    "dl": "delhi",
    "delhi": "delhi",
    "new delhi": "delhi",
}


def get_adapter(state_or_hint: Optional[str]) -> StateAdapter:
    """Resolve and return the appropriate StateAdapter based on state name, code, or district hint."""
    if not state_or_hint:
        return _ADAPTER_INSTANCES["rajasthan"]  # default

    query = state_or_hint.lower().strip()
    # Direct alias match
    if query in _STATE_ALIAS_MAP:
        key = _STATE_ALIAS_MAP[query]
        return _ADAPTER_INSTANCES.get(key, GenericStateAdapter(state_or_hint))

    # Partial substring search
    for alias, key in _STATE_ALIAS_MAP.items():
        if alias in query:
            return _ADAPTER_INSTANCES.get(key, GenericStateAdapter(state_or_hint))

    # Fallback to generic adapter
    return GenericStateAdapter(state_or_hint.title())


def list_supported_adapters() -> List[Dict[str, Any]]:
    """List all supported state adapters with portal names and authorities."""
    result = []
    for key, adapter in _ADAPTER_INSTANCES.items():
        result.append({
            "key": key,
            "state": adapter.name,
            "state_code": adapter.state_code,
            "portal": adapter.portal_name,
            "authority": adapter.authority,
            "hierarchy": adapter.location_hierarchy,
            "primary_identifier": adapter.primary_identifier_type
        })
    return result


def get_all_parcels_across_states() -> List[CanonicalParcel]:
    """Aggregate all cadastral parcels from all registered state adapters."""
    all_parcels = []
    for adapter in _ADAPTER_INSTANCES.values():
        all_parcels.extend(adapter.load_parcels())
    return all_parcels
