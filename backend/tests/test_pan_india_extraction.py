"""
backend/tests/test_pan_india_extraction.py — Validation of Dynamic Pan-India State Detection & Extraction.

Verifies:
  1. Odisha Schedule-1 Form 39-A extracts State=Odisha, Khata=192, Plot=349, Village, Mandal, District.
  2. Telangana Dharani Deed extracts State=Telangana and Dharani fields.
  3. Hindi / UP Bhulekh Record extracts State=Uttar Pradesh, Khasra, Khatauni, Tehsil, District.
  4. Bengali Banglarbhumi Record extracts State=West Bengal, Khatian, Dag, Mouza.
  5. Negative Assertion: Non-Telangana documents NEVER contain hardcoded Telangana defaults
     (e.g. Kalyan Reddy, Venkat Reddy, Shamshabad, Rangareddy, TS-DHARANI, KH-201, 101/A).
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from services.state_detector import detect_state
from services.multilingual_parser import parse_document_text


def test_odisha_schedule_1_form_39a_extraction():
    """Test 1: Upload / parse Odisha Schedule-1 Form 39-A."""
    odisha_ocr_sample = """
    04/09/2026, 09:55
    Schedule 1 Form No.39-A
    ମୌଜା : ଅଭିସଲପାଟଣା
    ଥାଜା : ବେଗୁନିଆ
    ଥାଜା ନମ୍ବର : 192
    ଖତିୟାନ
    about:blank
    ତହସିଲ: ଟାଙ୍ଗି
    ତହସିଲ ନମ୍ବର : 349
    ଜିଲ୍ଲା: ଖୋର୍ଦ୍ଧା
    ଜମିଦାରଙ୍କ ନାମ ଓ ଖେୱାଟ ବା ଖତିୟାନର କ୍ରମିକ ନମ୍ବର
    ଓଡିଶା ସରକାର ଖେୱାଟ ନମ୍ବର :- 1
    1) ଖତିୟାନର କ୍ରମିକ ନମ୍ବର
    15
    2) ପ୍ରଜାର ନାମ, ପିତାର ନାମ, ଜାତି ଓ ବାସସ୍ଥାନ ଜଗନ୍ନାଥ ପଟ୍ଟନାୟକ ପି:ବ୍ରଜବନ୍ଧୁ ପଟ୍ଟନାୟକ ଜା: କରଣ ବା: ନିଜଗାଁ
    3) ସ୍ଥିତିବାନ
    ଖଜଣା ସେସ୍
    ନିସ୍ତାର ସେସ୍ ଓ ଅନ୍ୟାନ୍ୟ
    ଦେୟ : 71.52
    """

    state, conf, signals = detect_state(odisha_ocr_sample)
    assert state == "Odisha", f"Expected Odisha, got {state} (signals: {signals})"
    assert conf >= 0.85

    res = parse_document_text(odisha_ocr_sample)
    vals = res["values"]

    assert vals["state"] == "Odisha"
    assert vals["khatian_no"] == "192", f"Expected Khata=192, got {vals['khatian_no']}"
    assert vals["survey_no"] == "349", f"Expected Plot=349, got {vals['survey_no']}"
    assert vals["khasra_no"] == "349"
    assert "ଅଭିସଲପାଟଣା" in vals["village"]
    assert "ଟାଙ୍ଗି" in vals["mandal"] or "ବେଗୁନିଆ" in vals["mandal"]
    assert "ଖୋର୍ଦ୍ଧା" in vals["district"]
    assert vals["owner_name"] == "ଜଗନ୍ନାଥ ପଟ୍ଟନାୟକ"
    assert vals["father_or_husband"] == "ବ୍ରଜବନ୍ଧୁ ପଟ୍ଟନାୟକ"
    assert "ସ୍ଥିତିବାନ" in vals["land_use_claim"]
    assert "Schedule 1 Form No.39-A" in vals["deed_registration_no"]

    # Strict negative check for Telangana demo values
    for val in vals.values():
        if val is not None:
            sval = str(val)
            assert "Kalyan Reddy" not in sval
            assert "Venkat Reddy" not in sval
            assert "Shamshabad" not in sval
            assert "Rangareddy" not in sval
            assert "TS-DHARANI" not in sval
            assert "KH-201" not in sval
            assert "101/A" not in sval


def test_telangana_dharani_extraction():
    """Test 2: Upload / parse Telangana Dharani deed."""
    telangana_sample = """
    GOVERNMENT OF TELANGANA
    CCLA DHARANI INTEGRATED LAND RECORDS MANAGEMENT SYSTEM
    RECORD OF RIGHTS (ROR - 1B)
    Pattadar Name: K. Rama Rao
    Father Name: K. Narayana Rao
    District: Rangareddy
    Mandal: Shamshabad
    Village: Mamidipally
    Khata No: KH-105
    Survey No: 104/A
    Extent: 12020.77 Sq.m (2.97 ఎకరాలు)
    Land Classification: Agricultural
    Deed Registration No: TS-DHARANI-2026-P-105
    ULPIN: 36-08420-1050-2026
    """

    state, conf, signals = detect_state(telangana_sample)
    assert state == "Telangana", f"Expected Telangana, got {state}"

    res = parse_document_text(telangana_sample)
    vals = res["values"]

    assert vals["state"] == "Telangana"
    assert vals["district"] == "Rangareddy"
    assert vals["mandal"] == "Shamshabad"
    assert vals["village"] == "Mamidipally"
    assert vals["survey_no"] == "104/A"
    assert vals["khatian_no"] == "KH-105"
    assert "K. Rama Rao" in vals["owner_name"]
    assert "K. Narayana Rao" in vals["father_or_husband"]
    assert vals["claimed_area_sqm"] == 12020.77
    assert vals["deed_registration_no"] == "TS-DHARANI-2026-P-105"
    assert vals["ulpin"] == "36-08420-1050-2026"


def test_hindi_up_bhulekh_extraction():
    """Test 3: Upload / parse mixed Hindi-English record (UP Bhulekh)."""
    up_bhulekh_sample = """
    उत्तर प्रदेश भूलेख खतौनी (अधिकार अभिलेख)
    जनपद : लखनऊ
    तहसील : मोहनलालगंज
    ग्राम : देहरामऊ
    खाता संख्या : 57
    खसरा संख्या : 45
    खातेदार का नाम : छोटे लाल
    पिता का नाम : राम सुमिरन
    रकबा : 0.7090 हेक्टेयर
    भूमि वर्गीकरण : कृषि
    बैनामा संख्या : UP-LKO-2026-REG-8421
    """

    state, conf, signals = detect_state(up_bhulekh_sample)
    assert state == "Uttar Pradesh", f"Expected Uttar Pradesh, got {state}"

    res = parse_document_text(up_bhulekh_sample)
    vals = res["values"]

    assert vals["state"] == "Uttar Pradesh"
    assert vals["district"] == "लखनऊ"
    assert vals["mandal"] == "मोहनलालगंज"
    assert vals["village"] == "देहरामऊ"
    assert vals["khatian_no"] == "57"
    assert vals["khasra_no"] == "45"
    assert vals["survey_no"] == "45"
    assert vals["owner_name"] == "छोटे लाल"
    assert vals["father_or_husband"] == "राम सुमिरन"
    assert vals["claimed_area_sqm"] == 7090.0  # 0.7090 hectare * 10000 sqm
    assert "कृषि" in vals["land_use_claim"] or "Agricultural" in vals["land_use_claim"]

    # Strict negative check for Telangana demo values
    for val in vals.values():
        if val is not None:
            sval = str(val)
            assert "Kalyan Reddy" not in sval
            assert "Shamshabad" not in sval
            assert "Rangareddy" not in sval
            assert "TS-DHARANI" not in sval


def test_bengali_banglarbhumi_extraction():
    """Test 4: Upload / parse Bengali record (Banglarbhumi)."""
    bengali_sample = """
    পশ্চিমবঙ্গ সরকার
    বাংলারভূমি খতিয়ান তথ্য (ফর্ম ৪)
    জেলা : হাওড়া
    ব্লক : উলুবেড়িয়া
    মৌজা : রাজাপুর
    খতিয়ান নং : 842
    দাগ নং : 1205
    রায়তের নাম : সুবীর কুমার সেন
    পিতার নাম : অশোক সেন
    জমির পরিমাণ : 0.25 একড়
    জমির শ্রেণী : বাস্তু
    দলিল নম্বর : WB-HOW-2026-DL-109
    """

    state, conf, signals = detect_state(bengali_sample)
    assert state == "West Bengal", f"Expected West Bengal, got {state}"

    res = parse_document_text(bengali_sample)
    vals = res["values"]

    assert vals["state"] == "West Bengal"
    assert vals["district"] == "হাওড়া"
    assert vals["mandal"] == "উলুবেড়িয়া"
    assert vals["village"] == "রাজাপুর"
    assert vals["khatian_no"] == "842"
    assert vals["survey_no"] == "1205"
    assert vals["owner_name"] == "সুবীর কুমার সেন"
    assert vals["father_or_husband"] == "অশোক সেন"
    assert vals["claimed_area_sqm"] == round(0.25 * 4046.86, 2)
    assert vals["land_use_claim"] == "বাস্তু"

    # Strict negative check for Telangana demo values
    for val in vals.values():
        if val is not None:
            sval = str(val)
            assert "Kalyan Reddy" not in sval
            assert "Shamshabad" not in sval
            assert "Rangareddy" not in sval
            assert "TS-DHARANI" not in sval
