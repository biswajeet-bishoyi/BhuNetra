# BhoomiNetra AI
Intelligent Land Record Digitization and Validation System

Smart India Hackathon 2026
Problem Statement ID: SIH26018
Problem Statement Title: Intelligent Land Record Digitization and Validation System
Theme: Smart Automation
Category: Software
Team Name: RADIANCE
Team ID: 138388
Ministry: Ministry of Rural Development, Government of India

---

## Video Demonstration

Watch the complete 5-minute technical walkthrough and system demo:
YouTube Link: https://youtu.be/EzqT4MyqQ8M

---

## Executive Summary

Under the Digital India Land Records Modernization Programme (DILRMP), over 95% of India's land records have been digitized. However, more than two-thirds of all pending civil litigation in Indian courts still originates from land and property disputes. Digitization without multi-source verification merely migrates historical errors, boundary collisions, and fraudulent titles into modern databases.

Addressing Ministry of Rural Development Problem Statement SIH26018, Team RADIANCE developed BhoomiNetra AI — an intelligent verification and decision-support layer built directly on top of DILRMP. BhoomiNetra AI does not replace existing state land registries; it evaluates whether those records can genuinely be trusted, detects spatial and title conflicts, and provides explainable, court-admissible evidence.

---

## Core Multi-Engine Architecture

1. Engine 1: Multilingual Registry OCR
   Extracts Pattadar names, Khasra/Survey numbers, Khata IDs, and boundary extents in under one second with over 96% accuracy across regional Indian scripts (Dharani, UP Bhulekh, Odisha Bhulekh).

2. Engine 2: Spatial GIS Topology & Conflict Engine
   Powered by in-memory GeoPandas and Shapely spatial indexing. It cross-references digitized deed polygons against NIC BhuNaksha cadastral vectors to detect physical boundary overlaps (such as Parcel P-105 encroaching 12.4% into P-106). Features TreeSHAP explainability (+35% spatial weight) to eliminate black-box predictions.

3. Engine 3: Temporal Ownership Graph
   Tracks property transaction velocity over time to expose money laundering, rapid resale syndicates, and benami holdings (such as Parcel P-108 resold 4 times in 24 days with an artificial valuation surge from 50 to 99 Lakhs).

4. Engine 4: Satellite Land-Use Cross-Verification
   Integrates ESA Copernicus Sentinel-2 multispectral satellite data to compute NDVI vegetation indices and built-up surfaces. Automatically flags mismatches where an agricultural parcel in the Record of Rights has an unauthorized commercial warehouse (such as Parcel P-135 with 78.5% concrete cover). Operates with offline deterministic tiles for remote field inspections.

5. Engine 5: Calibrated Fraud Risk Ensemble & Review Queue
   Synthesizes spatial (35%), ownership (25%), satellite (25%), and OCR (15%) signals into an overall risk score. Strictly enforces Human-in-the-Loop governance: the AI never cancels or modifies a deed autonomously; every administrative action requires a typed, accountable justification from the revenue officer.

6. Triple Evidence Workspace
   Triangulates the physical registered sale deed, the state digital RoR, and cadastral GPS survey coordinates. Binds evidence snapshots with an immutable SHA-256 cryptographic hash, generating court-admissible electronic dossiers.

---

## Citizen Features & Accessibility

- DPDP Act 2023 Compliance: Dynamic PII masking (names shown as Kalyan X., phone numbers redacted) and mandatory upfront citizen consent before querying spatial data.
- Buyer Pre-Verification: Instant QR code scanner allowing prospective buyers to check encumbrances, litigation flags, and non-agricultural conversion before paying a deposit.
- Multilingual WhatsApp AI Assistant: Rural conversational interface allowing farmers to check mutation status and survey boundaries in regional languages (Telugu, Hindi, Odia, English).
- District Collector Analytics: Macro-level Mandal Vulnerability Index ranking sub-districts, identifying dispute hotspots, and tracking Tahsildar statutory disposal SLAs.

---

## Statutory & Legal Compliance

- Digital Personal Data Protection (DPDP) Act, 2023: Enforces strict data minimization, privacy rights, and citizen consent.
- Information Technology Act, 2000 (Section 65B): Issues SHA-256 hashed electronic evidence packages meeting the statutory standards for admissibility in Indian courts.
- The Registration Act, 1908: Anchors legal title to registered deeds rather than replacing state deeds with unregulated ledgers.

---

## Benchmark Performance

Tested and validated across 42 ground-truth cadastral parcels:
- Precision: 0.875 (87.5%)
- Recall: 0.778 (77.8%)
- F1-Score: 0.824 (82.4%)
- OCR Processing Speed: < 1.0 second per deed

---

## Technology Stack

- Frontend: React, Vite, Vanilla CSS, Leaflet.js
- Backend: Python, FastAPI, GeoPandas, Shapely, PyMuPDF, OpenCV
- Machine Learning & Explainability: Scikit-learn (Isolation Forest), XGBoost, TreeSHAP
- Earth Observation: Sentinel-2 Multispectral Imagery, GDAL, Rasterio
- Agentic & Conversational AI: Agno Agent Framework, Google Gemini API
- Security: SHA-256 Cryptographic Hashing, Section 65B IT Act PDF Generator

---

## Installation & Setup

1. Clone the repository:
   git clone https://github.com/your-username/BhoomiNetra-AI.git
   cd BhoomiNetra-AI

2. Backend Setup:
   cd backend
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py

3. Frontend Setup:
   cd ../frontend
   npm install
   npm run dev

---

Team RADIANCE (Team ID: 138388)
Smart India Hackathon 2026
Ministry of Rural Development (SIH26018)
