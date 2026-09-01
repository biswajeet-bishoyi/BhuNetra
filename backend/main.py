import sys
import os
import threading

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from services import extraction_service
from routers import (
    gis,
    ocr,
    ownership,
    satellite,
    risk_ensemble,
    review_queue,
    revenue_court,
    blockchain,
    documents,
    certificate,
    auth,
    analytics,
    mutations
)

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BhuNetra AI — Land Record Verification & Decision Support System",
    description="SIH 2026 Problem Statement SIH26018 (Ministry of Rural Development) - Verification layer on top of DILRMP digitized records.",
    version="1.0.0"
)

# CORS middleware setup for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router Engines
app.include_router(ocr.router, prefix="/api")
app.include_router(gis.router, prefix="/api")
app.include_router(ownership.router, prefix="/api")
app.include_router(satellite.router, prefix="/api")
app.include_router(risk_ensemble.router, prefix="/api")
app.include_router(review_queue.router, prefix="/api")
app.include_router(revenue_court.router, prefix="/api")
app.include_router(blockchain.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(certificate.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

# Also include routes without /api prefix for backward compatibility
app.include_router(ocr.router)
app.include_router(gis.router)
app.include_router(ownership.router)
app.include_router(satellite.router)
app.include_router(risk_ensemble.router)
app.include_router(review_queue.router)
app.include_router(revenue_court.router)
app.include_router(blockchain.router)
app.include_router(documents.router)
app.include_router(certificate.router)
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(mutations.router)
app.include_router(mutations.router, prefix="/api")

# Serve synthetic scan files and satellite images
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
if os.path.exists(data_dir):
    app.mount("/static-data", StaticFiles(directory=data_dir), name="static-data")

@app.on_event("startup")
def warm_extraction_engine():
    """Pre-load the vision model into VRAM in the background.

    Runs off-thread so an offline/absent Ollama never blocks or breaks boot — the
    engine badge in the UI (GET /api/ocr/engine-status) reports the truth either way.
    """
    def _warm():
        status = extraction_service.engine_status()
        if status["model_available"]:
            extraction_service.warm_model()
            print(f"[extraction] warm: {status['engine_tag']}")
        else:
            print(f"[extraction] UNAVAILABLE — {status['hint']}")

    threading.Thread(target=_warm, name="warm-extraction", daemon=True).start()


@app.get("/")
def root():
    return {
        "system": "BhuNetra AI",
        "sih_problem_statement": "SIH26018",
        "ministry": "Ministry of Rural Development",
        "positioning": "Verification & Decision Support Layer on top of DILRMP digitized records",
        "status": "OPERATIONAL",
        "extraction_engine": extraction_service.engine_status(),
        "spatial_architecture": "In-memory GeoPandas/Shapely STRtree processing (Zero SpatiaLite extension required)",
        "production_scale_upgrade": "PostGIS",
        "compliance": {
            "dpdp_act_2023": "Consent-based data minimization & PII masking for Citizen role",
            "it_act_2000_sec_65b": "Digital record admissibility via timestamped SHA-256 approval hashing",
            "registration_act_1908": "Cryptographic hash verifies audit trail integrity without replacing registered deeds"
        }
    }
