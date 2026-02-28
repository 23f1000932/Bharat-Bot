"""
gateway/translator.py – Language detection and translation for BharatBot.

Uses the Azure Translator API to detect the language of incoming text and
to translate text between Indian regional languages.
"""

import logging
import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRANSLATOR_KEY: str = os.getenv("TRANSLATOR_KEY", "")
TRANSLATOR_ENDPOINT: str = os.getenv(
    "TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com"
)

# Maps ISO 639-1 language codes to Azure Speech Service locale codes
LANG_CODE_MAP: dict[str, str] = {
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "en": "en-IN",
}

# Maps Azure Speech locale codes to Azure Neural TTS female voice names
VOICE_MAP: dict[str, str] = {
    "hi-IN": "hi-IN-SwaraNeural",
    "ta-IN": "ta-IN-PallaviNeural",
    "te-IN": "te-IN-ShrutiNeural",
    "kn-IN": "kn-IN-SapnaNeural",
    "mr-IN": "mr-IN-AarohiNeural",
    "bn-IN": "bn-IN-TanishaaNeural",
    "gu-IN": "gu-IN-DhwaniNeural",
    "en-IN": "en-IN-NeerjaNeural",
}

# Supported language codes for BharatBot
SUPPORTED_LANGUAGES: set[str] = set(LANG_CODE_MAP.keys())


async def detect_language(text: str) -> str:
    """Detect the language of the given text using Azure Translator.

    Calls the Azure Translator /detect endpoint and returns the ISO 639-1
    language code (e.g. "hi", "ta", "en").  Falls back to "hi" (Hindi) if
    detection fails or the detected language is not supported.

    Args:
        text: The input text whose language needs to be detected.

    Returns:
        ISO 639-1 language code string such as "hi", "ta", "te", etc.
    """
    if not text or not text.strip():
        logger.warning("detect_language called with empty text; defaulting to 'hi'.")
        return "hi"

    if not TRANSLATOR_KEY:
        logger.warning("TRANSLATOR_KEY not set; defaulting to 'hi'.")
        return "hi"

    url = f"{TRANSLATOR_ENDPOINT}/detect"
    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": "global",
        "Content-Type": "application/json",
    }
    body = [{"text": text[:500]}]  # API limit; trimming for efficiency

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=body, params={"api-version": "3.0"})
            response.raise_for_status()
            data = response.json()
            detected: str = data[0].get("language", "hi")
            logger.info("Detected language: %s for text snippet: %.40s", detected, text)
            # Return detected code if supported, else default to Hindi
            return detected if detected in SUPPORTED_LANGUAGES else "hi"
    except Exception as exc:
        logger.error("Language detection failed: %s. Defaulting to 'hi'.", exc)
        return "hi"


async def translate_text(text: str, from_lang: str, to_lang: str) -> str:
    """Translate text from one language to another using Azure Translator.

    Args:
        text: The text to translate.
        from_lang: Source ISO 639-1 language code (e.g. "hi").
        to_lang: Target ISO 639-1 language code (e.g. "en").

    Returns:
        Translated text string. Returns the original text on failure.
    """
    if from_lang == to_lang:
        return text

    if not TRANSLATOR_KEY:
        logger.warning("TRANSLATOR_KEY not set; returning original text.")
        return text

    url = f"{TRANSLATOR_ENDPOINT}/translate"
    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": "global",
        "Content-Type": "application/json",
    }
    params = {
        "api-version": "3.0",
        "from": from_lang,
        "to": to_lang,
    }
    body = [{"text": text}]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=body, params=params)
            response.raise_for_status()
            data = response.json()
            translated: str = data[0]["translations"][0]["text"]
            logger.info("Translated from '%s' to '%s'.", from_lang, to_lang)
            return translated
    except Exception as exc:
        logger.error("Translation failed (%s→%s): %s. Returning original text.", from_lang, to_lang, exc)
        return text


def get_locale(lang_code: str) -> str:
    """Get the Azure Speech locale code for a given ISO language code.

    Args:
        lang_code: ISO 639-1 language code (e.g. "hi").

    Returns:
        Azure Speech locale string (e.g. "hi-IN"). Defaults to "hi-IN".
    """
    return LANG_CODE_MAP.get(lang_code, "hi-IN")


def get_voice(locale_code: str) -> str:
    """Get the Azure Neural TTS voice name for a given locale.

    Args:
        locale_code: Azure Speech locale (e.g. "hi-IN").

    Returns:
        Azure Neural TTS voice name string. Defaults to the Hindi voice.
    """
    return VOICE_MAP.get(locale_code, "hi-IN-SwaraNeural")
