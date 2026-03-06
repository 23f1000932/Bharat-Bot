"""
agents/base_agent.py – Base agent class for BharatBot domain agents.

Provides a unified async chat interface powered by Google Gemini
(gemini-1.5-flash) with per-thread conversation history management.
"""

import logging
import os
import uuid
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini configuration
# ---------------------------------------------------------------------------

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Google Gemini API configured successfully.")
else:
    logger.warning("GEMINI_API_KEY not set; LLM features will be unavailable.")


class BaseAgent:
    """Base class for BharatBot domain AI agents.

    Provides an async ``chat`` method that manages conversation threads
    using Google Gemini (gemini-1.5-flash) with in-memory history storage.

    Attributes:
        system_prompt: The agent's system instructions (English + language routing).
    """

    # Shared conversation history across all agents keyed by thread_id.
    # Each value is a list of {"role": ..., "parts": ...} dicts.
    _conversation_history: dict[str, list[dict]] = {}

    def __init__(self, system_prompt: str) -> None:
        """Initialise the base agent with a system prompt.

        Args:
            system_prompt: The agent-specific system prompt string.
        """
        self.system_prompt: str = system_prompt
        self._model = None

        if GEMINI_API_KEY:
            try:
                self._model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=1024,
                        temperature=0.7,
                    ),
                )
                logger.info("Gemini model initialised for agent.")
            except Exception as exc:
                logger.error("Failed to initialise Gemini model: %s", exc)

    async def chat(
        self,
        user_message: str,
        thread_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """Send a message to Google Gemini and return the response.

        Maintains conversation history per thread_id using an in-memory
        dictionary so that follow-up messages have full context.

        Args:
            user_message: The user's input message.
            thread_id: Optional existing conversation thread ID to continue.
                       A new UUID is generated if not provided.

        Returns:
            A tuple of (response_text, thread_id) where thread_id can be
            passed back in subsequent calls to continue the conversation.
        """
        # Generate a thread_id if not provided
        if not thread_id:
            thread_id = str(uuid.uuid4())
            logger.info("Created new conversation thread: %s", thread_id)

        # Check that Gemini is available
        if self._model is None:
            logger.error("Gemini model is not available. Check GEMINI_API_KEY.")
            return (
                "मुझे खेद है, अभी सेवा उपलब्ध नहीं है। कृपया थोड़ी देर बाद पुनः प्रयास करें। "
                "(Service temporarily unavailable. Please try again later.)",
                thread_id,
            )

        try:
            # Initialise history for new threads
            if thread_id not in self._conversation_history:
                self._conversation_history[thread_id] = []

            history: list[dict] = self._conversation_history[thread_id]

            # Start a chat session with existing history
            chat_session = self._model.start_chat(history=history)

            # Send the user message and get response
            response = chat_session.send_message(user_message)

            # Extract the response text
            answer: str = response.text or ""

            # Update the stored history with the new exchange
            history.append({"role": "user", "parts": [user_message]})
            history.append({"role": "model", "parts": [answer]})

            logger.info(
                "Gemini response obtained (%d chars) for thread %s.",
                len(answer),
                thread_id,
            )
            return answer, thread_id

        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            return (
                "मुझे खेद है, अभी सेवा उपलब्ध नहीं है। कृपया थोड़ी देर बाद पुनः प्रयास करें। "
                "(Service temporarily unavailable. Please try again later.)",
                thread_id,
            )
