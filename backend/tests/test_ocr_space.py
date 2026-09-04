"""
backend/tests/test_ocr_space.py — Tests for OCR.Space Indic Multi-Language OCR Engine & Parser.
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from services import ocr_space_service
from services import extraction_service as ex


def test_supported_languages():
    langs = ocr_space_service.get_supported_languages()
    assert len(langs) >= 10
    codes = [l["code"] for l in langs]
    assert "hin" in codes
    assert "tel" in codes
    assert "tam" in codes
    assert "kan" in codes
    assert "mar" in codes
    assert "guj" in codes
    assert "ben" in codes
    assert "pan" in codes
    assert "mal" in codes
    assert "eng" in codes
    assert "auto" in codes


def test_language_normalization():
    assert ocr_space_service.normalize_language_code("hindi") == "hin"
    assert ocr_space_service.normalize_language_code("TELUGU") == "tel"
    assert ocr_space_service.normalize_language_code("tam") == "tam"
    assert ocr_space_service.normalize_language_code("kannada") == "kan"
    assert ocr_space_service.normalize_language_code("unknown_xyz") == "auto"


def test_indic_land_record_parser_hindi():
    hindi_sample = """
    उत्तर प्रदेश राजस्व परिषद - खतौनी (अधिकार अभिलेख)
    जिला: Lucknow (लखनऊ)
    तहसील: Mohanlalganj (मोहनलालगंज)
    ग्राम: Dehramau (देहरामऊ)
    खसरा संख्या: 45
    खाता संख्या: KH-142
    खातेदार का नाम: Chhote Lal (छोटे लाल)
    पिता का नाम: Ram Sumiran (राम सुमिरन)
    रकबा (क्षेत्रफल): 7090 Sq.m
    भूमि वर्गीकरण: कृषि (Agricultural)
    ULPIN: 09-08-01-045-00045-2026
    दस्तावेज़ संख्या: UP-LKO-2026-P-45
    """
    parsed = ocr_space_service.parse_indic_land_record_text(hindi_sample, language_hint="hin")
    vals = parsed["values"]

    assert vals["khasra_no"] == "45"
    assert "Chhote Lal" in vals["owner_name"]
    assert "Mohanlalganj" in vals["mandal"]
    assert "Lucknow" in vals["district"]
    assert vals["state"] == "Uttar Pradesh"
    assert vals["claimed_area_sqm"] == 7090.0
    assert vals["land_use_claim"] == "Agricultural"
    assert parsed["confidences"]["khasra_no"] >= 0.85
    assert parsed["confidences"]["owner_name"] >= 0.85


def test_indic_land_record_parser_telangana():
    telangana_sample = """
    తెలంగాణ ప్రభుత్వం - ధరణి పోర్టల్ (Dharani Portal)
    దస్తావేజు నమోదు సంఖ్య: TS-DHARANI-2026-P-105
    సర్వే నం: 101/A
    ఖాతా నం: KH-201
    పట్టాదారు పేరు: Kalyan Reddy
    తండ్రి పేరు: Venkat Reddy
    గ్రామం: Shamshabad
    మండలం: Shamshabad
    జిల్లా: Rangareddy
    రాష్ట్రం: Telangana
    విస్తీర్ణం: 4046.86 చ.మీ (1.00 ఎకరాలు)
    భూ వర్గీకరణ: వ్యవసాయం (Agricultural)
    ULPIN: 36-78431-105-2026
    """
    parsed = ocr_space_service.parse_indic_land_record_text(telangana_sample, language_hint="tel")
    vals = parsed["values"]

    assert vals["survey_no"] == "101/A"
    assert vals["khatian_no"] == "KH-201"
    assert "Kalyan Reddy" in vals["owner_name"]
    assert vals["village"] == "Shamshabad"
    assert vals["mandal"] == "Shamshabad"
    assert vals["district"] == "Rangareddy"
    assert vals["state"] == "Telangana"
    assert vals["claimed_area_sqm"] == 4046.86
    assert vals["area_acres_printed"] == 1.0
    assert vals["land_use_claim"] == "Agricultural"


def test_engine_status():
    status = ex.engine_status()
    assert "OCR.Space" in status["primary_ocr"]
    assert status["model_available"] is True
    assert len(status["supported_languages"]) >= 10


if __name__ == "__main__":
    test_supported_languages()
    test_language_normalization()
    test_indic_land_record_parser_hindi()
    test_indic_land_record_parser_telangana()
    test_engine_status()
    print("ALL OCR.SPACE UNIT TESTS PASSED SUCCESSFULLY!")
