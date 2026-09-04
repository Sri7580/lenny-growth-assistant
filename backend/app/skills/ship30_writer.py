"""
Ship 30 for 30 essay-writing skill.

Encodes the framework's core structural rules (extracted from the Ship 30 for 30
guide) as an explicit prompt template, rather than relying on ad-hoc phrasing.
Principles applied:
  1. Hook: open with a curiosity gap, counterintuitive claim, or outcome promise.
  2. Skimmability: short paragraphs (1-3 sentences), clear H2/H3 headers, bold anchors.
  3. Narrative progression: each section builds on the last, not a flat list.
  4. Grounded substance: claims must trace back to retrieved transcript chunks.
  5. Concrete takeaway: end with an actionable checklist or framework, not a summary.
"""

SHIP30_SYSTEM_PROMPT = """You are an expert ghostwriter trained in the Ship 30 for 30 essay methodology.
Transform the provided source material into a high-impact, actionable essay of approximately 1,250 words.

Structural requirements:
1. Hook (first 2-3 lines): Open with a counterintuitive product/growth truth, a curiosity gap,
   or an urgent operational tension. Do not summarize the topic — provoke interest.
2. Skimmable formatting:
   - Short paragraphs, 1-3 sentences maximum.
   - Clear Markdown headers (## and ###) dividing sections.
   - Bold anchor phrases at the start of key bullet points.
3. Narrative progression: sections should build on each other, not read as a disconnected list.
4. Grounded substance: every claim must be traceable to the provided transcript context.
   Attribute insights to the specific guest/episode using [Guest, Episode] format.
5. Actionable conclusion: end with a concrete checklist, framework, or immediate next step
   the reader can apply today — not a generic summary.

Do not fabricate facts, statistics, or quotes not present in the provided context. If the context
is insufficient to reach ~1,250 words credibly, write a shorter, denser essay rather than padding
with generic advice."""


def build_ship30_prompt(user_query: str, retrieved_chunks: list[dict]) -> tuple[str, str]:
    """Returns (system_prompt, user_message) for the Ship 30/30 skill."""
    formatted_context = "\n\n".join(
        f"--- {c['guest']} — {c['episode']} ({c.get('timestamp', 'n/a')}) ---\n{c['text']}"
        for c in retrieved_chunks
    )
    user_message = (
        f"Source material:\n{formatted_context}\n\n"
        f"Write a Ship 30 for 30-style essay answering/exploring: {user_query}"
    )
    return SHIP30_SYSTEM_PROMPT, user_message
