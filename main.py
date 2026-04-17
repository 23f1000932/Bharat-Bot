"""
main.py – FastAPI entry point for BharatBot.

Exposes REST endpoints for text chat, voice chat (STT+TTS), a health
check, and the frontend single-page application.
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
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

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
agribot = AgriBot()
healthbot = HealthBot()
lawbot = LawBot()

AGENT_MAP: dict = {
    "agribot": agribot,
    "healthbot": healthbot,
    "lawbot": lawbot,
}

# ---------------------------------------------------------------------------
# Startup log — confirm active services
# ---------------------------------------------------------------------------

logger.info("=" * 60)
logger.info("BharatBot starting up...")
logger.info("  LLM Backend       : Google Gemini (gemini-2.5-flash)")
logger.info("  Speech Service    : Azure Cognitive Services Speech")
logger.info("  Translator Service: Azure Translator API")
logger.info("  Knowledge Search  : Azure AI Search")
logger.info("  Agents loaded     : AgriBot, HealthBot, LawBot")
logger.info("  WhatsApp          : Disabled")
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
CHAT_PATH: Path = Path(__file__).parent / "frontend" / "chat.html"


async def _route_and_respond(
    user_message: str,
    thread_id: Optional[str],
    forced_agent: Optional[str] = None,
) -> dict:
    """Core pipeline: detect language → classify intent → run agent.

    Args:
        user_message: Raw text from the user.
        thread_id: Optional existing conversation thread ID.
        forced_agent: If provided and valid, skip intent classification and
                      route directly to this agent (e.g. 'agribot').

    Returns:
        Dict with keys: response, language, agent, thread_id.
    """
    language: str = await detect_language(user_message)

    if forced_agent and forced_agent in AGENT_MAP:
        intent = forced_agent
        logger.info("Agent explicitly selected by user: %s", intent)
    else:
        intent = classify_intent(user_message, language)

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


@app.get("/chat", response_class=HTMLResponse)
async def serve_chat_page() -> FileResponse:
    """Serve the dedicated chat interface page."""
    if not CHAT_PATH.exists():
        raise HTTPException(status_code=404, detail="Chat frontend not found.")
    return FileResponse(str(CHAT_PATH), media_type="text/html")


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
            "llm": "Google Gemini (gemini-2.5-flash)",
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
    agent: Optional[str] = Query(default=None),
) -> JSONResponse:
    """Handle a text chat message.

    Detects the language, classifies intent (unless an agent is explicitly
    specified via query param), routes to the correct agent, and returns
    the response along with metadata.

    Args:
        message: The user's text message (form field).
        thread_id: Optional existing thread ID for conversation continuity.
        agent: Optional query param to force a specific agent
               ('agribot', 'healthbot', or 'lawbot').

    Returns:
        JSON with response, language code, agent name, and thread_id.
    """
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Validate agent param if supplied
    forced = agent if agent in AGENT_MAP else None

    try:
        result = await _route_and_respond(message.strip(), thread_id, forced)
        return JSONResponse(result)
    except Exception as exc:
        logger.error("chat/text failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


@app.post("/chat/voice")
async def chat_voice(
    audio: UploadFile = File(...),
    language: str = Form(default="hi-IN"),
    thread_id: Optional[str] = Form(default=None),
    agent: Optional[str] = Form(default=None),
) -> JSONResponse:
    """Handle a voice chat request via STT → agent → TTS pipeline.

    Converts uploaded audio to text, routes through the agent (honouring an
    explicit agent choice if provided), converts the response back to speech,
    and returns the audio as base64.

    Args:
        audio: Uploaded audio file (WAV or OGG format).
        language: Azure Speech locale code of the user's language.
        thread_id: Optional existing thread ID for conversation continuity.
        agent: Optional form field to force a specific agent.

    Returns:
        JSON with transcript, response text, base64 audio, and agent name.
    """
    forced = agent if agent in AGENT_MAP else None

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
        result = await _route_and_respond(transcript, thread_id, forced)
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





# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
