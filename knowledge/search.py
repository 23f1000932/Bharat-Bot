"""
knowledge/search.py – Azure AI Search query helper for BharatBot.

Provides functions to query the appropriate Azure AI Search knowledge base
index for each domain (agriculture, health, legal) and to format results
as context strings for injection into agent prompts.
"""

import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SEARCH_ENDPOINT: str = os.getenv("SEARCH_ENDPOINT", "")
SEARCH_KEY: str = os.getenv("SEARCH_KEY", "")
SEARCH_INDEX_AGRI: str = os.getenv("SEARCH_INDEX_AGRI", "agribot-knowledge")
SEARCH_INDEX_HEALTH: str = os.getenv("SEARCH_INDEX_HEALTH", "healthbot-knowledge")
SEARCH_INDEX_LAW: str = os.getenv("SEARCH_INDEX_LAW", "lawbot-knowledge")

# Map agent names to their index names
AGENT_INDEX_MAP: dict[str, str] = {
    "agribot": SEARCH_INDEX_AGRI,
    "healthbot": SEARCH_INDEX_HEALTH,
    "lawbot": SEARCH_INDEX_LAW,
}


def _get_search_client(index_name: str):
    """Build an Azure SearchClient for the given index.

    Args:
        index_name: The name of the Azure AI Search index.

    Returns:
        azure.search.documents.SearchClient instance or None on error.
    """
    try:
        from azure.core.credentials import AzureKeyCredential  # noqa: PLC0415
        from azure.search.documents import SearchClient  # noqa: PLC0415

        if not SEARCH_ENDPOINT or not SEARCH_KEY:
            logger.warning("SEARCH_ENDPOINT or SEARCH_KEY not configured.")
            return None

        client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=index_name,
            credential=AzureKeyCredential(SEARCH_KEY),
        )
        return client
    except ImportError:
        logger.error("azure-search-documents package is not installed.")
        return None
    except Exception as exc:
        logger.error("Failed to create SearchClient for index '%s': %s", index_name, exc)
        return None


async def search_knowledge(
    query: str,
    index_name: str,
    top: int = 3,
) -> list[dict[str, str]]:
    """Search the Azure AI Search knowledge base and return top results.

    Performs a keyword + semantic search on the specified index and returns
    the top matching documents as a list of dictionaries with 'title' and
    'content' keys.

    Args:
        query: The search query string (in any language).
        index_name: The Azure AI Search index name to query.
        top: Maximum number of results to return. Defaults to 3.

    Returns:
        List of dicts, each with 'title' and 'content' keys.
        Returns an empty list on failure or if not configured.
    """
    client = _get_search_client(index_name)
    if client is None:
        logger.warning("Search unavailable; returning empty results.")
        return []

    results: list[dict[str, str]] = []
    try:
        search_results = client.search(
            search_text=query,
            select=["title", "content"],
            top=top,
        )
        for doc in search_results:
            results.append({
                "title": doc.get("title", "Untitled"),
                "content": doc.get("content", ""),
            })
        logger.info(
            "Knowledge search returned %d results from index '%s'.",
            len(results), index_name,
        )
    except Exception as exc:
        logger.error("Knowledge search failed for index '%s': %s", index_name, exc)

    return results


def format_context(results: list[dict[str, str]]) -> str:
    """Format search results into a clean context string for prompt injection.

    Args:
        results: List of dicts with 'title' and 'content' keys.

    Returns:
        Formatted string suitable for injection into an agent system prompt.
    """
    if not results:
        return ""

    lines: list[str] = ["--- Relevant Knowledge Base Context ---"]
    for i, doc in enumerate(results, start=1):
        lines.append(f"\n[{i}] {doc['title']}")
        lines.append(doc["content"].strip())
    lines.append("--- End of Context ---")
    return "\n".join(lines)


async def get_context_for_agent(query: str, agent_name: str) -> str:
    """Retrieve and format knowledge base context for a given agent.

    Convenience function that looks up the correct index for the agent
    type, searches it, and returns formatted context.

    Args:
        query: The user's query string.
        agent_name: One of "agribot", "healthbot", or "lawbot".

    Returns:
        Formatted context string, or empty string if unavailable.
    """
    index_name: str = AGENT_INDEX_MAP.get(agent_name, SEARCH_INDEX_AGRI)
    results = await search_knowledge(query, index_name)
    return format_context(results)
