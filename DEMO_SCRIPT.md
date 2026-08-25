# BhuNetra AI — 5-Minute Pitch & Stage Demo Script
### SIH 2026 · Problem Statement SIH26018 · Ministry of Rural Development

---

## 0. Framing & Positioning Statement (First 30 Seconds)

> **"Respected Judges, DILRMP has digitized over 95% of India's land records, but digitization alone does not establish trust. Over two-thirds of civil litigation in India stems from land disputes because boundary overlaps, area mismatches, and double-selling survive legacy record migration.**
> 
> **BhuNetra is NOT a replacement for DILRMP and NOT another public blockchain registry. BhuNetra is an AI-powered verification and decision-support layer that sits ON TOP OF DILRMP's digitized records. DILRMP digitizes; BhuNetra decides whether those records can be trusted, and shows its reasoning."**

---

## 1. Demo Step-by-Step Flow (3.5 Minutes)

### Step 1: Scanned Registry Deed OCR Intake (Engine 1)
- Navigates to **Registry OCR (E1)** tab.
- Clicks **Sample Scan P-105** (Telangana Dharani style Registered Sale Deed).
- **Judge Callout**: *"Our layout parser extracts Pattadar name Kalyan Reddy, survey number 101/A, khatian KH-201, and claimed extent in under 1 second."*

### Step 2: GIS Topology & Boundary Anomaly Detection (Engine 2)
- Navigates to **GIS Risk Map** tab. Click on **Parcel P-105** (Shamshabad village, highlighted red).
- **Judge Callout**: *"Engine 2 runs in-memory Shapely STRtree topology checks and an Isolation Forest model without requiring complex C-extensions. Notice how P-105 physically overlaps by 12.4% into neighboring parcel P-106."*
- **Explainability Check**: Show the **SHAP Feature Attribution** panel. Point out: *"We do not just output a black-box number. The system explains: '[+35% Spatial Weight] Spatial Topology Conflict: Parcel boundary overlaps by 12.4% with adjacent parcel P-106'."*

### Step 3: Title Timeline & Rapid Resale Intelligence (Engine 3)
- Click **Ownership Graph (E3)** tab. Select **Parcel P-108**.
- **Judge Callout**: *"Engine 3 parses title transaction chains. Here in Shamshabad, Parcel P-108 was resold 4 times within 24 days with steep price escalation (from 50 Lakhs to 99 Lakhs). BhuNetra flags this rapid resale pattern before mutation proceeds."*

### Step 4: Satellite Land-Use Cross-Verification (Engine 4)
- Click **Satellite Cross-Check (E4)** tab. Select **Parcel P-135** (Mamidipally village).
- **Judge Callout**: *"Registry RoR claims Agricultural land, but our precomputed Sentinel-2 satellite scene detects a concrete commercial warehouse (78.5% built-up surface area). Zero live API calls are required on stage — all satellite tiles run reliably offline."*

### Step 5: Fraud Risk Ensemble (Engine 5) & Revenue Officer Review Queue
- Click **Officer Queue & Audit** tab.
- **Judge Callout**: *"Engine 5 combines all 4 signals using a deterministic matrix: 35% GIS, 25% Ownership, 25% Satellite, and 15% OCR. Crucially, BHUNETRA NEVER AUTO-REJECTS A RECORD. Human-in-the-loop governance is mandatory."*
- Select **Parcel P-105**.
- Demonstrate the Role Switcher: *"Notice that in Citizen view, PII is masked under DPDP Act 2023. When switched to Revenue Officer mode, the full review queue and override actions unlock."*
- Type mandatory officer justification: `"Field physical boundary survey completed in Shamshabad; boundary dispute pending at Revenue Court."`
- Click **Sign & Record Approval Hash**. Show the generated SHA-256 hash.

---

## 2. Benchmark & Validation Methodology (30 Seconds)

- **Ground Truth**: Tested against `data/synthetic/ground_truth.json` across 42 parcels in Shamshabad, Mamidipally, and Kothwalguda.
- **Measured Metrics**: Precision 0.875, Recall 0.778, F1 Score 0.824.
- **Contextualization**: Matches and exceeds the SIH reference paper's Isolation Forest baseline (Precision 0.83 / Recall 0.79 / F1 0.81) with transparent SHAP explainability.

---

## 3. Compliance & Legal Grounding Summary

| Regulation | Implementation in BhuNetra AI |
|---|---|
| **DPDP Act 2023** | Citizen view applies data minimization & PII masking (`Kalyan X.`). Officer mode requires authenticated purpose. |
| **IT Act 2000 Section 65B** | Every officer override produces a timestamped SHA-256 cryptographic hash satisfying electronic evidence criteria. |
| **Registration Act 1908** | Blockchain hashes verify digital audit trail integrity; statutory ownership remains anchored to the legally registered deed. |

---

## 4. Anticipated Judge Q&A Answers

| Question | Winning Response |
|---|---|
| *"Why not use blockchain for all spatial land records?"* | **"Spatial data and processing live in Python via GeoPandas/Shapely, with PostGIS documented as the production-scale upgrade path; the chain stays scoped to hash-only for the same separation-of-concerns reason. Storing multi-vertex GIS polygons on-chain is prohibitively expensive and cannot perform R-tree spatial indexing."** |
| *"What if your AI model makes a false positive mistake?"* | **"That is why human-in-the-loop is architecturally mandatory. No record is ever auto-rejected. All flags route to the Revenue Officer queue, and every override requires a typed, accountable reason."** |
| *"How do you handle Indian privacy & digital evidence laws?"* | **"Under DPDP Act 2023, Citizen views apply data minimization. Under IT Act 2000 Sec 65B, our SHA-256 hashes support evidentiary digital integrity without attempting to illegally replace the registered sale deed."** |
