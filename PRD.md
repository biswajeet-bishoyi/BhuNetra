# PRD — BhuNetra AI
### AI-Powered Land Record Verification and Decision Support Platform
SIH 2026 · Problem Statement SIH26018 · Ministry of Rural Development

---

## 1. Positioning & Value Proposition
BhuNetra AI is an AI-powered verification and decision-support layer that sits *on top of* DILRMP digitized land records. DILRMP digitizes records; BhuNetra evaluates whether those records can be trusted, surfaces anomalies across spatial, title, and satellite data, and presents explainable reasoning to revenue officers.

---

## 2. Architectural Principle
> **"Spatial data and processing live in Python via GeoPandas/Shapely, with PostGIS documented as the production-scale upgrade path; the chain stays scoped to hash-only for the same separation-of-concerns reason."**

- **Relational & Spatial Core**: SQLite stores cadastral records and plain WKT/GeoJSON geometries without external C/SpatiaLite extension requirements. All spatial indexing (`STRtree`), polygon intersections, boundary gap calculations, and area variances run in Python memory via GeoPandas and Shapely.
- **Blockchain Scope**: Blockchain is used solely for immutable SHA-256 approval hashing to establish an auditable chain of custody.

---

## 3. Core Engine Architecture

1. **Engine 1: Registry OCR Engine** (`REAL / FALLBACK`)
   - Scans bilingual (Telugu/English) registered sale deeds (Telangana Dharani style) and extracts survey number, khatian, pattadar name, and claimed extent.
2. **Engine 2: GIS Validation Engine** (`REAL`)
   - Evaluates cadastral parcel geometries in memory using Shapely STRtree indexing and a scikit-learn Isolation Forest model to detect boundary overlaps, sliver gaps, and area calculation deviations.
3. **Engine 3: Ownership Intelligence Engine** (`RULE-STUB`)
   - Detects rapid resale anomalies (>3 transfers in <30 days) and price escalation across transaction graphs.
4. **Engine 4: Satellite Cross-Verification Engine** (`RULE-STUB / MOCK`)
   - Cross-checks registered land-use claims (e.g. Agricultural) against pre-computed Sentinel-2 NDVI and built-up reflectance scenes.
5. **Engine 5: Fraud Risk Ensemble & Explainability** (`REAL`)
   - Deterministic weighted combination: **GIS (35%) + Ownership Intelligence (25%) + Satellite Verification (25%) + Registry OCR (15%)**.
   - Outputs Green ($<30$), Yellow ($30-64.9$), and Red ($\ge 65$) risk bands with SHAP-style feature attribution factors.
6. **Officer Review Queue & Audit Log** (`REAL`)
   - Mandatory human-in-the-loop workflow. AI never auto-rejects; every administrative override requires a typed justification and generates a timestamped digital audit record.
7. **Revenue Court Status Field** (`REAL`)
   - Tracks parcel litigation states: `Clean`, `Stay Order`, `Mutation Pending`, `Court Case`.
8. **Blockchain Approval Hash Layer** (`REAL / FALLBACK`)
   - Generates SHA-256 cryptographic approval hashes for digital audit verification.

---

## 4. Legal & Compliance Framework

- **DPDP Act 2023 (Digital Personal Data Protection Act)**:
  - Role-based data minimization: Citizen mode automatically masks Pattadar personal identifying information (PII). Officer mode enforces authenticated access with logged purpose.
- **IT Act 2000 — Section 65B**:
  - Audit trail timestamps, model version hashes, and officer decision records satisfy legal criteria for electronic record court admissibility.
- **Registration Act, 1908 Boundary**:
  - Cryptographic approval hashes verify workflow integrity; they **do not legally replace or supersede the physical registered sale deed**.

---

## 5. Demo Context & Personas
- **State & District**: **Telangana (Rangareddy District, Shamshabad Mandal)**.
- **Villages**: **Shamshabad**, **Mamidipally**, **Kothwalguda**.
- **User Roles**: Simplified Role Switcher in UI (`Citizen`, `Revenue Officer`, `Admin`).
