"""
backend/routers/translation.py — AI4Bharat IndicTransToolkit Multilingual Endpoints.

Repository: https://github.com/VarunGumma/IndicTransToolkit.git
Integrates 22 Indian language pre-processing & post-processing for IndicTrans2.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.indictrans_service import (
    translate_text_indictrans,
    translate_batch_indictrans,
    INDICTRANS_LANG_MAP
)

router = APIRouter(prefix="", tags=["Multilingual AI (IndicTransToolkit)"])


class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text content to translate")
    target_language: str = Field("hi", description="Target language code (hi, te, or, mr, bn, ta, kn, etc.)")
    source_language: str = Field("en", description="Source language code (en)")


class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(..., description="List of strings to translate")
    target_language: str = Field("hi", description="Target language code")
    source_language: str = Field("en", description="Source language code")


@router.post("/translate")
@router.post("/api/translate")
def translate_endpoint(payload: TranslationRequest) -> Dict[str, Any]:
    """Translate text using open-source IndicTransToolkit (AI4Bharat IndicTrans2)."""
    return translate_text_indictrans(
        text=payload.text,
        target_language=payload.target_language,
        source_language=payload.source_language
    )


@router.post("/translate/batch")
@router.post("/api/translate/batch")
def translate_batch_endpoint(payload: BatchTranslationRequest) -> Dict[str, Any]:
    """Translate batch of texts using IndicTransToolkit."""
    translations = translate_batch_indictrans(
        texts=payload.texts,
        target_language=payload.target_language,
        source_language=payload.source_language
    )
    return {
        "engine": "AI4Bharat IndicTransToolkit (IndicTrans2)",
        "translations": translations,
        "target_language": payload.target_language,
        "count": len(translations)
    }


@router.get("/translate/languages")
@router.get("/api/translate/languages")
def get_supported_languages() -> Dict[str, Any]:
    """Get list of supported sovereign Indian languages under IndicTrans2."""
    return {
        "provider": "AI4Bharat IndicTransToolkit (IndicTrans2)",
        "repository": "https://github.com/VarunGumma/IndicTransToolkit.git",
        "languages": [
            {"code": "en", "name": "English", "native": "English", "indic_code": "eng_Latn"},
            {"code": "hi", "name": "Hindi", "native": "हिन्दी", "indic_code": "hin_Deva"},
            {"code": "te", "name": "Telugu", "native": "తెలుగు", "indic_code": "tel_Telu"},
            {"code": "or", "name": "Odia", "native": "ଓଡ଼ିଆ", "indic_code": "ory_Orya"},
            {"code": "mr", "name": "Marathi", "native": "मराठी", "indic_code": "mar_Deva"},
            {"code": "bn", "name": "Bengali", "native": "বাংলা", "indic_code": "ben_Beng"},
            {"code": "ta", "name": "Tamil", "native": "தமிழ்", "indic_code": "tam_Taml"},
            {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ", "indic_code": "kan_Knda"},
            {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી", "indic_code": "guj_Gujr"},
            {"code": "ml", "name": "Malayalam", "native": "മലയാളം", "indic_code": "mal_Mlym"},
            {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ", "indic_code": "pan_Guru"}
        ]
    }
