"""
routers/alerts.py — Multi-channel citizen alert dispatch.

POST /api/alerts/whatsapp/dispatch  — WhatsApp Business API
POST /api/alerts/sms/dispatch        — Government SMS gateway (mock)

When WHATSAPP_API_TOKEN is absent or the WhatsApp API call fails, the
endpoint returns a mock delivery receipt so the UI can proceed without
breaking. The API token must be a WhatsApp Business Cloud API long-lived
access token (Meta Developer Console).

Note: in production, parcel owner phone numbers are fetched from the
registered Pattadar contact on file (not supplied by the UI caller).
The phone parameter here is a simulation convenience.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/alerts", tags=["Citizen Alert Dispatch"])
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class WhatsAppDispatchRequest(BaseModel):
    parcel_id: str
    template: str  # 'overlap' | 'rapid_resale' | 'court_stay'
    phone: str     # E.164 format: +91XXXXXXXXXX (simulation)
    owner_name: str = "Pattadar"


class SMSDispatchRequest(BaseModel):
    parcel_id: str
    template: str
    phone: str
    owner_name: str = "Pattadar"


class AlertReceipt(BaseModel):
    status: str            # DISPATCHED | MOCK_DISPATCHED | FAILED
    channel: str
    template: str
    parcel_id: str
    recipient: str          # masked phone: +91 XXXXX XXXXX
    message_id: str | None
    dispatched_at: str
    provider_response: str


# ---------------------------------------------------------------------------
# WhatsApp Business Cloud API
# ---------------------------------------------------------------------------

WHATSAPP_PHONE_ID   = os.getenv("WHATSAPP_PHONE_ID", "")
WHATSAPP_API_TOKEN  = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_API_BASE   = "https://graph.facebook.com/v20.0"

# Template bodies must be pre-registered in the Meta Business Manager.
WHATSAPP_TEMPLATES = {
    "overlap":        "bhunetra_boundary_alert",
    "rapid_resale":   "bhunetra_fraud_alert",
    "court_stay":     "bhunetra_court_notice",
}


def _mask_phone(phone: str) -> str:
    """Partially mask a phone number for audit logging."""
    if phone and len(phone) > 6:
        return phone[:4] + " XXXXX " + phone[-3:]
    return phone


async def _send_whatsapp_api(
    phone: str,
    template: str,
    header_vars: dict,
) -> tuple[str, str]:
    """
    Call the WhatsApp Business Cloud API to send a template message.

    Returns (message_id, raw_response).
    Raises HTTPException on non-retryable API errors.
    """
    if not WHATSAPP_API_TOKEN or not WHATSAPP_PHONE_ID:
        raise HTTPException(
            status_code=503,
            detail="WHATSAPP_API_TOKEN or WHATSAPP_PHONE_ID not configured"
        )

    template_name = WHATSAPP_TEMPLATES.get(template, "bhunetra_generic_alert")

    payload = {
        "messaging_product": "whatsapp",
        "to": phone.lstrip("+"),
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {"type": "text", "text": header_vars.get("parcel_id", "")}
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": header_vars.get("parcel_id", "")},
                        {"type": "text", "text": header_vars.get("risk_level", "MODERATE")},
                        {"type": "text", "text": header_vars.get("action", "Mutation held pending review")},
                    ]
                }
            ]
        }
    }

    url = f"{WHATSAPP_API_BASE}/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        msg_id = data.get("messages", [{}])[0].get("id", "")
        return msg_id, resp.text
    elif resp.status_code == 429:
        raise HTTPException(status_code=429, detail="WhatsApp API rate limit hit — retry after a short delay")
    else:
        raise HTTPException(
            status_code=502,
            detail=f"WhatsApp API error {resp.status_code}: {resp.text[:200]}"
        )


# ---------------------------------------------------------------------------
# Mock / simulation helpers
# ---------------------------------------------------------------------------

MOCK_WHATSAPP_BODY = {
    "overlap": (
        "BhuNetra Land Security Alert: Unauthorized boundary mutation on "
        "parcel {parcel_id} has been BLOCKED due to a 12.4% physical overlap "
        "with an adjacent parcel. Risk Level: HIGH (RED). Mutation placed on "
        "administrative hold pending Tahsildar field survey."
    ),
    "rapid_resale": (
        "BhuNetra Fraud Alert — Rapid Resale: Suspicious transaction velocity "
        "recorded on parcel {parcel_id}. 4 transfers within 24 days with 98% "
        "price spike. Transaction flagged for Sub-Registrar review under "
        "Anti-Benami Act."
    ),
    "court_stay": (
        "Revenue Court Litigation Notice: A Stay Order has been recorded "
        "for parcel {parcel_id} (OS-412/2026, Rangareddy Senior Civil Court). "
        "Any registry or conveyance deed will be void ab initio."
    ),
}

MOCK_SMS_BODY = {
    "overlap": (
        "GOVT-TS-LAND: Alert! Boundary overlap detected on Parcel {parcel_id} "
        "by BhuNetra AI. Mutation halted. Visit Tahsildar Shamshabad office "
        "with original passbook."
    ),
    "rapid_resale": (
        "GOVT-TS-LAND: Warning! High-frequency transfer anomaly flagged on "
        "Parcel {parcel_id}. Mutation locked pending Anti-Benami cell clearance."
    ),
    "court_stay": (
        "GOVT-TS-COURT: Stay Order active on Parcel {parcel_id} per "
        "OS-412/2026. Sale / Pattadar transfer prohibited."
    ),
}


def _build_mock_receipt(
    channel: str,
    template: str,
    parcel_id: str,
    phone: str,
    mock_message_id: str | None,
    provider_hint: str,
) -> AlertReceipt:
    return AlertReceipt(
        status="MOCK_DISPATCHED",
        channel=channel,
        template=template,
        parcel_id=parcel_id,
        recipient=_mask_phone(phone),
        message_id=mock_message_id,
        dispatched_at=datetime.utcnow().isoformat(),
        provider_response=f"[{provider_hint}] No WHATSAPP_API_TOKEN configured — returning mock receipt",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/whatsapp/dispatch", response_model=AlertReceipt)
async def dispatch_whatsapp_alert(req: WhatsAppDispatchRequest) -> AlertReceipt:
    """
    Dispatch a WhatsApp Business template message to a citizen.

    If WHATSAPP_API_TOKEN is set, calls the Meta WhatsApp Cloud API.
    Otherwise returns a mock receipt so the UI can demonstrate the flow.
    """
    header_vars = {
        "parcel_id": req.parcel_id,
        "risk_level": "HIGH (RED)" if req.template in {"overlap", "rapid_resale"} else "MEDIUM",
        "action": "Mutation held pending Tahsildar field survey",
    }

    # Attempt real API call if credentials are present
    if WHATSAPP_API_TOKEN and WHATSAPP_PHONE_ID:
        try:
            msg_id, raw = await _send_whatsapp_api(req.phone, req.template, header_vars)
            return AlertReceipt(
                status="DISPATCHED",
                channel="whatsapp",
                template=req.template,
                parcel_id=req.parcel_id,
                recipient=_mask_phone(req.phone),
                message_id=msg_id,
                dispatched_at=datetime.utcnow().isoformat(),
                provider_response=f"whatsapp_api:{msg_id}",
            )
        except HTTPException as exc:
            # Fall back to mock so the UI doesn't break on API misconfig
            log.warning("WhatsApp API call failed (%s), falling back to mock: %s", exc.status_code, exc.detail)
            return _build_mock_receipt(
                "whatsapp", req.template, req.parcel_id, req.phone,
                f"mock-{datetime.utcnow().strftime('%H%M%S%f')}",
                "WHATSAPP_API_CALL_FAILED"
            )
        except Exception as exc:
            log.error("Unexpected error calling WhatsApp API: %s", exc)
            return _build_mock_receipt(
                "whatsapp", req.template, req.parcel_id, req.phone,
                f"mock-{datetime.utcnow().strftime('%H%M%S%f')}",
                f"EXCEPTION:{type(exc).__name__}"
            )

    # No token configured — mock dispatch
    mock_id = f"mock-wa-{datetime.utcnow().strftime('%H%M%S%f')}"
    body = MOCK_WHATSAPP_BODY.get(req.template, MOCK_WHATSAPP_BODY["overlap"]).format(
        parcel_id=req.parcel_id
    )
    log.info(
        "WhatsApp mock dispatch [template=%s, parcel=%s, phone=%s]: %s",
        req.template, req.parcel_id, _mask_phone(req.phone), body[:80]
    )
    return _build_mock_receipt(
        "whatsapp", req.template, req.parcel_id, req.phone, mock_id,
        "WHATSAPP_API_TOKEN_NOT_SET"
    )


@router.post("/sms/dispatch", response_model=AlertReceipt)
async def dispatch_sms_alert(req: SMSDispatchRequest) -> AlertReceipt:
    """
    Dispatch an SMS via the configured government SMS gateway.

    Currently a mock/rule-stub — replace the implementation with a real
    SMS gateway (NIC SMS API, MSG91, etc.) in production.
    """
    body = MOCK_SMS_BODY.get(req.template, MOCK_SMS_BODY["overlap"]).format(
        parcel_id=req.parcel_id
    )
    mock_id = f"mock-sms-{datetime.utcnow().strftime('%H%M%S%f')}"
    log.info(
        "SMS mock dispatch [template=%s, parcel=%s, phone=%s]: %s",
        req.template, req.parcel_id, _mask_phone(req.phone), body[:80]
    )
    return AlertReceipt(
        status="MOCK_DISPATCHED",
        channel="sms",
        template=req.template,
        parcel_id=req.parcel_id,
        recipient=_mask_phone(req.phone),
        message_id=mock_id,
        dispatched_at=datetime.utcnow().isoformat(),
        provider_response="SMS_GATEWAY_NOT_CONFIGURED — mock receipt",
    )
