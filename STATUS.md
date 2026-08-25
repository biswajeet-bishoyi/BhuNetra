# BhuNetra AI — Module Implementation Status

This document explicitly tags every module in BhuNetra AI with its implementation tier for complete SIH 2026 hackathon transparency:
- **REAL**: Actual working model/logic running live in the demo path
- **RULE-STUB**: Rules-based approximation standing in for ML, honestly labeled
- **FALLBACK**: Triggered if optional heavy local packages (e.g. PaddleOCR, Web3 EVM node) are offline; always labeled as fallback rather than falsely claiming REAL
- **MOCK**: Canned/pre-computed output triggered by demo data, UI-only

| Module / Engine | Implementation Tier | Description |
|---|---|---|
| **Engine 1: Registry OCR / Digitization** | `REAL (On-device vision-language extraction)` | Reads the actual uploaded image with `qwen2.5vl:3b` running locally via Ollama. Per-field confidence calibrated against deterministic format checks, government master-data reconciliation, and cross-pass agreement; fields below threshold route to officer review. **No filename lookup and no registry fallback** — if the engine is offline the API returns 503 rather than fabricating fields. See [`docs/PHASE2_EXTRACTION.md`](docs/PHASE2_EXTRACTION.md). |
| **Engine 2: GIS Validation** | `REAL` | In-memory Shapely STRtree topology checks (overlap, gap, area deviation) + scikit-learn Isolation Forest (Zero SpatiaLite extension) |
| **Engine 3: Ownership Intelligence** | `RULE-STUB` | Rapid resale frequency rules (>3 transfers in <30 days) and ownership chain graph parsing |
| **Engine 4: Satellite Verification** | `RULE-STUB / MOCK` | Pre-downloaded Sentinel-2 Shamshabad/Mamidipally village scenes & land-use classification cross-checks |
| **Engine 5: Fraud Risk Ensemble** | `REAL` | Deterministic 35/25/25/15 weighted combination of Engines 1–4 into Green/Yellow/Red risk scores with SHAP feature attribution |
| **Officer Review Queue** | `REAL` | Full human-in-the-loop queue with mandatory override/approval reasons and timestamped audit logs |
| **Revenue Court Status Field** | `REAL` | Parcel litigation status tracking (Clean / Stay Order / Mutation Pending / Court Case) |
| **Blockchain Approval Hash** | `REAL` / `FALLBACK (SHA-256)` | SHA-256 cryptographic approval hashing + Solidity smart contract for local chain storage |

### Legal & Separation of Concerns Notes
1. **Spatial Architecture**: Spatial data and processing live in Python via GeoPandas/Shapely, with PostGIS documented as the production-scale upgrade path; the chain stays scoped to hash-only for the same separation-of-concerns reason.
2. **DPDP Act 2023**: Citizen view applies consent-based data minimization & PII masking.
3. **IT Act 2000 Sec 65B & Registration Act 1908**: Cryptographic hashes provide tamper-evident digital audit integrity; statutory title remains with the registered deed.
4. **Data sovereignty**: Document extraction runs entirely on-device. No scanned land record is transmitted to any external or cloud service, and the system requires no network connectivity to operate.

Updated: August 2026
