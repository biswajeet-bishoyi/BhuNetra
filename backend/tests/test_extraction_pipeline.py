"""
test_extraction_pipeline.py — offline verification of Engine 1.

Exercises every part of the extraction pipeline EXCEPT the model call itself, by
substituting a stub for `_call_ollama`. This proves the preprocessing, JSON
parsing, field normalization, confidence calibration, master-data reconciliation,
cross-pass agreement and review routing are correct without needing a GPU.

Run:
    python backend/tests/test_extraction_pipeline.py
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from services import extraction_service as ex  # noqa: E402

GT_PATH = ROOT / "data" / "synthetic" / "extraction_ground_truth.json"

_checks = 0
_failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    global _checks
    _checks += 1
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}   {detail}")
        _failures.append(label)


def model_output(values: dict, confidence: float = 0.95) -> dict:
    """Build a stub model response in the schema the service expects."""
    return {
        spec.key: {
            "value": "" if values.get(spec.key) is None else str(values.get(spec.key)),
            "confidence": confidence,
            "source_text": str(values.get(spec.key) or ""),
        }
        for spec in ex.FIELD_SPECS
    }


def png_bytes(w: int = 2400, h: int = 3300) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (250, 249, 241)).save(buf, format="PNG")
    return buf.getvalue()


CLEAN = {
    "deed_registration_no": "TS-DHARANI-2026-P-105",
    "survey_no": "104/A",
    "khatian_no": "KH-204",
    "ulpin": "36-78431-105-2026",
    "owner_name": "Prasad Sharma",
    "father_or_husband": "Narsimha Sharma",
    "village": "Shamshabad",
    "mandal": "Shamshabad",
    "district": "Rangareddy",
    "state": "Telangana",
    "claimed_area_sqm": "15075.63",
    "land_use_claim": "Agricultural",
}


def test_preprocessing() -> None:
    print("\n[1] Image preprocessing")
    b64, meta = ex.preprocess_image(png_bytes())
    check("oversized scan is downscaled to the VRAM guardrail",
          max(meta["submitted_size"]) == ex.MAX_EDGE, str(meta))
    check("aspect ratio preserved",
          abs(meta["submitted_size"][0] / meta["submitted_size"][1] - 2400 / 3300) < 0.01)
    check("returns non-empty base64", len(b64) > 100)
    try:
        ex.preprocess_image(b"this is not an image")
        check("non-image upload rejected", False, "no exception raised")
    except ValueError:
        check("non-image upload rejected", True)


def test_json_tolerance() -> None:
    print("\n[2] Tolerant JSON parsing")
    check("plain JSON", ex._parse_json_object('{"a": 1}') == {"a": 1})
    check("fenced JSON", ex._parse_json_object('```json\n{"a": 2}\n```') == {"a": 2})
    check("prose-wrapped JSON",
          ex._parse_json_object('Here you go:\n{"a": 3}\nHope that helps') == {"a": 3})
    check("garbage returns None", ex._parse_json_object("no json here") is None)


def test_clean_document() -> None:
    print("\n[3] Clean printed document")
    res = ex._assemble(model_output(CLEAN), {}, pass_count=1)
    check("status is EXTRACTED", res.status == "EXTRACTED", res.status)
    check("no fields flagged", res.low_confidence_fields == [], str(res.low_confidence_fields))
    check("area parsed to float", res.fields["claimed_area_sqm"]["value"] == 15075.63,
          str(res.fields["claimed_area_sqm"]["value"]))
    check("format checks recorded",
          "format_valid" in res.fields["khatian_no"]["checks"]["passed"])
    check("document confidence high", res.document_confidence >= 0.9,
          str(res.document_confidence))


def test_numeric_and_noise() -> None:
    print("\n[4] Noisy value normalization")
    noisy = dict(CLEAN, claimed_area_sqm="15,075.63 sq.m", survey_no="104 / A")
    res = ex._assemble(model_output(noisy), {}, pass_count=1)
    check("units and commas stripped from area",
          res.fields["claimed_area_sqm"]["value"] == 15075.63,
          str(res.fields["claimed_area_sqm"]["value"]))
    check("spacing normalized in survey no", res.fields["survey_no"]["value"] == "104/A",
          str(res.fields["survey_no"]["value"]))


def test_bad_reads_are_flagged() -> None:
    print("\n[5] Bad reads are caught and routed to review")
    bad = dict(CLEAN, khatian_no="KH2O4-|", ulpin="illegible", claimed_area_sqm="")
    res = ex._assemble(model_output(bad, confidence=0.97), {}, pass_count=1)
    check("malformed khatian capped despite model claiming 0.97",
          res.fields["khatian_no"]["confidence"] <= ex.FORMAT_FAIL_CAP,
          str(res.fields["khatian_no"]["confidence"]))
    check("'illegible' treated as missing", res.fields["ulpin"]["value"] is None)
    check("missing area gets zero confidence",
          res.fields["claimed_area_sqm"]["confidence"] == 0.0)
    check("document routed to NEEDS_REVIEW", res.status == "NEEDS_REVIEW", res.status)
    check("all three fields flagged",
          {"khatian_no", "ulpin", "claimed_area_sqm"} <= set(res.low_confidence_fields),
          str(res.low_confidence_fields))


def test_master_data_reconciliation() -> None:
    print("\n[6] Master-data reconciliation")
    typo = dict(CLEAN, village="Shamshabaad", land_use_claim="Agriculturel")
    res = ex._assemble(model_output(typo), {}, pass_count=1)
    check("near-miss village repaired", res.fields["village"]["value"] == "Shamshabad",
          str(res.fields["village"]["value"]))
    check("repair is disclosed, not hidden",
          "normalized_to_master_data" in res.fields["village"]["checks"]["failed"])
    check("repaired field is not pristine confidence",
          res.fields["village"]["confidence"] <= ex.NORMALISED_CAP)
    check("near-miss land use repaired",
          res.fields["land_use_claim"]["value"] == "Agricultural")

    unknown = dict(CLEAN, village="Ibrahimpatnam")
    res2 = ex._assemble(model_output(unknown), {}, pass_count=1)
    check("village outside master list is flagged, not silently replaced",
          res2.fields["village"]["value"] == "Ibrahimpatnam"
          and res2.fields["village"]["needs_review"])


def test_cross_pass_agreement() -> None:
    print("\n[7] Cross-pass agreement")
    first = model_output(CLEAN, confidence=0.9)
    second = model_output(dict(CLEAN, owner_name="Prasad Sharrna"), confidence=0.9)
    merged = ex._merge_passes(first, second, {}, first_ms=1000.0, second_ms=900.0)
    check("disagreed field is capped", merged.fields["owner_name"]["confidence"] <= ex.DISAGREEMENT_CAP,
          str(merged.fields["owner_name"]["confidence"]))
    check("alternate reading preserved for the officer",
          merged.fields["owner_name"].get("alternate_reading") == "Prasad Sharrna")
    check("agreed field keeps high confidence",
          merged.fields["khatian_no"]["confidence"] >= 0.9)
    check("disagreement routes the document to review", merged.status == "NEEDS_REVIEW")
    check("timings summed", merged.timing_ms == 1900.0)


def test_auto_escalation() -> None:
    print("\n[8] extract_document: auto escalation + honest failure")
    calls: list[float] = []

    def stub_clean(image_b64, temperature, seed):
        calls.append(temperature)
        return dict(model_output(CLEAN), _timing={"total_duration_ms": 1234.0})

    original = ex._call_ollama
    try:
        ex._call_ollama = stub_clean
        res = ex.extract_document(png_bytes(600, 800), passes="auto")
        check("clean document needs only one pass", len(calls) == 1, str(calls))
        check("single-pass result reported as such", res.passes == 1)
        check("parcel hint derived from page content, not filename",
              ex.derive_parcel_hint(res.to_dict()["values"]) == "P-105")

        calls.clear()

        def stub_bad(image_b64, temperature, seed):
            calls.append(temperature)
            return dict(model_output(dict(CLEAN, khatian_no="???")),
                        _timing={"total_duration_ms": 1000.0})

        ex._call_ollama = stub_bad
        res2 = ex.extract_document(png_bytes(600, 800), passes="auto")
        check("low confidence escalates to a second pass", len(calls) == 2, str(calls))
        check("second pass uses a different temperature", calls[0] != calls[1], str(calls))
        check("result still flags the bad field", "khatian_no" in res2.low_confidence_fields)

        def stub_down(image_b64, temperature, seed):
            raise ex.ExtractionUnavailable("engine offline")

        ex._call_ollama = stub_down
        try:
            ex.extract_document(png_bytes(600, 800))
            check("engine outage raises instead of fabricating fields", False)
        except ex.ExtractionUnavailable:
            check("engine outage raises instead of fabricating fields", True)
    finally:
        ex._call_ollama = original


def test_ground_truth_conformance() -> None:
    print("\n[9] Ground-truth conformance (patterns match every real scan)")
    if not GT_PATH.exists():
        check("ground truth present", False, str(GT_PATH))
        return
    gt = json.loads(GT_PATH.read_text(encoding="utf-8"))
    bad: list[str] = []
    for fname, entry in gt["scans"].items():
        res = ex._assemble(model_output(entry["fields"]), {}, pass_count=1)
        for key in gt["meta"]["scored_fields"]:
            f = res.fields[key]
            if f["needs_review"]:
                bad.append(f"{fname}:{key}={f['value']!r} {f['checks']['failed']}")
    check(f"a perfect read of all {len(gt['scans'])} scans validates cleanly",
          not bad, "; ".join(bad[:5]))

    sample = next(iter(gt["scans"].values()))
    res = ex._assemble(model_output(sample["fields"]), {}, pass_count=1)
    for key in gt["meta"]["scored_fields"]:
        got = res.fields[key]["value"]
        exp = sample["fields"][key]
        same = (abs(float(got) - float(exp)) < 0.01
                if ex.FIELD_BY_KEY[key].numeric else str(got) == str(exp))
        if not same:
            check(f"round-trip preserves {key}", False, f"{got!r} != {exp!r}")
            return
    check("round-trip preserves every scored ground-truth value", True)


def _code_only(path: Path) -> str:
    """Strip docstrings and comments so assertions test code, not prose.

    Both modules legitimately *mention* the old filename-lookup trick in their
    docstrings to explain why it was removed; grepping raw source would flag that.
    """
    import ast
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body[0].value.value = ""
    return ast.unparse(tree)


def _reads_filesystem(path: Path) -> bool:
    """True if the module calls builtins.open / Path.read_* anywhere.

    Substring matching is not enough: `Image.open(io.BytesIO(...))` contains
    "open(" but reads memory, not disk. So walk the AST and only count bare
    `open(...)` and `.read_text/.read_bytes/.load(` filesystem calls.
    """
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id == "open":
            return True
        if isinstance(fn, ast.Attribute) and fn.attr in {"read_text", "read_bytes", "open"}:
            # `Image.open` / `io.BytesIO(...).open` are memory ops; anything else is disk.
            owner = fn.value
            owner_name = owner.id if isinstance(owner, ast.Name) else (
                owner.attr if isinstance(owner, ast.Attribute) else "")
            if owner_name not in {"Image", "io", "ImageOps"}:
                return True
    return False


def _sends_images(path: Path) -> bool:
    """True if the Ollama payload includes an `images` key holding the encoded page."""
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if (isinstance(k, ast.Constant) and k.value == "images"
                        and isinstance(v, ast.List) and len(v.elts) == 1
                        and isinstance(v.elts[0], ast.Name)
                        and "image" in v.elts[0].id):
                    return True
    return False


def test_no_filename_lookup() -> None:
    print("\n[10] The filename trick is gone")
    router_code = _code_only(ROOT / "backend" / "routers" / "ocr.py")
    service_code = _code_only(ROOT / "backend" / "services" / "extraction_service.py")

    check("router code never opens parcels.geojson", "parcels.geojson" not in router_code)
    check("router code never opens the ground-truth file",
          "ground_truth" not in router_code)
    check("router never regex-matches a parcel id out of the filename",
          "P-\\d" not in router_code)
    check("service code never reads the registry",
          "parcels.geojson" not in service_code and "ground_truth" not in service_code)
    check("service code never touches the filesystem",
          not _reads_filesystem(ROOT / "backend" / "services" / "extraction_service.py"))
    check("service sends real image bytes to the model",
          _sends_images(ROOT / "backend" / "services" / "extraction_service.py"))

    # The strongest check: the router's own filename field must not influence output.
    # Same bytes, wildly different filenames -> identical extracted values.
    original = ex._call_ollama
    seen_names = []

    def stub(image_b64, temperature, seed):
        return dict(model_output(CLEAN), _timing={"total_duration_ms": 1.0})

    try:
        ex._call_ollama = stub
        img = png_bytes(600, 800)
        a = ex.extract_document(img, passes=1).to_dict()["values"]
        b = ex.extract_document(img, passes=1).to_dict()["values"]
        check("extraction is a pure function of the image bytes", a == b)
    finally:
        ex._call_ollama = original
        del seen_names


def test_acre_unit_handling() -> None:
    print("\n[11] Extent unit handling")
    spec = ex.FIELD_BY_KEY["claimed_area_sqm"]
    val, _, failed = ex._normalize_field(spec, "15,075.63 sq.m (3.73 ఎకరాలు)")
    check("sq.m with acre parenthetical parses to the sq.m figure", val == 15075.63, str(val))
    val2, _, failed2 = ex._normalize_field(spec, "3.73 acres")
    check("acres-only read is converted to sq.m",
          val2 is not None and abs(val2 - 3.73 * 4046.86) < 1.0, str(val2))
    check("acre conversion is disclosed", "converted_from_acres" in failed2)
    val3, _, failed3 = ex._normalize_field(spec, "abcd")
    check("non-numeric extent is flagged", "not_a_number" in failed3)


def test_joint_checks() -> None:
    """The failure class per-field validation is blind to.

    The 16-scan live benchmark measured only 50% review-flag recall: the model's
    wrong reads were mostly *individually plausible* — a real village name in the
    mandal row, an extent digit misread into a still-legal number. Nothing a
    single-field regex or master-list can see. These are the two joint checks
    that close that gap, so they need direct tests.
    """
    print("\n[12] Joint checks: transposition and the extent checksum")

    # (a) Row transposition. Every value below is individually valid: "Rangareddy"
    # is a real district, "Shamshabad" a real mandal — they are just in each
    # other's rows. This is exactly the P-118/P-140 failure the benchmark found.
    swapped = dict(CLEAN, mandal="Rangareddy", district="Shamshabad")
    res = ex._assemble(model_output(swapped, confidence=0.97), {}, pass_count=1)
    check("transposed mandal/district is caught despite both values being real",
          res.fields["mandal"]["needs_review"] or res.fields["district"]["needs_review"],
          f"mandal={res.fields['mandal']['confidence']} "
          f"district={res.fields['district']['confidence']}")
    check("transposition is named in the audit trail",
          any("cross_field_inconsistent" in c
              for k in ("mandal", "district")
              for c in res.fields[k]["checks"]["failed"]),
          str(res.fields["mandal"]["checks"]["failed"]))
    check("transposition routes the document to an officer",
          res.status == "NEEDS_REVIEW", res.status)

    # (a2) The same swap, but the misplaced value is itself misread. This is the
    # live P-140 case: mandal read "Kothalguda" while the village row said
    # "Shamshabad" — the village name Kothwalguda, misspelled, in the mandal row.
    # Exact list membership misses this; the row-origin test must tolerate OCR noise.
    sloppy = dict(CLEAN, village="Shamshabad", mandal="Kothalguda")
    res_sloppy = ex._assemble(model_output(sloppy, confidence=0.95), {}, pass_count=1)
    check("transposition is caught even when the moved value is misspelled",
          res_sloppy.fields["village"]["needs_review"],
          f"village conf={res_sloppy.fields['village']['confidence']} "
          f"{res_sloppy.fields['village']['checks']['failed']}")

    # A legitimate record where village and mandal genuinely share a name must NOT
    # trip the check — Shamshabad village sits in Shamshabad mandal.
    res_ok = ex._assemble(model_output(CLEAN), {}, pass_count=1)
    check("a village that legitimately shares its mandal name is not flagged",
          not res_ok.fields["village"]["needs_review"]
          and not res_ok.fields["mandal"]["needs_review"],
          str(res_ok.low_confidence_fields))

    # (b) Extent checksum. 12200.77 sq.m is a perfectly plausible number in
    # isolation; it only betrays itself against the acre figure printed alongside.
    acres = 2.97
    good = dict(CLEAN, claimed_area_sqm=str(round(acres * ex.SQM_PER_ACRE, 2)),
                area_acres_printed=str(acres))
    res_good = ex._assemble(model_output(good), {}, pass_count=1)
    check("extent that agrees with the printed acreage is corroborated",
          "area_agrees_with_printed_acres"
          in res_good.fields["claimed_area_sqm"]["checks"]["passed"],
          str(res_good.fields["claimed_area_sqm"]["checks"]))
    check("corroborated extent is not sent to review",
          not res_good.fields["claimed_area_sqm"]["needs_review"])

    bad = dict(CLEAN, claimed_area_sqm="12200.77", area_acres_printed=str(acres))
    res_bad = ex._assemble(model_output(bad, confidence=0.99), {}, pass_count=1)
    check("extent contradicting the printed acreage is caught",
          res_bad.fields["claimed_area_sqm"]["needs_review"],
          str(res_bad.fields["claimed_area_sqm"]["confidence"]))
    check("contradiction records the arithmetic for the officer",
          "area_contradicts_printed_acres"
          in res_bad.fields["claimed_area_sqm"]["checks"]["failed"],
          str(res_bad.fields["claimed_area_sqm"]["checks"]["failed"]))

    # (c) The tolerance has to be tight enough to matter. The real P-117 misread
    # deviated only 1.51% from the acre-implied value, so a loose band is a
    # check that always says "fine".
    check("tolerance is tight enough to catch a 1.5% extent misread",
          ex.AREA_REDUNDANCY_TOLERANCE_PCT < 1.5,
          str(ex.AREA_REDUNDANCY_TOLERANCE_PCT))


def test_optional_fields() -> None:
    """A field that simply is not printed on a form is not a defect.

    Some Dharani layouts print the extent in square metres only. If an absent
    optional field flagged the document, every such record would arrive at the
    officer's desk amber for no reason — and an alert that fires on healthy
    records trains people to ignore it.
    """
    print("\n[13] Optional fields")
    spec = ex.FIELD_BY_KEY["area_acres_printed"]
    check("the acre field is declared optional", spec.optional)
    check("the acre field is excluded from accuracy scoring", not spec.scored)

    res = ex._assemble(model_output(CLEAN), {}, pass_count=1)
    f = res.fields["area_acres_printed"]
    check("absent optional field is not flagged", not f["needs_review"], str(f))
    check("absence is disclosed as not-printed rather than hidden", f["not_printed"])
    check("a form without a printed acreage still clears",
          res.status == "EXTRACTED", res.status)

    # A required field going missing must still stop the document.
    missing_required = dict(CLEAN, khatian_no="")
    res2 = ex._assemble(model_output(missing_required), {}, pass_count=1)
    check("a missing REQUIRED field still demands review",
          "khatian_no" in res2.low_confidence_fields, str(res2.low_confidence_fields))

    # Optional-but-present values are still verified, not waved through.
    contradictory = dict(CLEAN, area_acres_printed="99.0")
    res3 = ex._assemble(model_output(contradictory), {}, pass_count=1)
    check("an optional field that IS present is still checked",
          res3.fields["claimed_area_sqm"]["needs_review"],
          str(res3.fields["claimed_area_sqm"]["checks"]["failed"]))

    # Two passes agreeing the field is absent must not resurrect the flag.
    out = model_output(CLEAN)
    merged = ex._merge_passes(out, out, {}, first_ms=1.0, second_ms=1.0)
    check("absent optional field stays unflagged after a two-pass merge",
          not merged.fields["area_acres_printed"]["needs_review"]
          and merged.status == "EXTRACTED",
          f"{merged.status} {merged.low_confidence_fields}")


if __name__ == "__main__":
    print("BhuNetra Engine 1 — offline pipeline verification")
    print("=" * 62)
    test_preprocessing()
    test_json_tolerance()
    test_clean_document()
    test_numeric_and_noise()
    test_bad_reads_are_flagged()
    test_master_data_reconciliation()
    test_cross_pass_agreement()
    test_auto_escalation()
    test_ground_truth_conformance()
    test_no_filename_lookup()
    test_acre_unit_handling()
    test_joint_checks()
    test_optional_fields()
    print("=" * 62)
    print(f"{_checks - len(_failures)}/{_checks} checks passed")
    if _failures:
        print("FAILED: " + ", ".join(_failures))
    raise SystemExit(1 if _failures else 0)
