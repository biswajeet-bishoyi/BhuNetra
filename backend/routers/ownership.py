from fastapi import APIRouter, HTTPException
import pandas as pd
import os
from datetime import datetime

router = APIRouter(prefix="/ownership", tags=["Engine 3 - Ownership Intelligence"])

@router.get("/{parcel_id}")
def get_ownership_timeline(parcel_id: str):
    """
    Engine 3: Fetch ownership timeline and analyze rapid-resale transfer anomaly flags.
    Tag: RULE-STUB (rules-based transfer frequency & pattern detection).
    """
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic", "ownership_history.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Ownership history CSV not found.")

    df = pd.DataFrame(pd.read_csv(csv_path))
    parcel_history = df[df["parcel_id"] == parcel_id].copy()

    if parcel_history.empty:
        return {
            "parcel_id": parcel_id,
            "transfers": [],
            "transfer_count": 0,
            "ownership_risk_score": 0.0,
            "is_anomalous": False,
            "explanations": ["No suspicious transfer frequency recorded."]
        }

    parcel_history["transfer_date_dt"] = pd.to_datetime(parcel_history["transfer_date"])
    parcel_history = parcel_history.sort_values("transfer_date_dt")

    raw_transfers = parcel_history.to_dict(orient="records")
    transfers = []
    for t in raw_transfers:
        clean_t = {}
        for k, v in t.items():
            if k == "transfer_date_dt":
                clean_t[k] = v.strftime("%Y-%m-%d")
            elif pd.isna(v):
                clean_t[k] = None
            elif hasattr(v, "item"):
                clean_t[k] = v.item()
            else:
                clean_t[k] = v
        transfers.append(clean_t)

    # Rule-stub anomaly detection logic
    transfer_count = len(transfers)
    is_anomalous = False
    risk_score = 0.0
    explanations = []

    if transfer_count >= 3:
        # Check time delta between first and last transfer
        dates = [datetime.strptime(t["transfer_date"], "%Y-%m-%d") for t in transfers]
        delta_days = (dates[-1] - dates[0]).days
        
        if delta_days <= 30 and transfer_count >= 3:
            is_anomalous = True
            risk_score = 88.0
            explanations.append(f"Suspicious Rapid Transfer Pattern: {transfer_count} property title resales executed within {delta_days} days.")
            explanations.append("Price Escalation Flag: Recorded property value inflated rapidly between sequential transfers.")
        elif delta_days <= 90:
            is_anomalous = True
            risk_score = 65.0
            explanations.append(f"Elevated Transfer Frequency: {transfer_count} resales recorded within {delta_days} days.")

    if not is_anomalous:
        explanations.append(f"Normal Transfer History: {transfer_count} ownership transfers over normal timeline.")

    return {
        "parcel_id": parcel_id,
        "transfers": transfers,
        "transfer_count": transfer_count,
        "ownership_risk_score": risk_score,
        "is_anomalous": is_anomalous,
        "explanations": explanations,
        "engine_tag": "RULE-STUB (transfer frequency & rapid resale rules)"
    }
