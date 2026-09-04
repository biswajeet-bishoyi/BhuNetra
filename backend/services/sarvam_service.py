"""
backend/services/sarvam_service.py — Sovereign Indian Multilingual Integration with Sarvam AI.

Provides:
1. Indic Text Translation across 11+ Indian languages (Hindi, Odia, Telugu, Marathi, Bengali, Tamil, Kannada, etc.)
2. Intelligent In-Memory Translation Cache (reduces API latency & prevents repeated calls)
3. Indic Text-to-Speech (TTS) Voice Synthesis for Citizen Audio Land Records Readout
"""

from __future__ import annotations

import os
import json
import httpx
from typing import Any, Dict, List, Optional

# Supported Language Code Mappings
SARVAM_LANG_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "te": "te-IN",
    "or": "od-IN",
    "od": "od-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "ta": "ta-IN",
    "kn": "kn-IN",
    "gu": "gu-IN",
    "ml": "ml-IN",
    "pa": "pa-IN"
}

# In-memory translation cache: (text, src_lang, tgt_lang) -> translated_text
_TRANSLATION_CACHE: Dict[str, str] = {}


def get_sarvam_api_key() -> str:
    """Retrieve Sarvam AI API Key from environment."""
    return os.environ.get("SARVAM_API_KEY", "sk_0vhfrs36_SYxDTNI44LJdWld2xQ0wLcNO").strip()


def translate_text_sarvam(
    text: str,
    target_language: str = "hi",
    source_language: str = "en",
    mode: str = "formal"
) -> Dict[str, Any]:
    """
    Translate text into any Indic language using Sarvam AI Sovereign API.
    """
    if not text or not text.strip():
        return {"translated_text": text, "source": source_language, "target": target_language}

    src_code = SARVAM_LANG_MAP.get(source_language.lower(), "en-IN")
    tgt_code = SARVAM_LANG_MAP.get(target_language.lower(), "hi-IN")

    if src_code == tgt_code:
        return {"translated_text": text, "source": source_language, "target": target_language}

    cache_key = f"{src_code}:{tgt_code}:{text.strip()}"
    if cache_key in _TRANSLATION_CACHE:
        return {
            "translated_text": _TRANSLATION_CACHE[cache_key],
            "source": source_language,
            "target": target_language,
            "cached": True
        }

    api_key = get_sarvam_api_key()
    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "input": text,
        "source_language_code": src_code,
        "target_language_code": tgt_code,
        "mode": mode,
        "model": "mayura:v1",
        "enable_preprocessing": True
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                "https://api.sarvam.ai/translate",
                headers=headers,
                json=payload
            )
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("translated_text", text)
                _TRANSLATION_CACHE[cache_key] = translated
                return {
                    "translated_text": translated,
                    "source": source_language,
                    "target": target_language,
                    "request_id": data.get("request_id")
                }
            else:
                return {
                    "translated_text": text,
                    "error": f"Sarvam API status {resp.status_code}: {resp.text}",
                    "source": source_language,
                    "target": target_language
                }
    except Exception as exc:
        return {
            "translated_text": text,
            "error": str(exc),
            "source": source_language,
            "target": target_language
        }


def translate_batch_sarvam(
    texts: List[str],
    target_language: str = "hi",
    source_language: str = "en"
) -> List[str]:
    """Batch translation of multiple strings."""
    results = []
    for t in texts:
        res = translate_text_sarvam(t, target_language, source_language)
        results.append(res.get("translated_text", t))
    return results


def synthesize_indic_speech(
    text: str,
    target_language: str = "hi",
    speaker_gender: str = "female"
) -> Dict[str, Any]:
    """
    Generate Indian Accent / Indic Voice Speech via Sarvam AI TTS.
    """
    api_key = get_sarvam_api_key()
    tgt_code = SARVAM_LANG_MAP.get(target_language.lower(), "hi-IN")

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": [text[:500]],
        "target_language_code": tgt_code,
        "speaker": "meera" if speaker_gender == "female" else "arvind",
        "pitch": 0,
        "pace": 1.05,
        "loudness": 1.5,
        "speech_sample_rate": 22050,
        "enable_preprocessing": True,
        "model": "bulbul:v1"
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                "https://api.sarvam.ai/text-to-speech",
                headers=headers,
                json=payload
            )
            if resp.status_code == 200:
                data = resp.json()
                audios = data.get("audios", [])
                return {
                    "audio_base64": audios[0] if audios else None,
                    "status": "SUCCESS"
                }
            else:
                return {"error": resp.text, "status": "FAILED"}
    except Exception as exc:
        return {"error": str(exc), "status": "FAILED"}
