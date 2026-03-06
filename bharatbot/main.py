"""
main.py – FastAPI entry point for BharatBot.

Exposes REST endpoints for text chat, voice chat (STT+TTS), the WhatsApp
webhook, a health check, and the frontend single-page application.
Uses Google Gemini for LLM, Azure Speech for STT/TTS, Azure Translator
for language detection, and Azure AI Search for knowledge retrieval.
"""

import base64
import logging
import os
from pathlib import Path
from typing import Annotated, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent singletons
# ---------------------------------------------------------------------------

from agents.agribot import AgriBot
from agents.healthbot import HealthBot
from agents.lawbot import LawBot
from gateway.router import classify_intent
from gateway.speech import audio_to_base64, speech_to_text, text_to_speech
from gateway.translator import detect_language, get_locale
from webhooks.whatsapp import (
    download_whatsapp_media,
    extract_message_from_payload,
    send_whatsapp_text,
    verify_webhook,
)

agribot = AgriBot()
healthbot = HealthBot()
lawbot = LawBot()

AGENT_MAP: dict = {
    "agribot": agribot,
    "healthbot": healthbot,
    "lawbot": lawbot,
}

AGENT_EMOJI: dict[str, str] = {
    "agribot": "🌾",
    "healthbot": "🏥",
    "lawbot": "⚖️",
}

# ---------------------------------------------------------------------------
# Startup log — confirm active services
# ---------------------------------------------------------------------------

logger.info("=" * 60)
logger.info("BharatBot starting up...")
logger.info("  LLM Backend       : Google Gemini (gemini-1.5-flash)")
logger.info("  Speech Service    : Azure Cognitive Services Speech")
logger.info("  Translator Service: Azure Translator API")
logger.info("  Knowledge Search  : Azure AI Search")
logger.info("  Agents loaded     : AgriBot, HealthBot, LawBot")
logger.info("=" * 60)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BharatBot API",
    description="Multilingual AI assistant for rural India — AgriBot, HealthBot, LawBot.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

FRONTEND_PATH: Path = Path(__file__).parent / "frontend" / "index.html"


async def _route_and_respond(user_message: str, thread_id: Optional[str]) -> dict:
    """Core pipeline: detect language → classify intent → run agent.

    Args:
        user_message: Raw text from the user.
        thread_id: Optional existing conversation thread ID.

    Returns:
        Dict with keys: response, language, agent, thread_id.
    """
    language: str = await detect_language(user_message)
    intent: str = classify_intent(user_message, language)
    agent = AGENT_MAP[intent]

    logger.info("Routing to %s (lang=%s, thread=%s)", intent, language, thread_id)

    response_text, new_thread_id = await agent.respond(user_message, thread_id)

    return {
        "response": response_text,
        "language": language,
        "agent": intent,
        "thread_id": new_thread_id,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def serve_frontend() -> FileResponse:
    """Serve the BharatBot single-page frontend application.

    Returns:
        HTML file response for the frontend UI.
    """
    if not FRONTEND_PATH.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(str(FRONTEND_PATH), media_type="text/html")


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint.

    Returns:
        JSON with service status, available agents, and version.
    """
    return JSONResponse({
        "status": "ok",
        "agents": ["agribot", "healthbot", "lawbot"],
        "services": {
            "llm": "Google Gemini (gemini-1.5-flash)",
            "speech": "Azure Cognitive Services Speech",
            "translator": "Azure Translator API",
            "search": "Azure AI Search",
        },
        "version": "1.0.0",
    })


@app.post("/chat/text")
async def chat_text(
    message: Annotated[str, Form()],
    thread_id: Annotated[Optional[str], Form()] = None,
) -> JSONResponse:
    """Handle a text chat message.

    Detects the language, classifies intent, routes to the correct agent,
    and returns the response along with metadata.

    Args:
        message: The user's text message (form field).
        thread_id: Optional existing thread ID for conversation continuity.

    Returns:
        JSON with response, language code, agent name, and thread_id.
    """
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        result = await _route_and_respond(message.strip(), thread_id)
        return JSONResponse(result)
    except Exception as exc:
        logger.error("chat/text failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


@app.post("/chat/voice")
async def chat_voice(
    audio: UploadFile = File(...),
    language: str = Form(default="hi-IN"),
) -> JSONResponse:
    """Handle a voice chat request via STT → agent → TTS pipeline.

    Converts uploaded audio to text, routes through the agent, converts
    the response back to speech, and returns the audio as base64.

    Args:
        audio: Uploaded audio file (WAV or OGG format).
        language: Azure Speech locale code of the user's language.

    Returns:
        JSON with transcript, response text, base64 audio, and agent name.
    """
    try:
        audio_bytes: bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        # STT: audio → text
        transcript: str = await speech_to_text(audio_bytes, language)
        if not transcript:
            logger.warning("STT produced empty transcript for language %s.", language)
            transcript = "आपकी आवाज़ समझ नहीं आई। कृपया फिर से बोलें।"

        # Route and get response
        result = await _route_and_respond(transcript, None)
        response_text: str = result["response"]
        agent_name: str = result["agent"]
        detected_lang: str = result["language"]
        locale_code: str = get_locale(detected_lang)

        # TTS: response text → audio bytes
        tts_audio: bytes = await text_to_speech(response_text, locale_code)
        audio_b64: str = audio_to_base64(tts_audio) if tts_audio else ""

        return JSONResponse({
            "transcript": transcript,
            "response": response_text,
            "audio_base64": audio_b64,
            "agent": agent_name,
            "language": detected_lang,
            "thread_id": result.get("thread_id", ""),
        })

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("chat/voice failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Voice chat error: {exc}")


@app.get("/webhook/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
) -> PlainTextResponse:
    """Verify the Meta WhatsApp webhook subscription.

    Called by Meta during webhook setup. Echoes back hub.challenge if the
    verify token matches WA_VERIFY_TOKEN.

    Args:
        hub_mode: Should be "subscribe" (sent by Meta).
        hub_verify_token: Token sent by Meta; must match WA_VERIFY_TOKEN.
        hub_challenge: Random challenge string from Meta.

    Returns:
        Plain text hub.challenge on success, or 403 Forbidden on failure.
    """
    challenge: Optional[str] = verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        raise HTTPException(status_code=403, detail="Verification failed.")
    return PlainTextResponse(challenge)


@app.post("/webhook/whatsapp")
async def whatsapp_incoming(request: Request) -> JSONResponse:
    """Handle incoming WhatsApp messages from Meta webhook.

    Parses the webhook payload, extracts the message (text or audio),
    routes it through the BharatBot pipeline, and replies via WhatsApp.

    Args:
        request: The raw FastAPI Request containing the Meta webhook payload.

    Returns:
        JSON {"status": "ok"} — Meta requires a 200 response.
    """
    try:
        payload: dict = await request.json()
        logger.info("WhatsApp webhook payload received.")

        message_data = extract_message_from_payload(payload)
        if not message_data:
            # Return 200 to acknowledge non-message webhooks (status updates, etc.)
            return JSONResponse({"status": "ok"})

        sender: str = message_data["from"]
        msg_type: str = message_data["type"]

        if msg_type == "text":
            user_text: str = message_data.get("text", "")
            if not user_text:
                return JSONResponse({"status": "ok"})

            result = await _route_and_respond(user_text, None)
            reply = (
                f"{AGENT_EMOJI.get(result['agent'], '🤖')} "
                f"{result['response']}"
            )
            await send_whatsapp_text(sender, reply)

        elif msg_type == "audio":
            media_id: str = message_data.get("media_id", "")
            if not media_id:
                return JSONResponse({"status": "ok"})

            # Download audio from WhatsApp
            audio_bytes: Optional[bytes] = await download_whatsapp_media(media_id)
            if not audio_bytes:
                await send_whatsapp_text(sender, "Sorry, I could not download your audio message.")
                return JSONResponse({"status": "ok"})

            # STT (default hi-IN — WhatsApp doesn't tell us user's language up front)
            transcript: str = await speech_to_text(audio_bytes, "hi-IN")
            if not transcript:
                await send_whatsapp_text(
                    sender,
                    "मैं आपकी आवाज़ नहीं समझ पाया। कृपया टेक्स्ट में लिखें।\n"
                    "(Could not understand audio. Please type your message.)",
                )
                return JSONResponse({"status": "ok"})

            result = await _route_and_respond(transcript, None)
            reply = (
                f"{AGENT_EMOJI.get(result['agent'], '🤖')} "
                f"[आपने कहा / You said]: {transcript}\n\n"
                f"{result['response']}"
            )
            await send_whatsapp_text(sender, reply)

        else:
            logger.info("Unsupported WhatsApp message type: %s", msg_type)

    except Exception as exc:
        logger.error("WhatsApp webhook error: %s", exc)
        # Always return 200 to Meta to prevent webhook retries
    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
