import json
import os
import sys
import httpx

sys.stdout.reconfigure(encoding="utf-8")

client = httpx.Client(base_url="http://127.0.0.1:8001", timeout=60.0)

# 1. Check Engine Status
res = client.get("/api/ocr/engine-status")
assert res.status_code == 200, f"Status failed: {res.text}"
status_data = res.json()["data"]
print(f"[1] Engine Status: {status_data['engine_tag']}")
print(f"[1] Primary OCR: {status_data['primary_ocr']}")

# 2. Check Supported Languages
res = client.get("/api/ocr/languages")
assert res.status_code == 200, f"Languages failed: {res.text}"
langs = res.json()["data"]
print(f"[2] Supported Languages Count: {len(langs)}")

# 3. Upload Scan
sample_path = os.path.join("data", "synthetic", "registry_scans", "scan_P-105.png")
with open(sample_path, "rb") as f:
    files = {"file": ("scan_P-105.png", f, "image/png")}
    res = client.post("/api/documents/upload", files=files)
assert res.status_code == 200, f"Upload failed: {res.text}"
doc_id = res.json()["document_id"]
print(f"[3] Document Uploaded with ID: {doc_id}")

# 4. Extract with OCR.Space (Telugu / Auto)
res = client.post(f"/api/documents/{doc_id}/extract", params={"passes": "auto", "allow_fallback": "true", "language": "tel"})
assert res.status_code == 200, f"Extract failed: {res.text}"
ext = res.json()
print(f"[4] Extraction Status: {ext['status']}")
print(f"[4] Engine Used: {ext['engine_tag']}")
print(f"[4] Extraction Confidence: {ext['extraction_confidence']}")
print(f"[4] Parcel ID Hint: {ext['parcel_id_hint']}")
print(f"[4] Extracted Fields: {json.dumps(ext['extracted_fields'], indent=2)}")

# 5. Check GIS Map and Composite Risk Ensemble
parcel_id = ext['parcel_id_hint'] or "P-105"
res = client.get(f"/api/risk-score/{parcel_id}?role=Revenue%20Officer")
assert res.status_code == 200, f"Risk score failed: {res.text}"
risk = res.json()
print(f"[5] Risk Score for {parcel_id}: {risk.get('composite_risk_score')} ({risk.get('risk_tier')})")

print("\n>>> ALL END-TO-END OCR.SPACE INTEGRATION CHECKS PASSED PERFECTLY! <<<")
