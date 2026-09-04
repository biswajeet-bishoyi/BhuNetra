"""
backend/routers/translation.py — Endpoints for Sarvam AI Sovereign Multilingual Translation & Voice Synthesis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.sarvam_service import (
    translate_text_sarvam,
    translate_batch_sarvam,
    synthesize_indic_speech,
    SARVAM_LANG_MAP
)

router = APIRouter(prefix="", tags=["Multilingual AI (Sarvam)"])


class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text content to translate")
    target_language: str = Field("hi", description="Target language code (hi, te, or/od, mr, bn, ta, kn, etc.)")
    source_language: str = Field("en", description="Source language code")
    mode: Optional[str] = Field("formal", description="Translation style (formal / modern / colloquial)")


class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(..., description="List of strings to translate")
    target_language: str = Field("hi", description="Target language code")
    source_language: str = Field("en", description="Source language code")


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to speak")
    language: str = Field("hi", description="Language code (hi, te, od, mr, bn, ta, etc.)")
    gender: Optional[str] = Field("female", description="Speaker voice: female or male")


@router.post("/translate")
@router.post("/api/translate")
def translate_endpoint(payload: TranslationRequest) -> Dict[str, Any]:
    """Translate a single text string using Sarvam AI Indic model."""
    return translate_text_sarvam(
        text=payload.text,
        target_language=payload.target_language,
        source_language=payload.source_language,
        mode=payload.mode or "formal"
    )


@router.post("/translate/batch")
@router.post("/api/translate/batch")
def translate_batch_endpoint(payload: BatchTranslationRequest) -> Dict[str, Any]:
    """Translate a batch of UI strings or dynamic land record sentences."""
    translations = translate_batch_sarvam(
        texts=payload.texts,
        target_language=payload.target_language,
        source_language=payload.source_language
    )
    return {
        "translations": translations,
        "target_language": payload.target_language,
        "count": len(translations)
    }


@router.post("/translate/tts")
@router.post("/api/translate/tts")
def tts_endpoint(payload: TTSRequest) -> Dict[str, Any]:
    """Generate audio voice speech for land record narration."""
    return synthesize_indic_speech(
        text=payload.text,
        target_language=payload.language,
        speaker_gender=payload.gender or "female"
    )


@router.get("/translate/languages")
@router.get("/api/translate/languages")
def get_supported_languages() -> Dict[str, Any]:
    """Get list of supported sovereign Indian languages."""
    return {
        "provider": "Sarvam AI (Mayura v1 & Bulbul v1)",
        "languages": [
            {"code": "en", "name": "English", "native": "English", "sarvam_code": "en-IN"},
            {"code": "hi", "name": "Hindi", "native": "हिन्दी", "sarvam_code": "hi-IN"},
            {"code": "te", "name": "Telugu", "native": "తెలుగు", "sarvam_code": "te-IN"},
            {"code": "or", "name": "Odia", "native": "ଓଡ଼ିଆ", "sarvam_code": "od-IN"},
            {"code": "mr", "name": "Marathi", "native": "मराठी", "sarvam_code": "mr-IN"},
            {"code": "bn", "name": "Bengali", "native": "বাংলা", "sarvam_code": "bn-IN"},
            {"code": "ta", "name": "Tamil", "native": "தமிழ்", "sarvam_code": "ta-IN"},
            {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ", "sarvam_code": "kn-IN"},
            {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી", "sarvam_code": "gu-IN"},
            {"code": "ml", "name": "Malayalam", "native": "മലയാളം", "sarvam_code": "ml-IN"},
            {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ", "sarvam_code": "pa-IN"}
        ]
    }
