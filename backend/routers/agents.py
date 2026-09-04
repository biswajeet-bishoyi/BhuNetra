"""
backend/routers/agents.py — Endpoints for AI Agents:
1. Agno UP Bhulekh Cadastral & Land History Agent (https://upbhulekh.gov.in/#/home)
2. Agno Odisha Bhulekh RoR Intelligence Agent (https://bhulekh.ori.nic.in/RoRView.aspx)
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agno_upbhulekh_agent import run_upbhulekh_agent
from services.agno_odishabhulekh_agent import run_odishabhulekh_agent, ODISHA_DISTRICTS

router = APIRouter(prefix="", tags=["AI Agents"])


# ---------------------------------------------------------------------------
# UP Bhulekh Models & Endpoints
# ---------------------------------------------------------------------------
class UPBhulekhHistoryRequest(BaseModel):
    khasra_no: Optional[str] = Field("45", description="Khasra or Gata number")
    village: Optional[str] = Field("Dehramau", description="Village or Mauza name")
    mandal: Optional[str] = Field("Mohanlalganj", description="Tehsil or Mandal name")
    district: Optional[str] = Field("Lucknow", description="District name")
    state: Optional[str] = Field("Uttar Pradesh", description="State name")
    owner_name: Optional[str] = Field("Chhote Lal", description="Recorded or claimant owner name")
    claimed_area_sqm: Optional[float] = Field(92.94, description="Claimed area in square metres")
    document_id: Optional[int] = Field(None, description="Optional uploaded document ID")


@router.post("/agents/upbhulekh-history")
@router.post("/api/agents/upbhulekh-history")
def fetch_upbhulekh_history_endpoint(payload: UPBhulekhHistoryRequest) -> Dict[str, Any]:
    """
    Launch the Agno Framework AI Agent to fetch comprehensive cadastral records,
    12-column Khatauni data, historical mutation orders (नामांतरण आदेश), and revenue court
    dispute status from UP Bhulekh (https://upbhulekh.gov.in/#/home).
    """
    try:
        result = run_upbhulekh_agent(
            khasra_no=payload.khasra_no or "45",
            village=payload.village or "Dehramau",
            mandal=payload.mandal or "Mohanlalganj",
            district=payload.district or "Lucknow",
            state=payload.state or "Uttar Pradesh",
            owner_name=payload.owner_name or "Chhote Lal",
            claimed_area_sqm=payload.claimed_area_sqm or 92.94,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute Agno UP Bhulekh agent: {exc}"
        )


@router.get("/agents/upbhulekh-history/{khasra_no}")
@router.get("/api/agents/upbhulekh-history/{khasra_no}")
def get_upbhulekh_history_by_khasra(khasra_no: str, village: str = "Dehramau", district: str = "Lucknow") -> Dict[str, Any]:
    """Quick lookup for Khasra history on UP Bhulekh via Agno agent."""
    try:
        result = run_upbhulekh_agent(
            khasra_no=khasra_no,
            village=village,
            mandal="Mohanlalganj",
            district=district,
            state="Uttar Pradesh",
            owner_name="Chhote Lal",
            claimed_area_sqm=92.94,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Odisha Bhulekh Models & Endpoints
# ---------------------------------------------------------------------------
class OdishaBhulekhRequest(BaseModel):
    khata_no: Optional[str] = Field("145/12", description="Khata / Khatian Number (ଖାତା ନଂ)")
    plot_no: Optional[str] = Field("1024/2", description="Plot / Chaka Number (ପ୍ଲଟ୍ ନଂ)")
    village: Optional[str] = Field("Patia", description="Village / Mouza Name (ମୌଜା)")
    tahasil: Optional[str] = Field("Bhubaneswar", description="Tahasil Name (ତହସିଲ)")
    district: Optional[str] = Field("Khordha", description="District Name (ଜିଲ୍ଲା)")
    tenant_name: Optional[str] = Field("Bishnu Charan Das", description="Tenant / Rayat Name (ରୟତଙ୍କ ନାମ)")
    claimed_area_decimals: Optional[float] = Field(15.0, description="Claimed area in Decimals (ଡେସିମିଲି)")
    document_id: Optional[int] = Field(None, description="Optional uploaded document ID")


@router.post("/agents/odisha-bhulekh")
@router.post("/api/agents/odisha-bhulekh")
def fetch_odisha_bhulekh_endpoint(payload: OdishaBhulekhRequest) -> Dict[str, Any]:
    """
    Launch the Agno Framework AI Agent to fetch official Record of Rights (RoR / ସ୍ୱତ୍ତ୍ୱ ଲିପି)
    Front Page & Back Page, Plot Kissam (Gharabari, Sarada, Gochar), Sthitiban tenure rights,
    and Mutation History from Odisha Bhulekh (https://bhulekh.ori.nic.in/RoRView.aspx).
    """
    try:
        result = run_odishabhulekh_agent(
            khata_no=payload.khata_no or "145/12",
            plot_no=payload.plot_no or "1024/2",
            village=payload.village or "Patia",
            tahasil=payload.tahasil or "Bhubaneswar",
            district=payload.district or "Khordha",
            tenant_name=payload.tenant_name or "Bishnu Charan Das",
            claimed_area_decimals=payload.claimed_area_decimals or 15.0
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute Agno Odisha Bhulekh agent: {exc}"
        )


@router.get("/agents/odisha-bhulekh/{khata_no}")
@router.get("/api/agents/odisha-bhulekh/{khata_no}")
def get_odisha_bhulekh_by_khata(
    khata_no: str,
    plot_no: str = "1024/2",
    village: str = "Patia",
    tahasil: str = "Bhubaneswar",
    district: str = "Khordha"
) -> Dict[str, Any]:
    """Quick lookup for Odisha RoR by Khata number."""
    try:
        result = run_odishabhulekh_agent(
            khata_no=khata_no,
            plot_no=plot_no,
            village=village,
            tahasil=tahasil,
            district=district,
            tenant_name="Bishnu Charan Das",
            claimed_area_decimals=15.0
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/agents/odisha-districts")
@router.get("/api/agents/odisha-districts")
def get_odisha_districts_master() -> Dict[str, Any]:
    """Get the master list of Odisha districts and tahasils for UI dropdowns."""
    return {
        "portal_source": "https://bhulekh.ori.nic.in/RoRView.aspx",
        "state": "Odisha",
        "districts": ODISHA_DISTRICTS
    }
