"""
Agent orchestration: decides whether to run a plain grounded-QA turn or invoke the
Ship 30/30 skill, builds the system prompt with retrieved context, and delegates
token generation to whichever LLM provider is configured.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.rag.retriever import retrieve_relevant_chunks
from app.skills.ship30_writer import build_ship30_prompt
from app.skills.artifact_generator import ARTIFACT_INSTRUCTION
from app.providers.ollama_provider import OllamaProvider
from app.providers.anthropic_provider import AnthropicProvider

GROUNDED_QA_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an internal tool that answers
product management and growth questions strictly using Lenny's Podcast transcript excerpts provided
as context. Rules:
- Only answer using the provided context. Do not use outside knowledge.
- Cite the guest and episode for every claim, e.g. [Guest Name, Episode Title].
- If the provided context does not contain enough information to answer, say exactly:
  "I do not have sufficient information in Lenny's podcast archive to answer this."
- Prefer concrete, tactical advice over generic statements.
""" + "\n\n" + ARTIFACT_INSTRUCTION

SHIP30_TRIGGER_KEYWORDS = ["ship 30", "ship30", "write an essay", "turn this into an essay", "blog post"]


def get_provider(provider_name: str | None = None):
    provider_name = provider_name or settings.default_llm_provider
    if provider_name == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    return OllamaProvider(settings.ollama_base_url, settings.ollama_model)


def _is_ship30_request(user_message: str) -> bool:
    lowered = user_message.lower()
    return any(kw in lowered for kw in SHIP30_TRIGGER_KEYWORDS)


async def run_agent_turn(
    db: AsyncSession,
    user_message: str,
    conversation_history: list[dict],
    provider_name: str | None = None,
):
    """Yields streamed text chunks, and returns (via a final sentinel) the retrieved sources."""
    chunks = await retrieve_relevant_chunks(db, user_message, top_k=6)

    if _is_ship30_request(user_message):
        system_prompt, user_content = build_ship30_prompt(user_message, chunks)
        messages = [{"role": "user", "content": user_content}]
    else:
        context_block = "\n\n".join(
            f"[{c['guest']}, {c['episode']} @ {c.get('timestamp', 'n/a')}]\n{c['text']}"
            for c in chunks
        ) or "(no relevant transcript context found)"
        system_prompt = GROUNDED_QA_SYSTEM_PROMPT
        messages = conversation_history + [
            {"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {user_message}"}
        ]

    provider = get_provider(provider_name)
    full_response = ""
    async for token in provider.generate_response(messages, system_prompt):
        full_response += token
        yield token

    # Note: async generators can't `return` a value alongside yields.
    # Sources/full_response reconstruction happens in chat.py from accumulated tokens.
