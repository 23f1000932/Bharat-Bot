"""
gateway/speech.py – Speech-to-Text and Text-to-Speech for BharatBot.

Uses Azure Cognitive Services Speech SDK to convert audio bytes to text
(STT) and to convert text responses back to audio bytes (TTS).  Supports
all 7 Indian regional languages via neural voice synthesis.
"""

import base64
import logging
import os
import tempfile

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SPEECH_KEY: str = os.getenv("SPEECH_KEY", "")
SPEECH_REGION: str = os.getenv("SPEECH_REGION", "centralindia")


def _get_speech_config():
    """Build and return an Azure SpeechConfig object.

    Returns:
        azure.cognitiveservices.speech.SpeechConfig instance or None on error.
    """
    try:
        import azure.cognitiveservices.speech as speechsdk  # noqa: PLC0415

        if not SPEECH_KEY:
            logger.warning("SPEECH_KEY is not set; speech features will be unavailable.")
            return None
        config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        return config
    except ImportError:
        logger.error("azure-cognitiveservices-speech package is not installed.")
        return None
    except Exception as exc:
        logger.error("Failed to create SpeechConfig: %s", exc)
        return None


async def speech_to_text(audio_bytes: bytes, language_code: str = "hi-IN") -> str:
    """Convert audio bytes to text using Azure Cognitive Services STT.

    Accepts raw audio bytes, saves to a temporary WAV file, runs Azure
    Speech recognition for the specified locale, and returns the
    transcribed text string.

    Args:
        audio_bytes: Raw audio content in WAV or OGG format.
        language_code: Azure Speech locale code (e.g. "hi-IN", "ta-IN").

    Returns:
        Transcribed text string. Returns empty string on failure.
    """
    if not audio_bytes:
        logger.warning("speech_to_text received empty audio bytes.")
        return ""

    try:
        import azure.cognitiveservices.speech as speechsdk  # noqa: PLC0415

        speech_config = _get_speech_config()
        if speech_config is None:
            return ""

        speech_config.speech_recognition_language = language_code

        # Save audio bytes to a temporary file for the SDK
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            audio_config = speechsdk.audio.AudioConfig(filename=tmp_path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, audio_config=audio_config
            )

            result = recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info("STT success (lang=%s): %.60s", language_code, result.text)
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("STT: no speech could be recognized from audio.")
                return ""
            else:
                logger.warning("STT failed – reason: %s", result.reason)
                return ""
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except Exception as exc:
        logger.error("speech_to_text error: %s", exc)
        return ""


async def text_to_speech(text: str, language_code: str = "hi-IN") -> bytes:
    """Convert text to audio bytes using Azure Neural TTS.

    Uses the appropriate female Neural voice for the given locale to
    synthesize speech and returns the resulting audio as bytes.

    Args:
        text: The text to synthesize into speech.
        language_code: Azure Speech locale code (e.g. "hi-IN", "ta-IN").

    Returns:
        MP3 audio bytes. Returns empty bytes on failure.
    """
    if not text or not text.strip():
        logger.warning("text_to_speech received empty text.")
        return b""

    from gateway.translator import VOICE_MAP  # noqa: PLC0415

    voice_name: str = VOICE_MAP.get(language_code, "hi-IN-SwaraNeural")

    try:
        import azure.cognitiveservices.speech as speechsdk  # noqa: PLC0415

        speech_config = _get_speech_config()
        if speech_config is None:
            return b""

        speech_config.speech_synthesis_voice_name = voice_name
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )

        # Synthesize to an in-memory pull stream
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=None
        )

        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data: bytes = result.audio_data
            logger.info(
                "TTS success (lang=%s, voice=%s): %d bytes",
                language_code, voice_name, len(audio_data),
            )
            return audio_data
        else:
            cancellation = result.cancellation_details
            logger.warning(
                "TTS failed – reason: %s | %s",
                result.reason, cancellation.error_details,
            )
            return b""

    except Exception as exc:
        logger.error("text_to_speech error: %s", exc)
        return b""


def audio_to_base64(audio_bytes: bytes) -> str:
    """Encode audio bytes to a base64 string for JSON transport.

    Args:
        audio_bytes: Raw audio bytes (WAV or MP3).

    Returns:
        Base64-encoded string of the audio data.
    """
    return base64.b64encode(audio_bytes).decode("utf-8")
