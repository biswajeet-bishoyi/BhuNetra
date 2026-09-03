# BhuNetra AI — Comprehensive Product Requirements Document (PRD)
### AI-Powered Land Record Verification & Decision Support Platform
**Smart India Hackathon (SIH 2026) · Problem Statement SIH26018 · Ministry of Rural Development**

---

## 1. Executive Summary & Core Value Proposition

### 1.1 The Real Problem
Under the Digital India Land Records Modernization Programme (DILRMP), India has digitized ~95% of its cadastral maps and Records of Rights (RoR), alongside rolling out the Unique Land Parcel Identification Number (ULPIN / Bhu-Aadhaar).

However, **digitization alone does not establish trust**:
- Over **66% of all civil cases** pending before Indian courts are land and property disputes.
- Historical boundary overlaps, sliver gaps, and area calculation discrepancies were digitized directly into state GIS systems without topology validation.
- Fraudulent deeds, illegal sub-divisions, rapid benami transfers, and ghost transactions remain undetected because registries lack an automated spatial and title verification layer.
- Existing blockchain proposals only secure records *after* entry; they do nothing to verify whether the incoming data was genuine, accurate, or physically consistent with ground reality.

### 1.2 What BhuNetra AI Is
**BhuNetra AI is not a replacement for DILRMP or the Registration Act.**  
It is an intelligent, automated **pre-transaction and pre-mutation decision-support layer** that plugs directly into existing land administration workflows. It analyzes deed scans, cadastral GIS layers, ownership transaction chains, and satellite imagery to give revenue officers, citizens, and collectors an explainable, risk-scored assessment before any land transaction is finalized.

---

## 2. System Architecture & 5-Engine Core

BhuNetra is organized around **5 specialized verification engines** orchestrated by an explainable AI ensemble:

```
                                  ┌───────────────────────────────┐
                                  │   Uploaded Document / Deed    │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                    [Engine 1: Registry OCR]
                                 Local VLM / Layout Extraction
                                                  │
                                                  ▼
                                      Document-to-Cadastre Bridge
                                  (Dynamic Plot Generation & GIS)
                                                  │
                  ┌───────────────────────────────┼───────────────────────────────┐
                  │                               │                               │
                  ▼                               ▼                               ▼
       [Engine 2: GIS Spatial]        [Engine 3: Ownership]           [Engine 4: Satellite]
       In-Memory Topology Checks      Graph Resale & Benami           Sentinel-2 L2A Tile
       Overlaps, Gaps, Deviation      Circular Chain Detector         Land-Use Verification
                  │                               │                               │
                  └───────────────────────────────┼───────────────────────────────┘
                                                  │
                                                  ▼
                                  [Engine 5: Fraud Risk Ensemble]
                                    Deterministic Weighted Model:
                              35% GIS + 25% Ownership + 25% Sat + 15% OCR
                                                  │
                                                  ▼
                                      Explainable Risk Score
                                  (Green <30 | Yellow 30-64 | Red ≥65)
                                                  │
                                                  ▼
                                      Officer Review Queue
                                   (IT Act Sec 65B Certificate)
```

---

### 2.1 Engine 1: Registry OCR & Layout Extraction
- **Role**: Ingests scanned or photographed property documents (e.g., General Power of Attorney, Registered Sale Deeds, Dharani RoRs).
- **Architecture**:
  - Primary: Local on-device Vision-Language Model (`qwen2.5vl:3b` via Ollama) for zero-cloud data sovereignty.
  - Fallback Engine: Calibrated layout and heuristic extraction engine that guarantees instantaneous processing (<400ms) with per-field confidence scoring.
  - Multi-pass cross-verification: Single-pass fast read or dual-pass consistency cross-check when field confidence is marginal (<0.85).
- **Document-to-Cadastre Bridge & Pan-India Geocoding (`uploaded_parcels.py`)**:
  - Automatically resolves real geographical coordinates across Indian jurisdictions:
    - **Odisha (Bhubaneswar, Khordha, Cuttack, Puri, Chandrasekharpur, Patia)**: Resolves to Bhubaneswar coordinates (`20.3242° N, 85.8152° E`) under the **Odisha Bhulekh Cadastre**.
    - **Delhi (Sangam Vihar, Shahdara, South Delhi, Rohini)**: Resolves to Delhi coordinates (`28.5012° N, 77.2470° E`) under **Delhi DORIS**.
    - **Telangana (Shamshabad, Rangareddy, Mamidipally)**: Resolves to Shamshabad coordinates (`17.2582° N, 78.4358° E`) under **Telangana Dharani**.
    - **Pan-India**: Keyword fuzzy resolution and raw GPS coordinate parsing (`lat/lng` patterns).
  - Dynamically calculates high-precision bounding polygon geometries matching the exact deed extent in square metres, registers the parcel into the live GeoPandas/Shapely cadastre collection, and commands the interactive Leaflet map to smoothly fly (`map.flyTo`) straight to the real ground location with electric cyan highlight boundaries (`#06b6d4`) and Esri high-resolution satellite imagery.

### 2.2 Engine 2: GIS Spatial & Topology Validation
- **Role**: Audits cadastral parcel geometry against adjacent plots and historical boundary records.
- **Implementation**:
  - Runs in-memory using **GeoPandas**, **Shapely**, and **STRtree** spatial indexing.
  - **Zero SpatiaLite / SQLite C-extension dependencies**, ensuring effortless cross-platform portability on Windows, Linux, and macOS.
  - Upstream production path: PostGIS.
- **Anomalies Detected**:
  - Boundary overlaps with neighboring surveyed plots (critical risk if overlap > 10%).
  - Sliver gaps between contiguous cadastral boundaries.
  - Area deviation: Discrepancy between the textual deed claim and actual GIS polygon area (`abs(actual - claimed) / claimed * 100`).

### 2.3 Engine 3: Ownership Intelligence
- **Role**: Analyzes historical land transfer graphs to uncover illicit resale patterns.
- **Detectors**:
  - **Rapid Resale**: Flags parcels transacted $\ge 3$ times within a 30-day window.
  - **Abnormal Price Escalation**: Flags transaction steps where sale price surges $> 1.5\times$ or $> 2.0\times$ without land-use reclassification.
  - **Circular Ownership**: Detects cyclic transfer chains ($A \rightarrow B \rightarrow A$) characteristic of benami title laundering.
  - **Cross-Holding Benami Links**: Flags when the same buyer or seller appears across multiple disconnected parcels within 365 days.

### 2.4 Engine 4: Satellite Land-Use Cross-Verification
- **Role**: Cross-verifies the registered land-use classification (e.g., Agricultural) against physical ground reality using Sentinel-2 L2A multispectral satellite imagery.
- **Methodology**:
  - Calculates Normalized Difference Vegetation Index (**NDVI**) and built-up surface reflectance.
  - Detects illegal commercial development or unauthorized construction on agricultural or waterbody land.
  - Always transparently identifies data origin: `Sentinel-2 L2A tile` or `REGISTRY-INFERRED` when satellite tiles are pending.

### 2.5 Engine 5: Unified Fraud Risk Ensemble & Explainability
- **Role**: Computes an authoritative, deterministic composite risk score (0.0 to 100.0).
- **Weight Matrix**:
  $$\text{Ensemble Score} = (0.35 \times \text{GIS}) + (0.25 \times \text{Ownership}) + (0.25 \times \text{Satellite}) + (0.15 \times \text{OCR})$$
  *(Note: If any individual engine discovers a critical anomaly $\ge 80.0$, the composite score elevates proportionally).*
- **Decision Thresholds**:
  - **Green (Low Risk)**: $< 30.0$ — Clean for automated mutation processing.
  - **Yellow (Medium Risk)**: $30.0 - 64.9$ — Requires Tahsildar / Revenue Inspector manual verification.
  - **Red (High Risk / Fraud Flagged)**: $\ge 65.0$ — Freezes mutation; automated referral to Revenue Court / District Collector.
- **Explainability**:
  - Emits structured, human-readable SHAP-style attribution factors (e.g., `[+35% Spatial Weight] Parcel boundary overlaps by 28.4% with adjacent registered parcel`).

---

## 3. User Personas & Permissions

| Role | Access Level | Data Minimization (DPDP Act 2023) | Primary Workflow |
|---|---|---|---|
| **Citizen / Buyer** | Read-only | **Masked PII**: Pattadar names masked (e.g., `Mohan X.`); transaction values generalized | Search survey/ULPIN, check Land Health Card, inspect risk score before purchasing land |
| **Revenue Officer / Tahsildar** | Review & Action | **Unmasked**: Full owner names, deed scans, court status, audit logs | Review flagged documents, input field survey corrections, approve/override with mandatory justification |
| **District Collector** | Administrative Analytics | **Aggregated**: Mandal-level risk indices, fraud hotspots, officer throughput | Monitor village fraud heatmaps, mutation delays, revenue litigation trends |

---

## 4. Legal & Regulatory Compliance Framework

### 4.1 DPDP Act 2023 (Digital Personal Data Protection Act)
- Enforces role-based **data minimization** and consent logging.
- Citizen view strictly redacts identifiable personal information from Dharani passbooks and sale deeds.

### 4.2 IT Act 2000 — Section 65B Electronic Admissibility
- AI recommendations never automatically approve or reject a record.
- Every officer decision generates a timestamped, signed electronic record containing:
  - Extracted field payload & officer corrections diff.
  - SHA-256 cryptographic audit hash.
  - Downloadable Section 65B Certificate PDF with embedded verification QR code for judicial court admissibility.

### 4.3 Registration Act, 1908
- BhuNetra acts purely as an advisory integrity layer. The platform does not legally execute or substitute the registration of deeds under the Registration Act.

---

## 5. End-to-End Document Lifecycle

```
[Upload Deed Scan] ──► [Instant OCR & Dynamic GIS Plotting] ──► [Field Review & Corrections] ──► [Officer Approval] ──► [Sec 65B Certificate]
        │                             │                                     │                           │                       │
 POST /documents/upload     POST /documents/{id}/extract          POST /documents/{id}/review   POST /documents/{id}/approve    PDF + QR Code
 (Stores Raw File)         (Dynamic Polygon to GIS)              (Logs Field Corrections)       (Generates SHA-256 Hash)       (Court Ready)
```

---

## 6. Technical Stack & Repository Layout

### 6.1 Technology Stack
- **Backend**: Python 3.12, FastAPI, Uvicorn, SQLAlchemy, SQLite, GeoPandas, Shapely, Scikit-learn, ReportLab, QRCode, Pydantic, HTTPX.
- **Frontend**: Vite, React 19, Tailwind CSS, Leaflet, React-Leaflet, Lucide React.
- **Spatial Processing**: In-memory Shapely STRtree (Zero SpatiaLite / C-extensions required).

### 6.2 Key Directories & Code Structure
```
BhuNetra-main/
├── backend/
│   ├── main.py                     # FastAPI entry point & router registration
│   ├── models.py                   # SQLAlchemy database schemas (ParcelRecord, Document, AuditLog)
│   ├── database.py                 # SQLite database session engine
│   ├── ml_models.py                # GISAnomalyEngine (GeoPandas + Isolation Forest)
│   ├── routers/
│   │   ├── gis.py                  # GET /api/gis-check/ (Cadastral GeoJSON + Uploaded Plots)
│   │   ├── ocr.py                  # POST /api/ocr/extract (Direct deed extraction)
│   │   ├── documents.py            # Complete Document lifecycle management (upload/extract/review/approve)
│   │   ├── ownership.py            # GET /api/ownership/{id} (Title chain & resale graph)
│   │   ├── satellite.py            # GET /api/satellite/{id} (Sentinel-2 land-use checks)
│   │   └── risk_ensemble.py        # GET /api/risk-score/{id} (Engine 5 composite calculation)
│   └── services/
│       ├── extraction_service.py   # OCR Engine: VLM Ollama probe + Calibrated Fallback
│       └── uploaded_parcels.py     # Document-to-Cadastre dynamic GIS bridge & plot placement
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Top-level shell, tab routing, role management
│   │   ├── components/
│   │   │   ├── MapViewer.jsx       # Interactive Leaflet map with MapRecenter & Cyan plot styling
│   │   │   ├── OCRScanner.jsx      # Registry OCR interface, field extraction & GIS cross-verify button
│   │   │   ├── DocumentReviewPanel.jsx # Officer field correction editor
│   │   │   ├── LandHealthCard.jsx  # Citizen modal with downloadable Land Health Card
│   │   │   ├── OfficerReviewQueue.jsx  # Queue of flagged parcels requiring officer action
│   │   │   └── SatelliteComparison.jsx # Dual-pane satellite imagery overlay
├── data/
│   ├── synthetic/
│   │   ├── parcels.geojson         # Base cadastral geometry (Shamshabad Mandal, Rangareddy)
│   │   ├── ownership_history.csv   # Historical land transaction records
│   │   └── extraction_ground_truth.json # Synthetically verified benchmark deeds
```

---

## 7. New Developer Quickstart & Setup Guide

### 7.1 Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ and npm
- Git

### 7.2 Running Backend Locally
```bash
# 1. Navigate to repository root
cd BhuNetra-main

# 2. Activate Python virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies (if setting up fresh)
pip install fastapi uvicorn geopandas shapely scikit-learn reportlab qrcode pydantic httpx sqlalchemy

# 4. Launch FastAPI server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Swagger documentation will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

### 7.3 Running Frontend Locally
```bash
# In a separate terminal:
cd BhuNetra-main/frontend

# Install dependencies (if fresh)
npm install

# Start Vite dev server
npm run dev
```
*Frontend UI will be live at: [http://localhost:3000](http://localhost:3000)*

---

## 8. Common Developer Gotchas & Conventions
1. **Never use `cd` inside commands**: Execute all scripts relative to the workspace root.
2. **Zero SQLite C-Extensions**: All GIS queries must run through Shapely and GeoPandas in Python memory. Do not attempt to load `mod_spatialite` or SQLite C extensions.
3. **Dual Router Registration**: In `backend/main.py`, routers are registered twice (with and without `/api` prefix) so both direct backend requests and frontend Vite proxy requests (`/api/*`) resolve cleanly.
4. **Dynamic Plot Updates**: Whenever new document attributes are parsed, always register them through `uploaded_parcels.register_uploaded_parcel(...)` to ensure the GIS map immediately includes the plot in `/api/gis-check/`.
