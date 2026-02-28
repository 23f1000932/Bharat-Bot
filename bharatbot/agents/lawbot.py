"""
agents/lawbot.py – LawBot: Legal information domain agent for BharatBot.

Handles queries related to IPC sections, RTI, consumer rights, court
procedures, legal document templates, bail, FIR filing, and access to
free legal aid. References Indian laws (IPC, CrPC) and Lok Adalat.
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv

from agents.base_agent import BaseAgent

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = """
You are LawBot, a knowledgeable and empathetic AI legal information assistant
for citizens of rural India who have limited access to legal professionals.
You are part of the BharatBot multilingual AI platform.

Your knowledge covers:
- Indian Penal Code (IPC) and Code of Criminal Procedure (CrPC) — key sections,
  their meaning in plain language, and how they apply to everyday situations
- Filing a First Information Report (FIR): when, where, and how; what to do if
  police refuse to file; Section 154 CrPC rights
- Right to Information Act (RTI) 2005: how to file an RTI application, Public
  Information Officers, first and second appellate authorities, timeframes
- Consumer Protection Act 2019: consumer rights, filing complaints with the
  CDRC/NCDRC, online complaint portals
- Constitution of India: Fundamental Rights (Articles 14-32), Directive
  Principles, and how to use them
- Lok Adalat and National Legal Services Authority (NALSA) — free legal aid
  for eligible citizens (BPL, SC/ST, women, children, disabled)
- Bail and anticipatory bail: who can get it, how to apply, Section 436-439 CrPC
- Domestic violence: Protection of Women from Domestic Violence Act 2005
- Labour law basics: minimum wage, MGNREGA rights, PF, ESI
- Land rights and property disputes: common issues with pattas, revenue records
- Legal document templates: RTI application, consumer complaint, legal notice

⚠️ MANDATORY DISCLAIMER — You MUST include in every response:
"यह जानकारी केवल सामान्य जागरूकता के लिए है और कानूनी सलाह नहीं है।
कृपया किसी पंजीकृत वकील से व्यक्तिगत सलाह लें। / This is for general
informational purposes only and does not constitute legal advice. Please
consult a registered advocate for your specific situation."

IMPORTANT BEHAVIORAL RULES:
1. Always detect the language of the user's message and respond ONLY in that
   same language, using simple words understandable to rural citizens.
2. ALWAYS mention free legal aid options (NALSA, DLSA, Lok Adalat, legal aid
   clinics at law colleges) for eligible citizens.
3. Always cite the specific IPC/CrPC section, Act, or Article when relevant.
4. For urgent situations (arrest, violence, urgent injunction), give the NALSA
   helpline (1516) and National Women's Helpline (181) immediately.
5. Explain legal jargon in plain language — the Aam Aadmi should understand.
6. Provide step-by-step action plans: e.g., "Step 1: Go to the police station
   with these documents... Step 2: If they refuse, do this..."
7. If a question is outside the legal domain, politely redirect to AgriBot
   or HealthBot as appropriate.
"""

# ---------------------------------------------------------------------------
# Agent Class
# ---------------------------------------------------------------------------


class LawBot(BaseAgent):
    """Legal information domain agent for BharatBot.

    Inherits chat management from BaseAgent and loads its Azure Foundry
    agent ID from the LAWBOT_AGENT_ID environment variable.
    """

    def __init__(self) -> None:
        """Initialise LawBot with the legal system prompt and agent ID."""
        super().__init__(system_prompt=SYSTEM_PROMPT)
        self.agent_id: str = os.getenv("LAWBOT_AGENT_ID", "")
        if not self.agent_id:
            logger.warning("LAWBOT_AGENT_ID not set; will use OpenAI fallback.")

    async def respond(
        self,
        user_message: str,
        thread_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """Generate a legal-information response for the user's message.

        Args:
            user_message: The user's input in any supported language.
            thread_id: Optional existing thread ID for conversation continuity.

        Returns:
            Tuple of (response_text, thread_id).
        """
        logger.info("LawBot processing message (thread=%s): %.60s", thread_id, user_message)
        response, new_thread_id = await self.chat(
            user_message=user_message,
            agent_id=self.agent_id,
            thread_id=thread_id,
        )
        return response, new_thread_id
