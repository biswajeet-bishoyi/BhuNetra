from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication & Role Management"])

class LoginRequest(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str
    jurisdiction: str
    badge_number: str

DEMO_USERS = {
    "collector@rangareddy.gov.in": {
        "id": "USR-COL-001",
        "name": "Dr. S. K. Ramanathan, IAS",
        "email": "collector@rangareddy.gov.in",
        "role": "District Collector",
        "jurisdiction": "Rangareddy District, Telangana",
        "badge_number": "IAS-TS-2014-998",
        "password": "Demo@1234"
    },
    "tahsildar.shamshabad@telangana.gov.in": {
        "id": "USR-REV-042",
        "name": "M. Praveen Kumar, Tahsildar",
        "email": "tahsildar.shamshabad@telangana.gov.in",
        "role": "Revenue Officer",
        "jurisdiction": "Shamshabad Mandal",
        "badge_number": "TS-REV-SHM-402",
        "password": "Demo@1234"
    },
    "kalyan.reddy@citizen.in": {
        "id": "USR-CIT-105",
        "name": "Kalyan Reddy (Pattadar)",
        "email": "kalyan.reddy@citizen.in",
        "role": "Citizen",
        "jurisdiction": "Shamshabad Village",
        "badge_number": "DHARANI-PP-78431",
        "password": "Demo@1234"
    }
}

@router.post("/login")
def login(req: LoginRequest):
    email_clean = req.email.strip().lower()
    
    # Check demo users
    user = DEMO_USERS.get(email_clean)
    if user and req.password == user["password"]:
        return {
            "success": True,
            "message": f"Welcome back, {user['name']}",
            "token": f"bhunetra_jwt_token_{user['id']}_{int(datetime.now(timezone.utc).timestamp())}",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "jurisdiction": user["jurisdiction"],
                "badge_number": user["badge_number"]
            }
        }
    
    # Generic fallback authentication for custom input
    if "@" in req.email and len(req.password) >= 4:
        role_guess = "Citizen"
        if "collector" in email_clean or "admin" in email_clean:
            role_guess = "District Collector"
        elif "tahsildar" in email_clean or "officer" in email_clean or "rev" in email_clean:
            role_guess = "Revenue Officer"
            
        return {
            "success": True,
            "message": "Authenticated successfully.",
            "token": f"bhunetra_jwt_token_custom_{int(datetime.now(timezone.utc).timestamp())}",
            "user": {
                "id": "USR-CUSTOM-009",
                "name": email_clean.split("@")[0].capitalize(),
                "email": email_clean,
                "role": role_guess,
                "jurisdiction": "Telangana State",
                "badge_number": "TS-AUTH-DEMO"
            }
        }
        
    raise HTTPException(status_code=401, detail="Invalid officer credentials. Use demo fast-fill accounts.")
