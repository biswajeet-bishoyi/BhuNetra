"""
backend/routers/agents.py — Endpoints for AI Agents (Agno UP Bhulekh Cadastral & Land History Agent).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agno_upbhulekh_agent import run_upbhulekh_agent

router = APIRouter(prefix="", tags=["AI Agents"])


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
