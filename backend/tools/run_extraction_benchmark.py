"""
run_extraction_benchmark.py — measure REAL extraction accuracy for Engine 1.

Runs the live extraction service over every synthetic Dharani scan and diffs the
result against `data/synthetic/extraction_ground_truth.json` (the values actually
PRINTED on each page). Writes a machine-readable report the Collector dashboard
reads, so the accuracy number shown on stage is a measured number, not a claim.

WHAT IS AND IS NOT SCORED
-------------------------
Scored: the 10 fields in the ground-truth `scored_fields` list.
Not scored: intentional scan-vs-registry disagreements (`registry_mismatch`, e.g.
P-117's deed name differing from the registry). Those are validation-layer
findings, not extraction errors — penalising them would measure the wrong thing.

BEYOND RAW ACCURACY
-------------------
Also reports whether the confidence signal is *useful*: of the fields the model
got wrong, how many did it correctly route to officer review (flag recall), and
how accurate are the fields it claimed high confidence on (high-confidence
precision). A digitization system is only trustworthy if its uncertainty is honest.

USAGE
-----
    python backend/tools/run_extraction_benchmark.py
    python backend/tools/run_extraction_benchmark.py --passes 2
    python backend/tools/run_extraction_benchmark.py --only P-105 P-106
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from services import extraction_service as ex  # noqa: E402

SYNTH_DIR = ROOT / "data" / "synthetic"
SCANS_DIR = SYNTH_DIR / "registry_scans"
GT_PATH = SYNTH_DIR / "extraction_ground_truth.json"
REPORT_PATH = SYNTH_DIR / "extraction_benchmark.json"

NUMERIC_TOLERANCE_PCT = 1.0   # OCR of "15075.63" reading "15075.6" is not an error


def norm_text(value) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())


def field_matches(key: str, got, expected) -> bool:
    spec = ex.FIELD_BY_KEY.get(key)
    if spec is not None and spec.numeric:
        try:
            g, e = float(got), float(expected)
        except (TypeError, ValueError):
            return False
        if e == 0:
            return abs(g) < 1e-6
        return abs(g - e) / abs(e) * 100.0 <= NUMERIC_TOLERANCE_PCT
    return norm_text(got) == norm_text(expected)


def main() -> int:
    ap = argparse.ArgumentParser(description="Engine 1 extraction accuracy benchmark")
    ap.add_argument("--passes", default="auto", choices=["1", "2", "auto"])
    ap.add_argument("--only", nargs="*", default=None, help="Parcel ids, e.g. P-105 P-106")
    ap.add_argument("--out", default=str(REPORT_PATH))
    args = ap.parse_args()

    status = ex.engine_status()
    if not status["model_available"]:
        print("Extraction engine unavailable — cannot benchmark.")
        print(f"  host  : {status['host']}  (reachable={status['reachable']})")
        print(f"  model : {status['model']}")
        print(f"  hint  : {status['hint']}")
        return 2

    gt = json.loads(GT_PATH.read_text(encoding="utf-8"))
    scored_fields = gt["meta"]["scored_fields"]
    scans = gt["scans"]
    if args.only:
        wanted = {p.upper() for p in args.only}
        scans = {k: v for k, v in scans.items() if v["parcel_id"].upper() in wanted}

    passes = int(args.passes) if args.passes in {"1", "2"} else "auto"

    print(f"Engine   : {status['engine_tag']}")
    print(f"Scans    : {len(scans)}   Scored fields/scan: {len(scored_fields)}   Passes: {passes}")
    print("-" * 78)

    per_field = {f: {"correct": 0, "total": 0} for f in scored_fields}
    by_style = {"printed": {"correct": 0, "total": 0}, "handwritten": {"correct": 0, "total": 0}}
    conf_buckets = {"high_confidence": {"correct": 0, "total": 0},
                    "flagged_for_review": {"correct": 0, "total": 0}}
    documents = []
    started = time.time()

    for fname, entry in scans.items():
        img_path = SCANS_DIR / fname
        if not img_path.exists():
            print(f"  SKIP {fname} (missing image)")
            continue

        t0 = time.time()
        try:
            result = ex.extract_document(img_path.read_bytes(), passes=passes)
        except ex.ExtractionUnavailable as exc:
            print(f"  FAIL {fname}: {exc}")
            documents.append({"scan": fname, "parcel_id": entry["parcel_id"],
                              "error": str(exc)})
            continue
        elapsed = round(time.time() - t0, 2)

        style = entry["style"]
        doc = {"scan": fname, "parcel_id": entry["parcel_id"], "style": style,
               "handwritten": entry["handwritten"], "seconds": elapsed,
               "status": result.status,
               "document_confidence": result.document_confidence,
               "correct": 0, "total": 0, "errors": []}

        for key in scored_fields:
            expected = entry["fields"].get(key)
            got_field = result.fields.get(key, {})
            got = got_field.get("value")
            conf = got_field.get("confidence", 0.0)
            flagged = bool(got_field.get("needs_review"))
            ok = field_matches(key, got, expected)

            per_field[key]["total"] += 1
            by_style[style]["total"] += 1
            doc["total"] += 1
            bucket = "flagged_for_review" if flagged else "high_confidence"
            conf_buckets[bucket]["total"] += 1

            if ok:
                per_field[key]["correct"] += 1
                by_style[style]["correct"] += 1
                conf_buckets[bucket]["correct"] += 1
                doc["correct"] += 1
            else:
                doc["errors"].append({"field": key, "expected": expected, "extracted": got,
                                      "confidence": conf, "flagged_for_review": flagged,
                                      "failed_checks": got_field.get("checks", {}).get("failed", [])})

        acc = 100.0 * doc["correct"] / doc["total"] if doc["total"] else 0.0
        doc["field_accuracy_pct"] = round(acc, 1)
        documents.append(doc)
        print(f"  {style:>11} {entry['parcel_id']:<7} "
              f"{doc['correct']:>2}/{doc['total']:<2} = {acc:5.1f}%   "
              f"conf={result.document_confidence:.2f}  {result.status:<12} {elapsed:5.1f}s"
              + (f"  errors: {[e['field'] for e in doc['errors']]}" if doc["errors"] else ""))

    total_correct = sum(v["correct"] for v in per_field.values())
    total_fields = sum(v["total"] for v in per_field.values())
    wrong = [e for d in documents for e in d.get("errors", [])]
    wrong_flagged = sum(1 for e in wrong if e["flagged_for_review"])

    def pct(c, t):
        return round(100.0 * c / t, 1) if t else None

    report = {
        "meta": {
            "engine_tag": status["engine_tag"],
            "model": status["model"],
            "passes": str(passes),
            "confidence_threshold": ex.CONFIDENCE_THRESHOLD,
            "scored_fields": scored_fields,
            "numeric_tolerance_pct": NUMERIC_TOLERANCE_PCT,
            "documents": len([d for d in documents if "error" not in d]),
            "wall_clock_seconds": round(time.time() - started, 1),
            "note": ("Field-level accuracy against the values printed on each scan. "
                     "Intentional scan-vs-registry disagreements are validation findings, "
                     "not extraction errors, and are excluded from scoring."),
        },
        "summary": {
            "field_accuracy_pct": pct(total_correct, total_fields),
            "fields_correct": total_correct,
            "fields_total": total_fields,
            "printed_accuracy_pct": pct(by_style["printed"]["correct"], by_style["printed"]["total"]),
            "handwritten_accuracy_pct": pct(by_style["handwritten"]["correct"],
                                            by_style["handwritten"]["total"]),
            "high_confidence_accuracy_pct": pct(conf_buckets["high_confidence"]["correct"],
                                                conf_buckets["high_confidence"]["total"]),
            "flagged_field_accuracy_pct": pct(conf_buckets["flagged_for_review"]["correct"],
                                              conf_buckets["flagged_for_review"]["total"]),
            "review_flag_recall_pct": pct(wrong_flagged, len(wrong)),
            "fields_routed_to_review": conf_buckets["flagged_for_review"]["total"],
            "documents_needing_review": sum(1 for d in documents if d.get("status") == "NEEDS_REVIEW"),
        },
        "per_field": {k: {"accuracy_pct": pct(v["correct"], v["total"]), **v}
                      for k, v in per_field.items()},
        "documents": documents,
    }

    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    s = report["summary"]
    print("-" * 78)
    print(f"Field accuracy        : {s['field_accuracy_pct']}%  "
          f"({s['fields_correct']}/{s['fields_total']})")
    print(f"  printed             : {s['printed_accuracy_pct']}%")
    print(f"  handwritten         : {s['handwritten_accuracy_pct']}%")
    print(f"High-confidence acc.  : {s['high_confidence_accuracy_pct']}%  "
          f"(fields the engine did NOT flag)")
    print(f"Review-flag recall    : {s['review_flag_recall_pct']}%  "
          f"({wrong_flagged}/{len(wrong)} wrong fields correctly routed to an officer)")
    print(f"Docs needing review   : {s['documents_needing_review']}")
    print(f"Report                -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
