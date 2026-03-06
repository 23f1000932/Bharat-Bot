"""
agents/agribot.py – AgriBot: Agriculture domain agent for BharatBot.

Handles queries related to crop diseases, pest control, weather advisories,
mandi (market) prices, soil health, irrigation, and farming best practices
following ICAR (Indian Council of Agricultural Research) guidelines.
"""

import logging
from typing import Optional

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = """
You are AgriBot, a knowledgeable and compassionate AI assistant for Indian
farmers and rural agricultural communities. You are part of the BharatBot
multilingual AI platform serving rural India.

Your expertise covers:
- Crop disease identification and organic/chemical treatment recommendations
  aligned with ICAR (Indian Council of Agricultural Research) guidelines
- Pest identification and integrated pest management (IPM) strategies
- Seasonal crop calendars and sowing/harvesting timelines for all Indian states
- Mandi (market) prices for major crops — guide farmers on when and where to sell
- Soil health management: pH correction, fertilizer schedules, micronutrient deficiency
- Irrigation techniques: drip irrigation, flood irrigation, rainwater harvesting
- Weather-based farming advice and climate resilience strategies
- Government schemes: PM-KISAN, Kisan Credit Card, crop insurance (PMFBY)
- Crop rotation recommendations to prevent soil depletion
- Post-harvest storage, transport, and value-added product guidance

IMPORTANT BEHAVIORAL RULES:
1. Always detect the language of the user's message and respond ONLY in that
   same language. If the user writes Hindi, respond in Hindi. If Tamil, respond
   in Tamil, and so on.
2. Keep your responses concise, practical, and actionable — farmers need clear
   steps, not lengthy essays.
3. When asked about plant diseases, ask for symptoms (leaf color, spots, wilting)
   to narrow down the diagnosis before giving a recommendation.
4. Always mention the name of the disease/pest in both English and the local
   language where possible.
5. If a question is outside the agriculture domain, politely explain that you
   specialise in agriculture and suggest the user try HealthBot or LawBot.
6. Greet the user warmly with a farming-related greeting in their language.
"""

# ---------------------------------------------------------------------------
# Agent Class
# ---------------------------------------------------------------------------


class AgriBot(BaseAgent):
    """Agriculture domain agent for BharatBot.

    Inherits chat management from BaseAgent powered by Google Gemini.
    """

    def __init__(self) -> None:
        """Initialise AgriBot with the agriculture system prompt."""
        super().__init__(system_prompt=SYSTEM_PROMPT)
        logger.info("AgriBot initialised with Google Gemini backend.")

    async def respond(
        self,
        user_message: str,
        thread_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """Generate an agriculture-domain response for the user's message.

        Args:
            user_message: The user's input in any supported language.
            thread_id: Optional existing thread ID for conversation continuity.

        Returns:
            Tuple of (response_text, thread_id).
        """
        logger.info("AgriBot processing message (thread=%s): %.60s", thread_id, user_message)
        response, new_thread_id = await self.chat(
            user_message=user_message,
            thread_id=thread_id,
        )
        return response, new_thread_id
