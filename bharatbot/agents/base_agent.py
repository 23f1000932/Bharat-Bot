"""
agents/base_agent.py – Base agent class for BharatBot domain agents.

Provides a unified async chat interface that first attempts to use the
Azure AI Foundry Agent Service (AIProjectClient) and falls back to a direct
Azure OpenAI API call if the Foundry SDK is unavailable or fails.
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY: str = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
FOUNDRY_PROJECT_ENDPOINT: str = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")


class BaseAgent:
    """Base class for BharatBot domain AI agents.

    Provides an async `chat` method that manages conversation threads using
    Azure AI Foundry Agent Service.  If the Foundry SDK is unavailable or
    the API call fails, it falls back to a direct Azure OpenAI completion.

    Attributes:
        system_prompt: The agent's system instructions (English + language routing).
    """

    def __init__(self, system_prompt: str) -> None:
        """Initialise the base agent with a system prompt.

        Args:
            system_prompt: The agent-specific system prompt string.
        """
        self.system_prompt = system_prompt

    async def chat(
        self,
        user_message: str,
        agent_id: str,
        thread_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """Send a message to the Azure Foundry agent and return the response.

        Tries Azure AI Foundry Agent Service first.  On any failure, falls
        back to a direct Azure OpenAI chat completion using the same system
        prompt.

        Args:
            user_message: The user's input message.
            agent_id: The Azure Foundry agent ID (e.g. "asst_xxxx").
            thread_id: Optional existing conversation thread ID to continue.

        Returns:
            A tuple of (response_text, thread_id) where thread_id can be
            passed back in subsequent calls to continue the conversation.
        """
        # Try Foundry Agent Service first
        if FOUNDRY_PROJECT_ENDPOINT and agent_id and not agent_id.startswith("asst_xxx"):
            try:
                result, tid = await self._foundry_chat(user_message, agent_id, thread_id)
                return result, tid
            except Exception as exc:
                logger.warning(
                    "Foundry agent call failed (%s); falling back to Azure OpenAI: %s",
                    agent_id, exc,
                )

        # Fallback: direct Azure OpenAI API call
        return await self._openai_fallback(user_message, thread_id or "fallback")

    async def _foundry_chat(
        self,
        user_message: str,
        agent_id: str,
        thread_id: Optional[str],
    ) -> tuple[str, str]:
        """Use Azure AI Foundry AIProjectClient to send a message.

        Args:
            user_message: The user's message.
            agent_id: Azure Foundry agent ID.
            thread_id: Optional existing thread ID.

        Returns:
            Tuple of (response_text, thread_id).

        Raises:
            Exception: Propagates any SDK or API error to the caller.
        """
        import asyncio  # noqa: PLC0415
        from azure.ai.projects import AIProjectClient  # noqa: PLC0415
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415

        client = AIProjectClient(
            endpoint=FOUNDRY_PROJECT_ENDPOINT,
            credential=DefaultAzureCredential(),
        )

        agents_client = client.agents

        # Create or reuse a thread
        if thread_id is None:
            thread = agents_client.create_thread()
            thread_id = thread.id
            logger.info("Created new Foundry thread: %s", thread_id)
        else:
            logger.info("Reusing Foundry thread: %s", thread_id)

        # Add user message to thread
        agents_client.create_message(
            thread_id=thread_id,
            role="user",
            content=user_message,
        )

        # Create and poll the run
        run = agents_client.create_and_process_run(
            thread_id=thread_id,
            agent_id=agent_id,
        )

        if run.status != "completed":
            raise RuntimeError(f"Foundry run ended with status: {run.status}")

        # Retrieve the latest assistant message
        messages = agents_client.list_messages(thread_id=thread_id)
        for msg in messages.data:
            if msg.role == "assistant":
                for content_block in msg.content:
                    if hasattr(content_block, "text"):
                        return content_block.text.value, thread_id

        raise RuntimeError("No assistant message found in Foundry thread response.")

    async def _openai_fallback(
        self,
        user_message: str,
        thread_id: str,
    ) -> tuple[str, str]:
        """Fall back to direct Azure OpenAI API call using the system prompt.

        Args:
            user_message: The user's message.
            thread_id: Passed through unchanged (no real thread management here).

        Returns:
            Tuple of (response_text, thread_id).
        """
        if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT:
            logger.error("Azure OpenAI credentials not configured.")
            return (
                "I'm sorry, I'm currently unable to connect to the AI service. "
                "Please check your configuration.",
                thread_id,
            )

        try:
            client = AsyncAzureOpenAI(
                api_key=AZURE_OPENAI_KEY,
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_version="2024-02-01",
            )

            response = await client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1024,
                temperature=0.7,
            )

            answer: str = response.choices[0].message.content or ""
            logger.info("OpenAI fallback response obtained (%d chars).", len(answer))
            return answer, thread_id

        except Exception as exc:
            logger.error("OpenAI fallback also failed: %s", exc)
            return (
                "मुझे खेद है, अभी सेवा उपलब्ध नहीं है। कृपया थोड़ी देर बाद पुनः प्रयास करें।"
                " (Service temporarily unavailable. Please try again later.)",
                thread_id,
            )
