"""
generate_scans.py — Realistic bilingual (Telugu + English) Telangana "Dharani"
Record-of-Rights (Pahani / RoR) deed scans for the BhuNetra digitization demo.

WHY THIS EXISTS
---------------
The OCR core of BhuNetra must read *real* text off *real* looking scans. Pillow
on Windows has no libraqm, so it cannot shape Telugu (conjuncts / matras render
broken). Browsers ship full HarfBuzz Indic shaping, so we render each deed as
HTML/CSS and screenshot it with headless Chrome/Edge (no extra pip deps), then
apply a light PIL "scanned" degradation pass.

PIPELINE
--------
    parcels.geojson  (authoritative digital registry)
        -> per-scan bilingual deed HTML  (values taken FROM the registry)
        -> headless-browser screenshot   (correct Telugu shaping)
        -> mild PIL degradation          (rotation / noise / blur / vignette)
    + extraction_ground_truth.json       (the EXACT values printed on each scan)

GROUND TRUTH vs REGISTRY
------------------------
`extraction_ground_truth.json` records what is *printed* on each image — the OCR
target used to measure extraction accuracy. It is deliberately DISTINCT from the
registry: intentional scan-vs-registry disagreements (see `registry_mismatch`)
are what the validation layer must catch, and must NOT be scored as OCR errors.
"""

import os
import json
import subprocess
import urllib.parse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# --- Paths (resolve relative to repo root, independent of CWD) ---------------
ROOT = Path(__file__).resolve().parents[2]
SYNTH_DIR = ROOT / "data" / "synthetic"
SCANS_DIR = SYNTH_DIR / "registry_scans"
PARCELS_PATH = SYNTH_DIR / "parcels.geojson"
GT_PATH = SYNTH_DIR / "extraction_ground_truth.json"

PAGE_W, PAGE_H = 900, 1240  # long side < 1280 -> safe for the vision model

# --- Browser detection (Chrome or Edge; both ship Indic text shaping) --------
_BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    for p in _BROWSER_CANDIDATES:
        if os.path.exists(p):
            return p
    raise RuntimeError(
        "No Chrome/Edge found for HTML->PNG rendering. Install Chrome or Edge, "
        "or add its path to _BROWSER_CANDIDATES in generate_scans.py."
    )


# --- Telugu transliteration tables (script demo lives in Telangana/Dharani) --
FN_TE = {
    "Kalyan": "కళ్యాణ్", "Venkat": "వెంకట్", "Srinivas": "శ్రీనివాస్", "Ravi": "రవి",
    "Ananya": "అనన్య", "Prasad": "ప్రసాద్", "Sujatha": "సుజాత", "Anand": "ఆనంద్",
    "Nagaraju": "నాగరాజు", "Kavitha": "కవిత", "Suresh": "సురేష్", "Praveen": "ప్రవీణ్",
    "Swapna": "స్వప్న", "Mahesh": "మహేష్",
}
LN_TE = {
    "Reddy": "రెడ్డి", "Rao": "రావు", "Goud": "గౌడ్", "Chary": "చారి", "Yadav": "యాదవ్",
    "Naidu": "నాయుడు", "Varma": "వర్మ", "Kumar": "కుమార్", "Sharma": "శర్మ", "Babu": "బాబు",
}
VILLAGE_TE = {"Shamshabad": "శంషాబాద్", "Mamidipally": "మామిడిపల్లి", "Kothwalguda": "కొత్వాల్‌గూడ"}
LU_TE = {"Agricultural": "వ్యవసాయం", "Residential": "నివాస", "Commercial": "వాణిజ్య"}
STATE_TE = "తెలంగాణ"
DISTRICT_TE = "రంగారెడ్డి"
MANDAL_TE = "శంషాబాద్"


def te_name(en_name):
    """Transliterate an 'First Last' English name to Telugu (best-effort)."""
    parts = en_name.split()
    out = []
    for i, w in enumerate(parts):
        if i == 0:
            out.append(FN_TE.get(w, w))
        else:
            out.append(LN_TE.get(w, w))
    return " ".join(out)


def acres_from_sqm(sqm):
    return round(sqm / 4046.86, 2)


# --- The scan set: 14 printed + 2 handwritten -------------------------------
# owner_print: override the printed pattadar name to seed a scan-vs-registry
# discrepancy the validation layer must flag (NOT an OCR error).
SCAN_SPEC = [
    {"pid": "P-101", "style": "printed"},
    {"pid": "P-102", "style": "printed"},
    {"pid": "P-103", "style": "printed"},
    {"pid": "P-105", "style": "printed"},   # spatial overlap anomaly; scan itself is clean
    {"pid": "P-108", "style": "printed"},   # rapid-resale anomaly; scan clean
    {"pid": "P-112", "style": "printed"},   # area deviation: printed claim >> GIS actual
    {"pid": "P-117", "style": "printed", "owner_print": "Ravi Kumar"},  # owner mismatch vs registry
    {"pid": "P-118", "style": "printed"},
    {"pid": "P-124", "style": "printed"},
    {"pid": "P-130", "style": "printed"},   # area deviation
    {"pid": "P-131", "style": "printed"},
    {"pid": "P-132", "style": "printed"},
    {"pid": "P-135", "style": "printed"},   # land-use mismatch vs satellite; scan says Agricultural
    {"pid": "P-140", "style": "printed"},
    {"pid": "P-106", "style": "handwritten"},   # hand-filled -> low confidence -> officer review
    {"pid": "P-125", "style": "handwritten"},   # hand-filled -> low confidence -> officer review
]


def _row(label_te, label_en, value_html, hand=False):
    val_cls = "val hand" if hand else "val"
    return f"""<tr>
      <td class="lbl"><span class="te">{label_te}</span><br><span class="en">{label_en}</span></td>
      <td class="{val_cls}">{value_html}</td>
    </tr>"""


def deed_html(rec, spec):
    """Build one bilingual Dharani RoR deed as an HTML string."""
    pid = rec["parcel_id"]
    hand = spec["style"] == "handwritten"
    owner_en = spec.get("owner_print", rec["owner_name"])
    owner_te = te_name(owner_en)
    father_en = "Narsimha " + owner_en.split()[-1]
    village_en = rec["village"]
    village_te = VILLAGE_TE.get(village_en, village_en)
    lu_en = rec["land_use_claim"]
    lu_te = LU_TE.get(lu_en, lu_en)
    area = rec["claimed_area_sqm"]
    deed_no = f"TS-DHARANI-2026-{pid}"

    # In printed deeds the pattadar name & village appear bilingually; in the
    # hand-filled form the values are written in Latin cursive only.
    owner_cell = f"{owner_te} / {owner_en}" if not hand else owner_en
    village_cell = f"{village_te} / {village_en}" if not hand else village_en
    lu_cell = f"{lu_te} / {lu_en}" if not hand else lu_en

    rows = "".join([
        _row("దస్తావేజు నమోదు సంఖ్య", "Deed Registration No.", deed_no, hand),
        _row("నమోదు తేదీ", "Date of Registration", "14-05-2026", hand),
        _row("రాష్ట్రం / జిల్లా", "State / District", f"{STATE_TE} / Telangana &nbsp;·&nbsp; {DISTRICT_TE} / Rangareddy", hand),
        _row("మండలం", "Mandal", f"{MANDAL_TE} / Shamshabad", hand),
        _row("గ్రామం", "Village", village_cell, hand),
        _row("సర్వే నంబర్", "Survey / Sub-division No.", rec["survey_no"], hand),
        _row("ఖాతా నంబర్", "Khatian / Passbook No.", rec["khatian_no"], hand),
        _row("భూ కమతం గుర్తింపు సంఖ్య (ULPIN)", "Unique Land Parcel ID", rec["ulpin"], hand),
        _row("పట్టాదారు పేరు", "Pattadar (Recorded Owner)", owner_cell, hand),
        _row("తండ్రి / భర్త పేరు", "Father / Husband Name", father_en, hand),
        _row("విస్తీర్ణం", "Recorded Extent", f"{area} sq.m &nbsp;({acres_from_sqm(area)} ఎకరాలు)", hand),
        _row("భూ వర్గీకరణ", "Land Classification", lu_cell, hand),
    ])

    stamp = "ధరణి · DHARANI"
    return f"""<!doctype html><html lang="te"><head><meta charset="utf-8"><style>
      html,body{{margin:0;padding:0;background:#e9e6dc;}}
      *{{box-sizing:border-box;}}
      .page{{position:relative;width:{PAGE_W}px;height:{PAGE_H}px;background:#fbf9f1;
            padding:26px 30px;font-family:'Segoe UI',Arial,sans-serif;color:#1b1b1b;
            border:3px double #2f5d34;box-shadow:inset 0 0 0 1px #6f8f74;overflow:hidden;}}
      .te{{font-family:'Nirmala UI','Gautami','Noto Sans Telugu',sans-serif;}}
      .watermark{{position:absolute;top:46%;left:50%;transform:translate(-50%,-50%) rotate(-24deg);
            font-size:120px;color:rgba(47,93,52,.06);font-family:'Nirmala UI',sans-serif;white-space:nowrap;}}
      .head{{display:flex;align-items:center;gap:16px;border-bottom:2px solid #2f5d34;padding-bottom:12px;}}
      .emblem{{width:74px;height:74px;border-radius:50%;border:2px solid #2f5d34;flex:0 0 auto;
            display:flex;align-items:center;justify-content:center;text-align:center;
            font-size:10px;color:#2f5d34;line-height:1.1;}}
      .titles{{flex:1;text-align:center;}}
      .titles .t1{{font-size:30px;font-weight:700;color:#1f3d1f;}}
      .titles .t2{{font-size:19px;font-weight:600;letter-spacing:.5px;}}
      .titles .t3{{font-size:14px;color:#33474f;margin-top:2px;}}
      .formno{{flex:0 0 auto;font-size:11px;border:1px solid #888;padding:4px 8px;color:#444;text-align:center;}}
      .subttl{{text-align:center;font-size:15px;margin:12px 0 8px;color:#1f3d1f;font-weight:600;}}
      table{{width:100%;border-collapse:collapse;font-size:16px;}}
      td{{border:1px solid #b9c3b2;padding:8px 10px;vertical-align:middle;}}
      td.lbl{{width:44%;background:#f1f0e6;}}
      td.lbl .en{{font-size:12px;color:#5a5a5a;}}
      tr:nth-child(even) td.val{{background:#fdfcf6;}}
      .val{{font-size:17px;}}
      .hand{{font-family:'Ink Free','Segoe Print','Bradley Hand',cursive;color:#123a8a;font-size:22px;}}
      .bounds{{margin-top:12px;border:1px solid #b9c3b2;padding:8px 10px;font-size:13px;background:#f6f5ec;}}
      .bounds b{{color:#1f3d1f;}}
      .foot{{position:absolute;left:30px;right:30px;bottom:26px;}}
      .seal{{position:absolute;right:36px;bottom:96px;width:150px;height:150px;border-radius:50%;
            border:3px solid #2f5d34;color:#2f5d34;display:flex;flex-direction:column;
            align-items:center;justify-content:center;text-align:center;font-size:11px;
            transform:rotate(-8deg);opacity:.85;line-height:1.35;}}
      .sig{{font-size:13px;color:#333;margin-top:6px;}}
    </style></head><body><div class="page">
      <div class="watermark te">{stamp}</div>
      <div class="head">
        <div class="emblem te">సత్యమేవ<br>జయతే</div>
        <div class="titles">
          <div class="t1 te">తెలంగాణ ప్రభుత్వం</div>
          <div class="t2">GOVERNMENT OF TELANGANA</div>
          <div class="t3 te">రిజిస్ట్రేషన్ &amp; స్టాంపుల శాఖ · Registration &amp; Stamps Dept.</div>
        </div>
        <div class="formno">FORM 1-B<br><span class="te">పహాణీ</span></div>
      </div>
      <div class="subttl te">హక్కుల రికార్డు — RECORD OF RIGHTS (RoR / Pahani)</div>
      <table>{rows}</table>
      <div class="bounds te">
        <b>చతుర్హద్దులు / Boundaries.</b>
        ఉత్తరం (N): Survey {rec['survey_no']} Pathway &nbsp;·&nbsp;
        దక్షిణం (S): Adjacent Field &nbsp;·&nbsp;
        తూర్పు (E): Village Link Road &nbsp;·&nbsp;
        పడమర (W): Irrigation Channel
      </div>
      <div class="seal te">సబ్ రిజిస్ట్రార్<br>SUB-REGISTRAR<br>శంషాబాద్ మండలం<br>GOVT OF TELANGANA</div>
      <div class="foot">
        <div class="sig">పట్టాదారు సంతకం / Pattadar Signature: ______________________</div>
        <div class="sig">సబ్ రిజిస్ట్రార్ సంతకం / Sub-Registrar Signature: ______________________</div>
      </div>
    </div></body></html>"""


def render_html_to_png(browser, html, out_png, w=PAGE_W, h=PAGE_H):
    tmp_html = Path(out_png).with_suffix(".html")
    tmp_html.write_text(html, encoding="utf-8")
    file_url = "file:///" + urllib.parse.quote(str(tmp_html).replace("\\", "/"), safe=":/")
    cmd = [
        browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
        "--force-device-scale-factor=1", f"--window-size={w},{h}",
        f"--screenshot={out_png}", file_url,
    ]
    subprocess.run(cmd, capture_output=True, timeout=120)
    tmp_html.unlink(missing_ok=True)
    if not os.path.exists(out_png):
        raise RuntimeError(f"Headless render produced no file: {out_png}")


def degrade_png(path, heavy=False, seed=0):
    """Apply a mild 'scanned document' degradation so the image is not pixel-clean."""
    rng = np.random.RandomState(seed)
    im = Image.open(path).convert("RGB")
    angle = rng.uniform(-2.2, 2.2) if heavy else rng.uniform(-1.0, 1.0)
    im = im.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(233, 230, 220))
    arr = np.asarray(im).astype(np.float32)
    h, w, _ = arr.shape
    yy, xx = np.mgrid[0:h, 0:w]
    vignette = 1.0 - 0.10 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    arr *= vignette[..., None]
    sigma = 9.0 if heavy else 4.0
    arr += rng.normal(0, sigma, arr.shape)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(0.7 if heavy else 0.3))
    im.save(path)


def generate_scans():
    print("Generating realistic bilingual Dharani deed scans (browser-rendered)...")
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    print(f"  Using browser: {browser}")

    parcels = json.loads(PARCELS_PATH.read_text(encoding="utf-8"))
    by_pid = {f["properties"]["parcel_id"]: f["properties"] for f in parcels["features"]}

    gt = {
        "meta": {
            "note": (
                "Field-level extraction ground truth = the exact values PRINTED on each "
                "scan image, used to measure OCR/extraction accuracy. This is DISTINCT "
                "from the registry (parcels.geojson). Intentional scan-vs-registry "
                "disagreements are listed under 'registry_mismatch' and must be caught by "
                "the validation layer, NOT scored as OCR errors."
            ),
            "scored_fields": [
                "survey_no", "khatian_no", "ulpin", "owner_name", "village",
                "mandal", "district", "claimed_area_sqm", "land_use_claim",
                "deed_registration_no",
            ],
        },
        "scans": {},
    }

    for spec in SCAN_SPEC:
        pid = spec["pid"]
        rec = by_pid[pid]
        hand = spec["style"] == "handwritten"
        fname = f"scan_{pid}.png"
        out_png = SCANS_DIR / fname

        render_html_to_png(browser, deed_html(rec, spec), str(out_png))
        degrade_png(str(out_png), heavy=hand, seed=int(pid.split("-")[1]))

        owner_printed = spec.get("owner_print", rec["owner_name"])
        entry = {
            "parcel_id": pid,
            "style": spec["style"],
            "handwritten": hand,
            "expected_low_confidence": hand,
            "fields": {
                "survey_no": rec["survey_no"],
                "khatian_no": rec["khatian_no"],
                "ulpin": rec["ulpin"],
                "owner_name": owner_printed,
                "father_or_husband": "Narsimha " + owner_printed.split()[-1],
                "village": rec["village"],
                "mandal": "Shamshabad",
                "district": "Rangareddy",
                "state": "Telangana",
                "claimed_area_sqm": rec["claimed_area_sqm"],
                "land_use_claim": rec["land_use_claim"],
                "deed_registration_no": f"TS-DHARANI-2026-{pid}",
            },
            "registry_mismatch": {},
        }
        if owner_printed != rec["owner_name"]:
            entry["registry_mismatch"]["owner_name"] = {
                "printed_on_scan": owner_printed,
                "registry_value": rec["owner_name"],
                "note": "Deed name differs from digital registry; validation must flag.",
            }
        gt["scans"][fname] = entry
        print(f"  [{spec['style']:>11}] {fname}  ({rec['village']}, owner='{owner_printed}')")

    GT_PATH.write_text(json.dumps(gt, ensure_ascii=False, indent=2), encoding="utf-8")
    n_hand = sum(1 for s in SCAN_SPEC if s["style"] == "handwritten")
    print(f"Generated {len(SCAN_SPEC)} scans ({n_hand} handwritten) in {SCANS_DIR}")
    print(f"Extraction ground truth -> {GT_PATH}")


if __name__ == "__main__":
    generate_scans()
