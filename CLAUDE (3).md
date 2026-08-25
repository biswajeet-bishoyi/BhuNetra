# CLAUDE.md — BhuNetra AI (SIH 2026, SIH26018)

This file guides any AI coding assistant (Claude Code or otherwise) working on this
repository. Read this before writing code. It encodes decisions already made so you
don't re-litigate them, and it encodes the hackathon-reality constraints that the
original brainstorm skipped.

## 0. What this project actually is

**BhuNetra AI** — an AI-powered verification and decision-support layer that sits
*on top of* DILRMP-digitized land records, not a replacement for DILRMP itself.
Problem statement: SIH26018, Ministry of Rural Development — "Intelligent Land
Record Digitization and Validation System."

Core pitch: DILRMP digitizes records; BhuNetra decides whether those records can
be trusted, and shows its reasoning.

## 1. Hard constraint: this is a hackathon build, not a production system

Before writing any code, know the build window is realistically 36–48 hours after
the idea round, with a 5–6 person team. The original 5-engine, Hyperledger Fabric,
500-page-SRS plan is NOT buildable at that scope. Every engine below is tagged:

- **REAL** — build with an actual trained/working model, runs live in the demo
- **RULE-STUB** — rules-based approximation, labeled honestly as "production would
  use ML here" if a judge asks
- **MOCK** — canned/pre-computed output triggered by demo data, UI only

Do not silently upgrade a MOCK to claim it's REAL in the pitch deck. Judges probe.
Honesty about what's stubbed reads as engineering maturity, not weakness.

### Engine scope for this build

| Engine | Scope for hackathon | Tag |
|---|---|---|
| 1. Registry OCR | PaddleOCR + basic layout parsing on a small curated set of sample registry scans (own state's script) | REAL (narrow dataset) |
| 2. GIS Validation | Shapely/GeoPandas topology checks (overlap, gap, area deviation) on synthetic parcel geometries with injected anomalies | REAL |
| 3. Ownership Intelligence | Transfer-frequency and timeline anomaly rules (e.g. >N transfers in <X days) over a small synthetic ownership graph | RULE-STUB, present as "graph AI" only if a simple NetworkX pattern-match is actually wired in |
| 4. Satellite Verification | Pre-downloaded Sentinel-2 tiles for 2–3 demo villages, simple land-cover classification (not live GEE calls in the demo) | RULE-STUB / MOCK |
| 5. Fraud Risk (ensemble) | Weighted combination of Engines 1–4's outputs into a single Green/Yellow/Red score, with feature attribution shown per flag | REAL |
| Blockchain layer | A single smart contract (Solidity, local Hardhat/Ganache chain) that hashes approved records — not a multi-node Hyperledger deployment | REAL but minimal |
| Revenue Court dashboard | Static status field (Clean/Stay Order/Mutation Pending/Court Case) per parcel, officer-editable | REAL, simple CRUD |

If team size or time drops, cut Engine 4 (satellite) to pure MOCK first — it's the
most infrastructure-heavy and least demo-time-critical piece. Never cut Engine 5
(the risk dashboard) — it's the visual centerpiece of the pitch.

## 2. Data strategy (this was missing from the original plan — do this first)

No real Bhulekh/ULPIN/Aadhaar API access will be available. Do not build against
live government endpoints; they don't exist for you.

- **Synthetic parcel dataset**: generate GeoJSON parcels with GeoPandas/Shapely,
  deliberately inject overlaps, gaps, and area-mismatch anomalies into ~10-15% of
  records so the anomaly detector has something real to find.
- **OCR sample set**: 15–20 photographed/printed sample registry pages (can be
  self-created from public RoR format templates) — don't claim a large corpus.
- **Ownership history**: synthetic CSV of parcel_id → owner → date, with a handful
  of suspicious rapid-resale chains injected for the demo to catch.
- **Satellite tiles**: pre-download (not live-fetch) 2–3 Sentinel-2 scenes for
  named demo villages before the presentation. Live API calls during a stage demo
  are a common failure point — avoid them.
- **Validation**: hand-label the injected anomalies as ground truth and report
  precision/recall against them, the same way the ML reference paper does (its
  Isolation Forest baseline is precision 0.83 / recall 0.79 / F1 0.81 — use this
  as your target to beat or contextualize, not to blindly claim you matched).

## 3. Architecture

```
React (Vite) frontend
   │
   ├── Map/parcel viewer (Leaflet or Mapbox GL, PostGIS-backed)
   ├── OCR upload flow
   ├── Risk dashboard (Green/Yellow/Red + explanation panel)
   └── Officer review queue (approve/override/audit log)
   │
FastAPI backend
   ├── /ocr        → Engine 1
   ├── /gis-check   → Engine 2 (PostGIS + Shapely)
   ├── /ownership   → Engine 3
   ├── /satellite   → Engine 4 (serves precomputed results)
   ├── /risk-score  → Engine 5 (ensemble, SHAP-based explanation)
   └── /blockchain  → hash + officer-approval write to local chain
   │
PostgreSQL + PostGIS (parcels, ownership history, court status)
Local Ethereum-compatible chain (Hardhat/Ganache) + Solidity contract for hashing
```

**Why PostGIS + a thin blockchain layer, not "we use blockchain" for everything**:
say this explicitly in any technical Q&A — "We use a permissioned chain only for
immutable approval hashes; spatial data stays in PostGIS because GIS queries need
spatial indexing blockchain doesn't provide." This is the answer that distinguishes
you from teams who reach for blockchain as a buzzword.

## 4. Tech stack

- Frontend: React + Vite, Tailwind, Leaflet (or Mapbox GL if a token is available)
- Backend: FastAPI (Python) — not Node, because Engines 1/2/5 need Python ML
  libraries (scikit-learn, GeoPandas, Shapely, PaddleOCR, SHAP) in-process
- DB: PostgreSQL + PostGIS extension
- ML: scikit-learn (Isolation Forest — matches the reference paper's best-performing
  model), SHAP for explanation, GeoPandas/Shapely for topology
- OCR: PaddleOCR (open source, no API cost)
- Blockchain: Solidity + Hardhat local network, ethers.js on frontend
- Auth: simple JWT, roles = citizen / officer / admin

## 5. Explainability requirement (non-negotiable)

Every Red/Yellow flag from Engine 5 must render a short human-readable reason
(e.g., top 2–3 contributing features from SHAP or from the rule that fired). A risk
score with no reasoning is not decision support — do not ship a flag without an
explanation string attached.

## 6. Human-in-the-loop requirement (non-negotiable)

No engine auto-rejects a record. All flags route to an officer review queue. Every
officer decision (approve/reject/override) is logged with a reason and timestamp —
this is both the ethical design and the answer to "what if the AI is wrong."

## 7. Repo conventions

- `backend/` — FastAPI app, one router file per engine
- `frontend/` — React app
- `data/synthetic/` — generator scripts + output GeoJSON/CSV, checked in
- `models/` — trained model artifacts (small enough to check in; note in README if not)
- `contracts/` — Solidity contract + Hardhat config
- Commit messages: reference which engine/module they touch
- Keep the README's "what's real vs stubbed" table in sync with section 1 above —
  this is what you show if a judge asks to see the code

## 8. Demo script (what the 5-minute run-through hits)

1. Citizen uploads a scanned registry → Engine 1 extracts fields live
2. Map opens, parcel renders → Engine 2 flags a boundary overlap in red
3. Explanation panel shows *why* (feature attribution)
4. Ownership timeline shows a suspicious rapid-resale pattern → Engine 3 flags it
5. Satellite comparison shows registry-says-agriculture vs imagery-says-building
6. Officer reviews the aggregated risk score, approves with a logged reason
7. Blockchain hash generated, ownership record updates, audit trail visible

Keep every step running against pre-loaded demo data — don't depend on live network
calls during the actual presentation.
