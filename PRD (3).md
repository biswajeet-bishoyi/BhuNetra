# PRD — BhuNetra AI
### AI-Powered Land Record Verification and Decision Support Platform
SIH 2026 · Problem Statement SIH26018 · Ministry of Rural Development · Theme: Software

---

## 1. Problem Statement

DILRMP has digitized ~95% of Records of Rights and cadastral maps and rolled out
ULPIN nationally, but digitization alone does not establish *trust*. Two-thirds of
civil cases pending before Indian courts are land-related, largely because:

- Boundary overlaps, gaps, and geometry errors persist in digitized cadastral data
- Ownership mismatches and duplicate records survive legacy data migration
- Manual verification of these anomalies is not feasible at national scale
- Forged documents, double-selling, and impersonation still occur because no
  automated cross-check exists between registry claims and ground reality
- Existing blockchain land-registry proposals secure *records as entered* but do
  not verify whether what was entered is *correct* in the first place

**The gap neither DILRMP nor existing academic proposals fully close: an automated
layer that verifies digitized records are trustworthy before they're relied on for
transactions or legal disputes.**

## 2. Why not just build another portal or another blockchain registry

DILRMP already provides RoR digitization, cadastral maps, ULPIN, registration
integration, and Aadhaar linking. Building another land portal duplicates existing
government infrastructure and gives judges no reason to prefer it over DILRMP.
A blockchain-only registry (as in the reference IEEE paper) secures transactions
once digitized but does nothing to catch bad data at entry — its own conclusion
section flags this as future work, not something it solves.

**Positioning: BhuNetra is not a replacement for DILRMP. It is a verification and
decision-support layer that plugs into it.**

## 3. Goals

| Goal | Success looks like |
|---|---|
| Detect data-quality anomalies in digitized records | Flag boundary overlaps, area mismatches, ownership inconsistencies with measurable precision/recall |
| Make every AI decision explainable | Every flag shows the specific reason it was raised |
| Keep a human in the loop | No automated rejection; every decision has an accountable officer and an audit trail |
| Demonstrate real cross-verification | Registry claims checked against satellite imagery, not just internal consistency |
| Stay legally and architecturally honest | Chain used only for immutable approval hashes; spatial data in PostGIS; explicit note on DPDP/IT Act relevance |

## 4. Non-goals (explicitly out of scope, say this to judges)

- Not a replacement for the Registration Act's legal deed-recording process
- Not a public/permissionless blockchain — government-authorized validators only,
  matching the reference IEEE paper's own recommendation against public mining
- Not attempting live integration with real Bhulekh/ULPIN/Aadhaar APIs during the
  hackathon — demo runs on a synthetic dataset built to resemble real record
  structure (see CLAUDE.md §2)
- Not claiming production-grade accuracy — reporting honest precision/recall on a
  hand-labeled synthetic validation set, in line with academic practice

## 5. Users / personas

- **Citizen / buyer**: wants to check a parcel's risk status before purchase
- **Revenue officer / land inspector**: reviews AI-flagged records, approves or
  overrides with a logged reason
- **District collector**: views aggregate dashboards — fraud trends, mutation
  delays, encroachment hotspots, village-level risk heatmap
- **Land rectifier** (per reference blockchain paper's role model): verifies
  conditions are met before a block is added

## 6. Core features (MVP for hackathon demo)

1. **Registry OCR intake** — upload a scanned/handwritten registry page, extract
   owner, khatian, survey number, village, area
2. **GIS anomaly detection** — topology checks on parcel geometry (overlap, gap,
   area deviation) using Isolation Forest, matching the best-performing model from
   the reference ML paper (precision 0.83 / recall 0.79 / F1 0.81 on their dataset)
3. **Ownership timeline + anomaly flag** — visual transfer history, flags
   suspiciously rapid resale patterns
4. **Satellite cross-check** — compares registry land-use claim against imagery for
   a small set of pre-loaded demo parcels
5. **Unified risk score (Green/Yellow/Red)** — weighted ensemble of the above four
   signals, not an independent fifth model
6. **Explanation panel** — every flag shows its top contributing reasons (SHAP or
   equivalent feature attribution)
7. **Officer review queue** — approve/override with mandatory reason, full audit
   log, nothing auto-rejects
8. **Revenue Court status field** — Clean / Stay Order / Mutation Pending / Court
   Case, visible before a transaction proceeds
9. **Blockchain approval hash** — on officer approval, a hash of the finalized
   record is written to a local permissioned chain for immutability

## 7. Stretch features (only if time remains)

- Village-level risk heatmap for district collectors
- Offline field verification mode (downloads village maps, records GPS/photos
  offline, syncs later) — describe the design even if not fully implemented
- Active learning loop: officer overrides feed back into anomaly model retraining

## 8. What this project adds beyond the two reference papers

| Reference paper | What it solves | What BhuNetra adds |
|---|---|---|
| ML anomaly detection paper | Detects bad records (boundary/ownership anomalies) via Isolation Forest/OC-SVM/DBSCAN | Adds satellite cross-verification, explanation layer, and routes detections into an actual officer workflow instead of stopping at detection |
| IEEE blockchain paper | Protects good records once entered, via permissioned Ethereum, smart contracts, ECDSA signatures | Adds the missing pre-entry verification step — the blockchain paper assumes uploaded data is correct; BhuNetra checks that assumption first |

## 9. Compliance and legal grounding (say this explicitly — most teams won't)

- **DPDP Act 2023**: Aadhaar-linked ownership data requires stated consent and
  data-minimization design; note this in the architecture even if full compliance
  tooling isn't built in 36 hours
- **IT Act 2000 (Sec 65B)**: relevant to digital record admissibility — the
  blockchain hash supports evidentiary integrity but does not itself replace the
  legally registered deed
- **Registration Act**: BhuNetra's blockchain hash is a trust/integrity layer on
  top of the legal registration process, not a substitute for it

## 10. Risks and honest mitigations

| Risk | Mitigation |
|---|---|
| No labeled ground truth for "real" fraud | Hand-label a small synthetic validation set; report precision/recall transparently, don't overclaim |
| 5-engine scope too large for hackathon window | Explicit REAL/RULE-STUB/MOCK tagging per engine (see CLAUDE.md); cut satellite engine first if needed |
| Live government/satellite API dependency during demo | Pre-load all data before presentation; no live external calls on stage |
| "We use blockchain" sounds like buzzword-chasing to judges | Have the specific PostGIS-vs-chain architectural answer ready (CLAUDE.md §3) |
| Regional-script OCR (most registries aren't in English) | Scope OCR demo to one state/script explicitly rather than implying general coverage |
| AI flag treated as final verdict | Human-in-the-loop is architecturally mandatory, not optional — no auto-rejection anywhere |

## 11. Success metrics for the demo/pitch

- Live OCR extraction on at least 3 sample registry pages
- At least 2 correctly detected synthetic GIS anomalies with visible explanation
- Ownership timeline flagging at least 1 injected suspicious pattern
- One end-to-end flow: upload → flag → explanation → officer approval → hash
  generated → audit log visible
- A one-slide answer ready for: "why not just use DILRMP," "why blockchain here
  specifically," and "how do you know your anomaly detection is accurate"

## 12. Team ownership (6-member team)

| Member | Responsibility |
|---|---|
| 1 | React frontend + map/dashboard UI |
| 2 | FastAPI backend + API integration |
| 3 | PostGIS + synthetic data generation + GIS engine |
| 4 | ML models (Isolation Forest, SHAP) + OCR |
| 5 | Solidity contract + local chain integration |
| 6 | Pitch deck, demo script, judge Q&A prep, integration testing |
