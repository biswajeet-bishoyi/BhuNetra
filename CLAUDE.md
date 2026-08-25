# CLAUDE.md — BhuNetra AI (SIH 2026, SIH26018)

This file guides any AI coding assistant working on this repository. Read this before writing code.

## 0. What this project actually is

**BhuNetra AI** — an AI-powered verification and decision-support layer that sits
*on top of* DILRMP-digitized land records, not a replacement for DILRMP itself.
Problem statement: SIH26018, Ministry of Rural Development — "Intelligent Land
Record Digitization and Validation System."

Core pitch: DILRMP digitizes records; BhuNetra decides whether those records can
be trusted, and shows its reasoning.

---

## 1. Architectural Foundation & Separation of Concerns

> **"Spatial data and processing live in Python via GeoPandas/Shapely, with PostGIS documented as the production-scale upgrade path; the chain stays scoped to hash-only for the same separation-of-concerns reason."**

- **Spatial Layer**: SQLite serves as a plain relational store with WKT/GeoJSON text columns. No `mod_spatialite` or SpatiaLite C-extensions are loaded into SQLite. All spatial indexing (`STRtree`), polygon overlap math, and topology checks run in Python memory via GeoPandas and Shapely.
- **Blockchain Layer**: Scoped strictly to immutable SHA-256 approval hashing for audit trails. Raw spatial polygons are never stored on-chain.

---

## 2. Legal & Regulatory Compliance Framework

- **DPDP Act 2023 (Data Protection & Privacy)**:
  - Citizen / public view enforces data minimization: PII (Pattadar full names, Aadhaar, contact details) is masked.
  - Officer mode requires authenticated role access with logged purpose.
- **IT Act 2000 — Section 65B (Electronic Evidence Admissibility)**:
  - Every officer decision generates a timestamped SHA-256 cryptographic hash and audit trail designed to satisfy Sec 65B admissibility criteria.
- **Registration Act 1908 (Title Boundary)**:
  - Cryptographic approval hashes verify digital workflow integrity and auditability; they **do not legally replace or supersede the physical registered sale deed**.

---

## 3. Engine Scope & Transparent Implementation Tiers

Every engine is explicitly tagged:
- **REAL** — built with an actual working model/logic, runs live in the demo
- **RULE-STUB** — rules-based approximation, labeled honestly in copy/code
- **FALLBACK** — triggered if optional heavy packages (e.g. PaddleOCR, Web3 EVM node) are offline; always labeled as fallback rather than falsely claiming REAL
- **MOCK** — canned/pre-computed output triggered by demo data, UI only

| Engine / Module | Implementation Scope | Tag |
|---|---|---|
| **1. Registry OCR** | Layout parser & regex/bilingual extraction on Telangana Dharani scans | `REAL (Narrow Dataset)` / `FALLBACK (Regex Parser)` |
| **2. GIS Validation** | In-memory Shapely/GeoPandas STRtree topology checks + scikit-learn Isolation Forest | `REAL` |
| **3. Ownership Intelligence** | Transfer-frequency rules (>3 transfers in <30 days) over ownership timeline | `RULE-STUB` |
| **4. Satellite Verification** | Pre-downloaded Sentinel-2 village scenes & NDVI/built-up reflectance comparison | `RULE-STUB / MOCK` |
| **5. Fraud Risk Ensemble** | Deterministic 35/25/25/15 weighted combination with SHAP feature attribution strings | `REAL` |
| **Officer Review Queue** | Human-in-the-loop queue with mandatory override reasons & Sec 65B audit log | `REAL` |
| **Revenue Court Dashboard** | Parcel litigation status tracking (Clean / Stay Order / Mutation Pending / Court Case) | `REAL` |
| **Blockchain Approval Hash**| SHA-256 cryptographic approval hashing + Solidity smart contract for audit trail | `REAL` / `FALLBACK (SHA-256)` |

---

## 4. Engine 5 Combination Rule & Weight Matrix

The ensemble risk score $S_{\text{composite}} \in [0, 100]$ is computed deterministically:

$$S_{\text{composite}} = 0.35 \times S_{\text{GIS}} + 0.25 \times S_{\text{Ownership}} + 0.25 \times S_{\text{Satellite}} + 0.15 \times S_{\text{OCR}}$$

- **Green (Low Risk)**: $< 30.0$ $\rightarrow$ Clean record, recommended for direct clearance.
- **Yellow (Moderate Risk)**: $30.0 - 64.9$ $\rightarrow$ Advisory flag, routed to officer queue.
- **Red (High Risk)**: $\ge 65.0$ $\rightarrow$ Severe anomaly detected; mutation hold recommended.
- **Explainability**: Every score generates a structured SHAP-style breakdown list (e.g., `[+35% Spatial Weight] 12.4% boundary overlap with P-106`).

---

## 5. Demo Narrative & Data Strategy

- **State & District**: **Telangana (Rangareddy District, Shamshabad Mandal)**.
- **Canonical Demo Villages**:
  1. **Shamshabad**: Urban fringe, high velocity (P-105/P-106 overlap, P-108 rapid resale).
  2. **Mamidipally**: Peri-urban growth (P-135 agricultural vs. concrete warehouse).
  3. **Kothwalguda**: Clean agricultural baseline parcels (P-101, P-102).
- **Zero Live Government APIs**: Pre-generated offline data files in `data/synthetic/` and `data/satellite/`.
- **Simplified Role-Based Access**: Role Switcher (`Citizen` / `Revenue Officer` / `Admin`) in top navigation.

---

## 6. Build Order & Milestones

1. **Engine 2 (GIS)**: In-memory Shapely/GeoPandas topology checks + Isolation Forest + Leaflet map.
2. **Engine 1 (OCR)**: Scanned deed intake + bilingual Dharani layout extraction.
3. **Engine 5 (Ensemble)**: Fixed 35/25/25/15 weighted score + SHAP factor breakdown.
4. **Officer Review Queue**: Human-in-the-loop override console + mandatory justification + audit trail.
5. **Engines 3 & 4**: Rapid resale timeline detector + offline Sentinel-2 satellite scene cross-check.
6. **Blockchain & Court Status**: SHA-256 approval hash generator + Revenue Court litigation flags.
