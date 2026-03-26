"""
webhooks/whatsapp.py – Meta WhatsApp Cloud API webhook handler for BharatBot.

Handles webhook verification (GET) and incoming message processing (POST).
Supports text messages and audio messages from WhatsApp users.
"""

import logging
import os
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

WA_TOKEN: str = os.getenv("WA_TOKEN", "")
WA_PHONE_ID: str = os.getenv("WA_PHONE_ID", "")
WA_VERIFY_TOKEN: str = os.getenv("WA_VERIFY_TOKEN", "bharatbot_webhook_2024")

WHATSAPP_API_BASE: str = "https://graph.facebook.com/v19.0"


async def send_whatsapp_text(to: str, message: str) -> bool:
    """Send a text message to a WhatsApp user via the Cloud API.

    Args:
        to: The recipient's WhatsApp phone number in E.164 format.
        message: The text message content to send.

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    if not WA_TOKEN or not WA_PHONE_ID:
        logger.error("WhatsApp credentials (WA_TOKEN, WA_PHONE_ID) are not configured.")
        return False

    url = f"{WHATSAPP_API_BASE}/{WA_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info("WhatsApp message sent to %s.", to)
            return True
    except Exception as exc:
        logger.error("Failed to send WhatsApp message to %s: %s", to, exc)
        return False


async def download_whatsapp_media(media_id: str) -> Optional[bytes]:
    """Download a media file from the WhatsApp Cloud API.

    Args:
        media_id: The media ID returned in the incoming message.

    Returns:
        Raw media bytes if successful, None otherwise.
    """
    if not WA_TOKEN:
        logger.error("WA_TOKEN not configured; cannot download media.")
        return None

    headers = {"Authorization": f"Bearer {WA_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Get media URL from media ID
            meta_url = f"{WHATSAPP_API_BASE}/{media_id}"
            meta_response = await client.get(meta_url, headers=headers)
            meta_response.raise_for_status()
            media_url: str = meta_response.json().get("url", "")

            if not media_url:
                logger.error("No URL in WhatsApp media metadata for ID %s.", media_id)
                return None

            # Step 2: Download the actual media bytes
            media_response = await client.get(media_url, headers=headers)
            media_response.raise_for_status()
            logger.info("Downloaded %d bytes of WhatsApp media (ID=%s).", len(media_response.content), media_id)
            return media_response.content

    except Exception as exc:
        logger.error("Failed to download WhatsApp media (ID=%s): %s", media_id, exc)
        return None


def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str) -> Optional[str]:
    """Verify a Meta webhook verification request.

    Called during the GET /webhook/whatsapp endpoint to validate that the
    webhook URL belongs to BharatBot.

    Args:
        hub_mode: The mode sent by Meta (should be "subscribe").
        hub_verify_token: The token sent by Meta to verify.
        hub_challenge: The challenge string to echo back to Meta.

    Returns:
        The hub_challenge string if verification passes, None otherwise.
    """
    if hub_mode == "subscribe" and hub_verify_token == WA_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verification successful.")
        return hub_challenge
    else:
        logger.warning(
            "WhatsApp webhook verification failed — mode: %s, token: %s",
            hub_mode, hub_verify_token,
        )
        return None


def extract_message_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract message details from a WhatsApp webhook payload.

    Parses the nested Meta webhook payload structure to extract the sender's
    phone number, message type, message text, and media ID (for audio).

    Args:
        payload: The raw webhook payload dictionary from Meta.

    Returns:
        Dict with keys: 'from', 'type', 'text', 'media_id', 'message_id'.
        Returns an empty dict if no valid message is found.
    """
    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {}

        msg = messages[0]
        msg_type: str = msg.get("type", "")
        sender: str = msg.get("from", "")
        msg_id: str = msg.get("id", "")

        result: dict[str, Any] = {
            "from": sender,
            "type": msg_type,
            "text": "",
            "media_id": "",
            "message_id": msg_id,
        }

        if msg_type == "text":
            result["text"] = msg.get("text", {}).get("body", "")
        elif msg_type == "audio":
            result["media_id"] = msg.get("audio", {}).get("id", "")

        return result

    except Exception as exc:
        logger.error("Failed to parse WhatsApp webhook payload: %s", exc)
        return {}
