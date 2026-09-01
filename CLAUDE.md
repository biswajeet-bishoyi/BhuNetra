# CLAUDE.md — BhuNetra AI (SIH 2026, SIH26018)

This file guides any AI coding assistant working on this repository. Read this before writing code.

## 0. What this project actually is

**BhuNetra AI** — an AI-powered verification and decision-support layer that sits
*on top of* DILRMP-digitized land records, not a replacement for DILRMP itself.
Problem statement: SIH26018, Ministry of Rural Development — "Intelligent Land
Record Digitization and Validation System."

Core pitch: DILRMP digitizes records; BhuNetra decides whether those records can
be trusted, and shows its reasoning.

### Feature surface (post-Phase 1-4)

| Feature | Where | Notes |
|---|---|---|
| **5 Engines** (OCR / GIS / Ownership / Satellite / Ensemble) | `backend/routers/` | 35/25/25/15 weighted ensemble |
| **Document Lifecycle** | `backend/routers/documents.py` | UPLOADED → EXTRACTED → NEEDS_REVIEW → VERIFIED → APPROVED/REJECTED |
| **Officer Review Queue** | `backend/routers/review_queue.py` | Human-in-the-loop + Sec 65B audit log |
| **Revenue Court** | `backend/routers/revenue_court.py` | Litigation / mutation / stay tracking |
| **Block-chain Audit** | `backend/routers/blockchain.py` | SHA-256 approval hash + visualizer |
| **Land Health Card + PDF** | `backend/routers/certificate.py` | reportlab + qrcode + dual-role PDF |
| **Executive Analytics** | `backend/routers/analytics.py` | Mandal stats / 12mo trend / search |
| **Mutation Workspace** | `backend/routers/mutations.py` | Officer draws polygon → review queue |
| **Multi-channel Alerts** | `backend/routers/alerts.py` | WhatsApp Cloud API + SMS gateway |
| **Batch Document Processing** | `POST /api/documents/batch` | Up to 20 files / request |
| **Temporal Risk Animation** | `/api/analytics/anomaly-trends` | 12-month scrubber |
| **DPDP Consent Dialog** | `frontend/src/components/ConsentDialog.jsx` | localStorage gate, citizen data minimization |
| **English / Telugu i18n** | `frontend/src/i18n.js` | LangProvider context, localStorage persistence |
| **Demo Walkthrough** | `frontend/src/components/DemoWalkthrough.jsx` | 10-step auto-tour with TTS |
| **Parcel Search** | `Header.jsx` | 300ms debounce, DPDP-masked dropdown |

---

## 1. Architectural Foundation & Separation of Concerns

> **"Spatial data and processing live in Python via GeoPandas/Shapely, with PostGIS documented as the production-scale upgrade path; the chain stays scoped to hash-only for the same separation-of-concerns reason."**

- **Spatial Layer**: SQLite serves as a plain relational store with WKT/GeoJSON text columns. No `mod_spatialite` or SpatiaLite C-extensions are loaded into SQLite. All spatial indexing (`STRtree`), polygon overlap math, and topology checks run in Python memory via GeoPandas and Shapely.
- **Blockchain Layer**: Scoped strictly to immutable SHA-256 approval hashing for audit trails. Raw spatial polygons are never stored on-chain.
- **Polygon Drawing**: Officer mutation requests store GeoJSON Polygon text in `mutation_requests` (no spatialite needed). Drawing in the UI uses click-to-add-points on react-leaflet — no `leaflet-draw` dependency required.
- **Document Storage**: Lifecycle metadata is text in `documents`; raw scan bytes are stored on disk under `data/uploads/` with SHA-256 deduplication.

---

## 1. Architectural Foundation & Separation of Concerns

> **"Spatial data and processing live in Python via GeoPandas/Shapely, with PostGIS documented as the production-scale upgrade path; the chain stays scoped to hash-only for the same separation-of-concerns reason."**

- **Spatial Layer**: SQLite serves as a plain relational store with WKT/GeoJSON text columns. No `mod_spatialite` or SpatiaLite C-extensions are loaded into SQLite. All spatial indexing (`STRtree`), polygon overlap math, and topology checks run in Python memory via GeoPandas and Shapely.
- **Blockchain Layer**: Scoped strictly to immutable SHA-256 approval hashing for audit trails. Raw spatial polygons are never stored on-chain.

---

## 2. Legal & Regulatory Compliance Framework

- **DPDP Act 2023 (Data Protection & Privacy)**:
  - Citizen / public view enforces data minimization: PII (Pattadar full names, Aadhaar, contact details) is masked via `utils/dpdp.py`.
  - Officer mode requires authenticated role access with logged purpose.
  - **Consent Gate**: `ConsentDialog` blocks the app on first load until the citizen accepts / declines. Choice persisted in `localStorage` as `bhunetra_dpdp_consent` = `accepted` or `declined`.
- **IT Act 2000 — Section 65B (Electronic Evidence Admissibility)**:
  - Every officer decision generates a timestamped SHA-256 cryptographic hash and audit trail designed to satisfy Sec 65B admissibility criteria.
  - Document approval also generates a SHA-256 hash of `BHUNETRA:{id}:{filename}:{file_hash}:{parcel_id}:{confidence}:{timestamp}`.
  - Officer queue actions require a typed reason of at least 5 characters (audit trail validation in `review_queue.py` and `documents.py`).
- **Registration Act 1908 (Title Boundary)**:
  - Cryptographic approval hashes verify digital workflow integrity and auditability; they **do not legally replace or supersede the physical registered sale deed**.
  - Pending mutation geometry never overrides existing records until the Tahsildar approves.

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

## 7. Frontend Patterns

- **Tab Registry**: Tabs are defined in `Header.jsx` `allTabs`. Each entry has `{id, label, icon, roles}`. The `visibleTabs` filter restricts by selected role. Adding a new tab requires updating Header, App, and `i18n.js` (EN + TE).
- **Multilingual**: All user-facing strings go through the `t()` helper from `useLang()`. New strings must be added to `DICTIONARY.en` AND `DICTIONARY.te`.
- **PII Masking**: Any component that displays `owner_name` or owner-specific contact data must call `mask_pii_fields(...)` or check `selectedRole === 'Citizen'` and show a masked form. The full mask helper lives at `utils/dpdp.py`.
- **PDF Generation**: Frontend uses `fetch(...).then(r => r.blob())` against `/api/certificate/{parcel_id}/export-pdf`. The backend uses `reportlab` for A4 layout and `qrcode` for the SHA-256 QR.
- **Live Engine Status**: The header "Engine Status" pill opens `StatusModal` which calls `/api/ocr/engine-status`. A failed / off engine does not block the rest of the UI.
- **Search Bar**: `Header.jsx` debounces 300ms and queries `/api/analytics/search`. Owner name is hidden for Citizen role.

## 8. Backend Patterns

- **Router registration**: Every new router must be added to `main.py` TWICE — once with `prefix="/api"` and once without — for backward compatibility.
- **In-memory cache**: `_ensemble_cache` in `analytics.py` is a module-level dict that memoizes `compute_fraud_risk_ensemble` per parcel. Reset only on process restart.
- **File uploads**: 12 MB per file ceiling, SHA-256 deduplication, file persisted at `data/uploads/{file_hash}_{filename}`.
- **Audit trail validation**: All override / review / approval endpoints require a typed `reason` of at least 5 characters and write to the `audit_logs` table.
- **Mutations**: New mutation geometry is stored as raw GeoJSON text in `mutation_requests.geometry_geojson`. Status: PENDING → APPROVED / REJECTED. The original parcel record is never modified.
- **WhatsApp / SMS dispatch**: Reads `WHATSAPP_API_TOKEN` + `WHATSAPP_PHONE_ID` from env. Without these, returns `MOCK_DISPATCHED` receipts so the UI demo flow is never blocked.
- **Temporal trend**: `anomaly_trends` deterministically perturbs the static ensemble score with `((hash(pid) + m*13) % 100)/100 * 20 - 10` noise per month to produce a stable 12-month series.

## 9. Environment Variables

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5vl:3b
EXTRACTION_MAX_EDGE=1280
EXTRACTION_TIMEOUT=300
EXTRACTION_CONFIDENCE_THRESHOLD=0.75
CLIENT_ORIGIN=http://localhost:3000
JWT_SECRET=<change-me>
WHATSAPP_PHONE_ID=<from Meta Business>
WHATSAPP_API_TOKEN=<from Meta Business>
```
